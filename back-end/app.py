import datetime
import logging as rel_log
import os
import shutil
from datetime import timedelta
from flask import *
from queue import Queue
from threading import Lock
from processor.AIDetector_pytorch import Detector
from models.user import User
from utils.auth import generate_token, token_required, verify_token
import core.main
import cv2
# from processor.yolov8_detector import YOLOv8Detector
from processor.yolov11_detector import YOLOv11Detector

UPLOAD_FOLDER = r'./uploads'

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
app = Flask(__name__)
app.secret_key = 'secret!'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Store SSE clients
sse_clients = []
sse_lock = Lock()

werkzeug_logger = rel_log.getLogger('werkzeug')
werkzeug_logger.setLevel(rel_log.ERROR)

# 解决缓存刷新问题
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)

# 初始化缺陷检测器
# defect_detector = DefectDetector('defect_detection/defect_model/defect_detector/weights/best.pt')
# defect_detector = Detector()
defect_detector = YOLOv11Detector('weights/best.pt')
# 添加header解决跨域
@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With, Authorization'
    return response


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/stream')
def stream():
    token = request.args.get('token')
    print(f"SSE connect attempt - Token: {token}, Remote: {request.remote_addr}")
    if token:
        try:
            user_id = verify_token(token)
            if not user_id:
                print(f"SSE connection rejected: Invalid token, Remote: {request.remote_addr}")
                return jsonify({'status': 0, 'message': 'Invalid token'}), 401
            print(f"SSE client connected: user_id={user_id}, Remote: {request.remote_addr}")
        except Exception as e:
            print(f"Token verification failed: {str(e)}, Remote: {request.remote_addr}")
            return jsonify({'status': 0, 'message': 'Token verification failed'}), 401
    else:
        print(f"SSE connection rejected: Missing token, Remote: {request.remote_addr}")
        return jsonify({'status': 0, 'message': 'Missing token'}), 401

    def generate():
        with sse_lock:
            client_queue = Queue()
            sse_clients.append(client_queue)
        try:
            while True:
                event = client_queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        except GeneratorExit:
            with sse_lock:
                sse_clients.remove(client_queue)
                print(f"SSE client disconnected: Remote: {request.remote_addr}")

    return Response(generate(), mimetype='text/event-stream')


@app.route('/')
def hello_world():
    return redirect(url_for('static', filename='./index.html'))


# 用户注册
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not all([username, password, email]):
        return jsonify({'status': 0, 'message': 'Missing required fields'})
    
    user_model = User()
    if user_model.get_user_by_username(username):
        return jsonify({'status': 0, 'message': 'Username already exists'})
    
    if user_model.register(username, password, email):
        return jsonify({'status': 1, 'message': 'Registration successful'})
    return jsonify({'status': 0, 'message': 'Registration failed'})


# 用户登录
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not all([username, password]):
        return jsonify({'status': 0, 'message': 'Missing username or password'})
    
    user_model = User()
    user = user_model.login(username, password)
    
    if user:
        token = generate_token(user['id'])
        return jsonify({
            'status': 1,
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        })
    return jsonify({'status': 0, 'message': 'Invalid username or password'})


# 需要认证的图片上传接口
# 
@app.route('/upload', methods=['GET', 'POST'])
@token_required
def upload_file(current_user_id):
    file = request.files['file']
    print(datetime.datetime.now(), file.filename)
    if file and allowed_file(file.filename):
        filename = file.filename
        src_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(src_path)

        # 保存到临时检测路径
        tmp_ct_path = os.path.join('./tmp/ct', filename)
        shutil.copy(src_path, tmp_ct_path)

        # 执行缺陷检测
        try:
            img = cv2.imread(tmp_ct_path)
            # 使用process_image方法，它会返回检测结果和标注后的图像
            detections, annotated_image = defect_detector.process_image(img)

            pid, image_info = core.main.c_main(tmp_ct_path, current_app.model, filename.rsplit('.', 1)[1])

            # 保存带注释的图像
            draw_path = os.path.join('./tmp/draw', filename)
            cv2.imwrite(draw_path, annotated_image)
            # cv2.imshow("Debug Annotated", annotated_image)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()

            response = {
                'status': 1,
                'image_url': f'http://127.0.0.1:5003/tmp/ct/{filename}',
                'draw_url': f'http://127.0.0.1:5003/tmp/draw/{filename}',
                'image_info': image_info,
                'defect_detection': {
                    'detections': detections,
                    'total_defects': len(detections),
                    'defect_types': list(set(d['class'] for d in detections))
                }
            }

            # Send to SSE clients
            with sse_lock:
                for client_queue in sse_clients:
                    client_queue.put(response)
            print(f"Sent SSE event for file: {filename}")
            return jsonify(response)

        except Exception as e:
            print(f"Defect detection error: {str(e)}")
            return jsonify({'status': 0, 'message': 'Defect detection failed'})

    return jsonify({'status': 0, 'message': 'Invalid file'})


@app.route("/download", methods=['GET'])
@token_required
def download_file(current_user_id):
    # 需要知道2个参数, 第1个参数是本地目录的path, 第2个参数是文件名(带扩展名)
    return send_from_directory('data', 'testfile.zip', as_attachment=True)


# show photo
# @app.route('/tmp/<path:file>', methods=['GET'])
# def show_photo(file):
#     if request.method == 'GET':
#         filepath = os.path.join('tmp', file)
#         if os.path.exists(filepath):
#             with open(filepath, 'rb') as f:
#                 image_data = f.read()
#             response = make_response(image_data)
#             response.headers['Content-Type'] = 'image/jpeg'  # 可根据文件扩展名判断
#             return response
#         return jsonify({'error': 'File not found'}), 404
@app.route('/tmp/<path:file>', methods=['GET'])
def show_photo(file):
    filepath = os.path.join('tmp', file)
    if os.path.exists(filepath):
        ext = os.path.splitext(file)[1].lower()
        content_type = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.bmp': 'image/bmp'
        }.get(ext, 'application/octet-stream')

        with open(filepath, 'rb') as f:
            image_data = f.read()
        response = make_response(image_data)
        response.headers['Content-Type'] = content_type
        return response

    return jsonify({'error': 'File not found'}), 404



@app.route('/api/user/info', methods=['GET'])
@token_required
def get_user_info(current_user_id):
    try:
        user_model = User()
        user = user_model.get_user_by_id(current_user_id)
        if not user:
            return jsonify({'status': 0, 'message': 'User not found'}), 404

        return jsonify({
            'status': 1,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'created_at': user['created_at'].strftime('%Y-%m-%d %H:%M:%S') if user['created_at'] else None
            }
        })
    except Exception as e:
        return jsonify({'status': 0, 'message': str(e)}), 500


if __name__ == '__main__':
    with app.app_context():
        current_app.model = Detector()
    app.run(host='127.0.0.1', port=5003, debug=True)


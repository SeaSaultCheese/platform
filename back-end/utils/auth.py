import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from config import JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRES)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')

def verify_token(token):
    """Verify a JWT token and return the user_id if valid, else None."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            current_user_id = data['user_id']
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user_id, *args, **kwargs)
    return decorated 


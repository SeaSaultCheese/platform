import cv2
from datetime import datetime
import serial
import time
import requests
import os
from pathlib import Path

# Server configuration
BASE_URL = "http://127.0.0.1:5003"
LOGIN_ENDPOINT = f"{BASE_URL}/api/login"
UPLOAD_ENDPOINT = f"{BASE_URL}/upload"

def capture_webcam_image():
    # Initialize webcam
    # cap = cv2.VideoCapture(1) # Use 0 for default webcam, or 1 for external webcam
    cap = cv2.VideoCapture(0) 
    # Check if webcam opened successfully
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)  # Enable autofocus if supported by the webcam

    width, height = 1920, 1080  # Set desired resolution
    
    # Set the resolution of the webcam
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    # Capture frame
    ret, frame = cap.read()
    
    if not ret:
        print("Error: Could not read frame")
    else:
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"capture_{timestamp}.jpg"
        
        # Save the image
        cv2.imwrite(filename, frame)
        print(f"Image saved as {filename}")
    
    # Release webcam
    cap.release()

    return filename

def login(username: str, password: str) -> str:
    """Login to the server and return the authentication token."""
    headers = {"Content-Type": "application/json"}
    payload = {
        "username": username,
        "password": password
    }
    
    response = requests.post(LOGIN_ENDPOINT, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("status") == 1:
            return data.get("token")
        else:
            raise Exception(f"Login failed: {data.get('message')}")
    else:
        raise Exception(f"Login request failed with status {response.status_code}")

def upload_image(token: str, image_path: str) -> dict:
    """Upload an image to the server using the provided token."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    # Check if file extension is allowed
    allowed_extensions = {'png', 'jpg', 'jpeg'}
    file_ext = Path(image_path).suffix[1:].lower()
    if file_ext not in allowed_extensions:
        raise ValueError(f"Invalid file extension. Allowed extensions: {allowed_extensions}")

    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    with open(image_path, 'rb') as image_file:
        files = {'file': (os.path.basename(image_path), image_file, f'image/{file_ext}')}
        response = requests.post(UPLOAD_ENDPOINT, headers=headers, files=files)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Image upload failed with status {response.status_code}: {response.text}")

if __name__ == "__main__":

    # Configuration - replace with your actual credentials and image path
    USERNAME = "root"  # Replace with actual username
    PASSWORD = "123456"  # Replace with actual password

    ser = serial.Serial('COM7', 9600, timeout=0.1)  # Adjust COM port as needed
    time.sleep(2)

    # Attempt to read a line from the serial port
    while True:
        data = ser.readline().decode('utf-8', errors='ignore').strip()

        # Check if the received data is "TRIGGER"
        if data == "TRIGGER":
            print("Trigger received, capturing image...")

            filename = capture_webcam_image()
   
            try:
                # Step 1: Login to get token
                print("Attempting to login...")
                token = login(USERNAME, PASSWORD)
                print("Login successful!")
                
                # Step 2: Upload image
                print(f"Uploading image: {filename}")
                result = upload_image(token, filename)
                
                # Print results
                if result.get("status") == 1:
                    print("Upload successful!")
                    print(f"Image URL: {result.get('image_url')}")
                    print(f"Annotated Image URL: {result.get('draw_url')}")
                    print(f"Defect Detection Results: {result.get('defect_detection')}")
                else:
                    print(f"Upload failed: {result.get('message')}")
                    
            except Exception as e:
                print(f"Error: {str(e)}")

            finally:
                # Optionally delete local image after upload
                if os.path.exists(filename):
                    os.remove(filename)
                    print(f"Local image {filename} deleted")

                time.sleep(20)
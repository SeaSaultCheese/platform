import requests
import os
from pathlib import Path

# Server configuration
BASE_URL = "http://127.0.0.1:5003"
LOGIN_ENDPOINT = f"{BASE_URL}/api/login"
UPLOAD_ENDPOINT = f"{BASE_URL}/upload"
# TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3NTIzOTgwMDl9.MkXWMx07L1M2-floMrxCe-vs3iDH61PwpAvENKjQNmI"

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

def main():
    # Configuration - replace with your actual credentials and image path
    USERNAME = "123"  # Replace with actual username
    PASSWORD = "123456"  # Replace with actual password
    IMAGE_PATH = r"C:\Users\Caiijo\Desktop\samples-aug\2cm_1_original.jpg" # Replace with actual image path
    
    try:
        # Step 1: Login to get token
        print("Attempting to login...")
        token = login(USERNAME, PASSWORD)
        print("Login successful!")
        
        # Step 2: Upload image
        print(f"Uploading image: {IMAGE_PATH}")
        result = upload_image(token, IMAGE_PATH)
        
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

if __name__ == "__main__":
    main()
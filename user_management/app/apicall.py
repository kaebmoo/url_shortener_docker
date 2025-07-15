# user_management/app/apicall.py
# call fastapi 

from flask import current_app, session
from flask_login import current_user

import jwt
from datetime import datetime, timedelta, timezone
import requests

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

def is_token_expired(token, secret_key):
  try:
    payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM]) # หรือ algorithm ที่คุณใช้
    expiration_timestamp = payload['exp']
    current_timestamp = datetime.now(timezone.utc).timestamp()
    return expiration_timestamp < current_timestamp
  except jwt.ExpiredSignatureError:
    return True  # โทเค็นหมดอายุแล้ว
  except jwt.InvalidTokenError:
    return True  # โทเค็นไม่ถูกต้อง

def create_jwt_token():
    now = datetime.now(timezone.utc)
    payload = {
        "sub": 'user_management',
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm=ALGORITHM)
    return token

def create_refresh_token():
    now = datetime.now(timezone.utc)
    payload = {
        "sub": 'user_management',
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm=ALGORITHM)
    return token

def refresh_jwt_token():
    url = current_app.config['SHORTENER_HOST'] + "/api/refresh_token"
    refresh_token = session.get('refresh_token')
    payload = {"refresh_token": refresh_token}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        new_access_token = response.json().get("access_token")
        session['access_token'] = new_access_token
        return new_access_token
    else:
        # Handle error, such as asking the user to re-login
        return None
    
def send_api_key_to_register(api_key: str, role_id: int):
    # don't call this function directly, please call register_api_key()
    url = current_app.config['SHORTENER_HOST'] + "/api/register_api_key"
    access_token = session.get('access_token')
    if not access_token:
        # Handle the case where access_token is missing, such as re-login
        access_token = create_jwt_token()
    if is_token_expired(access_token, current_app.config['SECRET_KEY']):
        access_token = create_jwt_token()

    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"api_key": api_key, "role_id": role_id}
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 401:  # Token expired
        new_access_token = refresh_jwt_token()
        if new_access_token:
            headers = {"Authorization": f"Bearer {new_access_token}"}
            response = requests.post(url, json=payload, headers=headers)
        else:
            return "Failed to refresh access token", 401

    if response.status_code == 200:
        return "API key registered successfully", 200
    else:
        return "Failed to register API key", response.status_code
    
def send_api_key_to_deactivate(api_key: str):
    url = current_app.config['SHORTENER_HOST'] + "/api/deactivate_api_key"
    access_token = session.get('access_token')
    if not access_token:
        # Handle the case where access_token is missing, such as re-login
        access_token = create_jwt_token()
    if is_token_expired(access_token, current_app.config['SECRET_KEY']):
        access_token = create_jwt_token()

    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"api_key": api_key}
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 401:  # Token expired
        new_access_token = refresh_jwt_token()
        if new_access_token:
            headers = {"Authorization": f"Bearer {new_access_token}"}
            response = requests.post(url, json=payload, headers=headers)
        else:
            return "Failed to refresh access token", 401

    if response.status_code == 200:
        return "API key deleted successfully", 200
    else:
        return "API key cannot be deleted", response.status_code

def register_api_key(uid: str, role_id: int):
    api_key = uid
    message, status = send_api_key_to_register(api_key, role_id)
    return message, status

def deactivate_api_key(uid: str):
    api_key = uid
    message, status = send_api_key_to_deactivate(api_key=api_key)
    return message, status

def get_user_urls():
    # ขอจำนวน urls ที่ผู้ใช้สร้าง โดยส่ง uid หรือ api_key เพื่อยืนยันตัวตน
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'X-API-KEY': current_user.uid
    }

    try:
        shortener_host = current_app.config['SHORTENER_HOST']
        response = requests.get(shortener_host + '/user/urls', headers=headers)
        if response.status_code == 200:
            user_urls = response.json()
            return user_urls
        else:
            return []
    except requests.exceptions.RequestException:
        return []
    
def get_url_scan_status(secret_key: str, api_key: str, target_url: str, scan_type: str = None):
    """
    เรียกใช้ API เพื่อรับสถานะการสแกน URL โดยไม่ใช้ JWT Authentication
    """
    url = current_app.config['SHORTENER_HOST'] + "/user/url/status"

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'X-API-KEY': api_key,
    }

    data = {
        "secret_key": secret_key,
        "target_url": target_url,
        "scan_type": scan_type  # รวม scan_type ใน body ถ้ามี
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            # Return the JSON response and status code if status is 200 OK
            return response.json(), response.status_code
        
        elif response.status_code == 404:
            # Return error message and status code if scan records not found
            return {"error": "Scan records not found."}, response.status_code
        
        else:
            # Return error message and status code for other status codes
            return {"error": f"Unexpected error: {response.status_code}"}, response.status_code
    
    except requests.exceptions.RequestException as e:
        # Return error message and a status code indicating request failure
        return {"error": "Request failed."}, 500

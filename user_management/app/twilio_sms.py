import os
from twilio.rest import Client

def send_otp(phone_number, otp):
    # อ่านค่าจาก Environment Variables
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_number = os.environ.get('TWILIO_FROM_NUMBER')

    # ตรวจสอบว่ามีค่าครบถ้วนหรือไม่
    if not all([account_sid, auth_token, from_number]):
        # อาจจะ log error หรือ raise exception
        print("Twilio credentials are not configured.")
        return None

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=f'Your OTP code is {otp}',
        from_=from_number,
        to=phone_number  # ใช้ phone_number ที่รับเข้ามา 'whatsapp:+66813520625'
    )
    return message.sid
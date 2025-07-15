import http.client
import json
import os
from app import create_app
from urllib.parse import quote_plus  # สำหรับ URL encoding
import ssl

def send_otp(phone_number, otp):
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')

    user = app.config["NT_SMS_USER"]
    passw = app.config["NT_SMS_PASS"]
    otp_code = otp

    # URL encode ข้อความ OTP ก่อนนำไปใส่ใน XML
    encoded_message = quote_plus(f"Your OTP code is {otp_code}")

    # Construct the XML payload
    payload = f"""<?xml version="1.0" encoding="UTF-8"?>
                <Envelope>
                <Header/>
                    <Body>
                        <sendSMS>
                            <user>{user}</user>
                            <pass>{passw}</pass>
                            <from>{app.config["NT_SMS_SENDER"]}</from>
                            <target>{phone_number}</target>
                            <mess>{encoded_message}</mess>
                            <lang>E</lang>
                        </sendSMS>
                    </Body>
                </Envelope>
                """
    headers = {
        'Content-Type': 'application/xml',
        'Accept': 'application/xml'
    }

    context = ssl._create_unverified_context()  # ไม่แนะนำ แต่ทำอะไรไม่ได้ตอนนี้ Disable SSL certificate verification
    conn = http.client.HTTPSConnection(app.config["NT_SMS_HOST"], context=context)
    conn.request("POST", app.config["NT_SMS_API"], payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

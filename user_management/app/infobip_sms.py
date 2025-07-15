import http.client
import json
import os
from app import create_app

def send_otp(phone_number, otp):
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')

    conn = http.client.HTTPSConnection("pp9d33.api.infobip.com")
    otp_code = otp
    # 66813520625
    payload = json.dumps({
        "messages": [
            {
                "destinations": [{"to":f"{phone_number}"}],
                "from": "ServiceSMS",
                "text": f"Your OTP code is {otp_code}" 
            }
        ]
    })
    headers = {
        'Authorization': app.config['INFOBIP'],
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    conn.request("POST", "/sms/2/text/advanced", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

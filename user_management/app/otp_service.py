"""Module providing a function OTP python version."""

import threading
import time
import base64
import hashlib
import pyotp


class OTPService:
    """ One Time Password service """
    def __init__(self):
        self.otp_storage = {}
        # เริ่ม Background Job เพื่อลบ OTP ที่หมดอายุ
        threading.Thread(target=self.cleanup_expired_otp, daemon=True).start()

    def generate_otp(self, phone_number, expiration=60):
        """สร้างคีย์เฉพาะสำหรับหมายเลขโทรศัพท์แต่ละเบอร์"""
        hex_key = self._get_hex_key_for_user(phone_number)
        byte_key = bytes.fromhex(hex_key)
        base32_key = base64.b32encode(byte_key).decode('utf-8')

        # สร้าง TOTP object
        totp = pyotp.TOTP(base32_key, digits=4, interval=expiration)
        otp = totp.now()

        # เก็บ TOTP object และเวลาที่สร้างใน storage
        self.otp_storage[phone_number] = {
            'totp': totp,
            'created_at': time.time(),
            'expiration': expiration
        }
        return otp

    def confirm_otp(self, phone_number, otp):
        """ confirm otp """
        # ดึงข้อมูล OTP ของผู้ใช้จาก storage
        user_otp_data = self.otp_storage.get(phone_number)

        if not user_otp_data:
            return False

        totp = user_otp_data['totp']
        created_at = user_otp_data['created_at']
        expiration = user_otp_data['expiration']

        # ตรวจสอบว่า OTP หมดอายุหรือไม่
        current_time = time.time()
        if current_time - created_at > expiration:
            # ลบ OTP ที่หมดอายุออกจาก storage
            del self.otp_storage[phone_number]
            return False

        # ยืนยัน OTP
        # ยืนยัน OTP โดยใช้ valid_window เพื่อขยายเวลาที่ OTP ถูกต้อง
        return totp.verify(otp, valid_window=1)
    
    def get_time_remaining(self, phone_number):
        """Return the time remaining before the OTP expires."""
        user_otp_data = self.otp_storage.get(phone_number)

        if not user_otp_data:
            return None  # ไม่มี OTP สำหรับหมายเลขนี้

        totp = user_otp_data['totp']
        current_time = time.time()

        # คำนวณเวลาที่เหลือก่อนที่ OTP จะหมดอายุ
        time_remaining = totp.interval - (current_time % totp.interval)

        return time_remaining

    def _get_hex_key_for_user(self, phone_number):
        """ generate key by phone number """
        # ใช้ SHA-256 แปลงหมายเลขโทรศัพท์ให้เป็นคีย์ที่ปลอดภัย
        hash_object = hashlib.sha256(phone_number.encode())
        return hash_object.hexdigest()

    def cleanup_expired_otp(self):
        """ delete dictionary from memory """
        while True:
            current_time = time.time()
            # ตรวจสอบ OTP ที่หมดอายุแล้ว
            for phone_number in list(self.otp_storage.keys()):
                otp_data = self.otp_storage[phone_number]
                if current_time - otp_data['created_at'] > otp_data['expiration']:
                    # ลบ OTP ที่หมดอายุ
                    del self.otp_storage[phone_number]
            # รอ 120 วินาที ก่อนตรวจสอบอีกครั้ง
            time.sleep(120)

'''
# ตัวอย่างการใช้งาน
otp_service = OTPService()

phone_number = '1234567890'
otp = otp_service.generate_otp(phone_number)
print(f"OTP for {phone_number}: {otp}")

# ไม่ยืนยัน OTP เพื่อทดสอบการลบอัตโนมัติ
time.sleep(35)  # รอให้ OTP หมดอายุ

# ตรวจสอบว่าถูกลบออกจาก storage หรือไม่
print(f"Is {phone_number} still in storage?: {phone_number in otp_service.otp_storage}")
'''
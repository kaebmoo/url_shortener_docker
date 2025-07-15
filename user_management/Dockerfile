# ใช้ Python 3.9-slim เป็น base image
FROM python:3.10-slim

# ตั้งค่า Working Directory ภายใน Container
WORKDIR /app

# คัดลอกไฟล์ requirements.txt เข้าไปก่อนเพื่อใช้ประโยชน์จาก Docker cache
COPY requirements.txt .

# ติดตั้ง dependencies
# เพิ่ม gunicorn สำหรับรันใน production
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# คัดลอกโค้ดทั้งหมดในโฟลเดอร์ปัจจุบันเข้าไปใน /app ของ Container
COPY . .

# ตั้งค่า environment variable สำหรับ Flask
ENV FLASK_CONFIG=production

# คำสั่งที่จะรันเมื่อ Container เริ่มทำงาน (รันผ่าน Gunicorn)
# Gunicorn จะมองหา object ชื่อ app ในไฟล์ wsgi.py
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]
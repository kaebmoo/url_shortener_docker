# ใช้ Python 3.9-slim เป็น base image
FROM python:3.10-slim

# ตั้งค่า Working Directory
WORKDIR /app

# คัดลอกและติดตั้ง dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโค้ดทั้งหมด
COPY . .

# คำสั่งสำหรับรัน script ของเรา (สมมติว่าไฟล์หลักคือ check_urls.py)
CMD ["python", "check_urls.py"]
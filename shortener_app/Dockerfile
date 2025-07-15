# ใช้ Python 3.9-slim เป็น base image
FROM python:3.10-slim

# ตั้งค่า Working Directory ภายใน Container
WORKDIR /app

# คัดลอกไฟล์ requirements.txt
COPY requirements.txt .

# ติดตั้ง dependencies และ gunicorn
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# คัดลอกโค้ดทั้งหมด
COPY . .

# คำสั่งที่จะรันเมื่อ Container เริ่มทำงาน
# Gunicorn จะมองหา object ชื่อ app ในไฟล์ main.py
# ใช้ shell form และอ้างถึงตัวแปร $PORT
# ${PORT:-5000} หมายความว่า: ถ้ามีตัวแปร PORT ให้ใช้ค่านั้น, ถ้าไม่มีให้ใช้ค่า default เป็น 5000
# CMD gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind "0.0.0.0:${PORT:-8000}" main:app
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "main:app"]
URL Shortener Docker Setup Guide
=====================================

ระบบย่อ URL ที่ใช้ Docker สำหรับการ deploy ง่ายๆ พร้อมด้วยระบบจัดการผู้ใช้และการสแกน URL

## 1. การดาวน์โหลด Source Code จาก GitHub

```bash
git clone https://github.com/kaebmoo/url_shortener_docker.git
cd url_shortener_docker
```

## 2. โครงสร้างของโปรเจค

โปรเจคประกอบด้วย 4 ส่วนหลัก:
- `shortener_app/` - API สำหรับย่อ URL (FastAPI)
- `user_management/` - ระบบจัดการผู้ใช้ (Flask)
- `web_scan/` - ระบบสแกน URL เพื่อตรวจหา phishing
- `nginx/` - Reverse proxy และ load balancer

## 3. การจัดทำไฟล์ Config

### 3.1 config.env สำหรับ shortener_app
แก้ไขไฟล์ `shortener_app/config.env`:

```env
# การตั้งค่าพื้นฐาน
ENV_NAME=Production
BASE_URL=https://yourdomain.com
HOST=0.0.0.0
PORT=8000

# ฐานข้อมูล PostgreSQL
DB_URL=postgresql+psycopg2://myadminuser:mysecretpassword@db/shortener
DB_API=postgresql+psycopg2://myadminuser:mysecretpassword@db/apikey
DB_BLACKLIST=postgresql+psycopg2://myadminuser:mysecretpassword@db/blacklist

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
SAFE_HOST=https://yourdomain.com/apps
```

### 3.2 config.env สำหรับ user_management
แก้ไขไฟล์ `user_management/config.env`:

```env
# การตั้งค่าแอป
FLASK_CONFIG=production
APP_NAME=URL Shortener
SECRET_KEY=your-secret-key-here

# ข้อมูล Admin เริ่มต้น
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=your-admin-password

# การตั้งค่า Email (SendGrid)
sendgrid_api_key=your-sendgrid-api-key
EMAIL_SENDER=noreply@yourdomain.com
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# ฐานข้อมูล
DATABASE_URL=postgresql+psycopg2://myadminuser:mysecretpassword@db/user
BLACKLIST_DATABASE_URL=postgresql+psycopg2://myadminuser:mysecretpassword@db/blacklist

# การตั้งค่า App
SHORTENER_HOST=http://shortener_app:8000
SHORTENER_HOST_NAME=https://url.nt.th

APP_HOST=https://url.nt.th
APP_PATH=/apps
ASSET_PATH=/apps
```

### 3.3 config.env สำหรับ web_scan
แก้ไขไฟล์ `web_scan/config.env`:

```env
# การตั้งค่าการสแกน
INTERVAL_HOURS=2
SLEEP_SECONDS=2

# ฐานข้อมูล
DATABASE_PATH=postgresql+psycopg2://myadminuser:mysecretpassword@db/shortener
BLACKLIST_DATABASE_PATH=postgresql+psycopg2://myadminuser:mysecretpassword@db/blacklist

# API Keys สำหรับ Security Services
URLHAUS_AUTH_KEY=your-urlhaus-api-key
VIRUSTOTAL_API_KEY=your-virustotal-api-key
HYBRID_ANALYSIS_API_KEY=your-hybrid-analysis-api-key
```

แก้ไขไฟล์ web_scan/check_urls.py

ค้นหาบรรทัดที่มี code นี้ (ประมาณบรรทัดที่ 139)

```credentials_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api-project-744419703652-f520f5308dff.json")```

แล้วเปลี่ยนชื่อเป็นชื่อไฟล์ ```api-project-744419703652-f520f5308dff.json``` เป็นไฟล์ที่ได้จาก Google Cloud Platform 

### 3.4 การตั้งค่า SSL Certificate (nginx)
วางไฟล์ SSL certificate ในโฟลเดอร์ `nginx/certs/`:
- `fullchain.pem` - Certificate chain
- `privkey.pem` - Private key

## 4. การรัน Docker

### 4.1 Build และ Start Services
```bash
# Build และเริ่มต้น services ทั้งหมด
docker-compose up --build -d

# ตรวจสอบสถานะ containers
docker-compose ps
```

### 4.2 การตั้งค่าเริ่มต้น
หลังจาก containers ทั้งหมดรันแล้ว ให้รันคำสั่งต่อไปนี้:

```bash
# สร้าง admin user และ roles
docker-compose exec user_management flask seed

```

### 4.3 การตรวจสอบ Services
```bash
# ตรวจสอบ logs
docker-compose logs -f [service-name]

# ตัวอย่าง
docker-compose logs -f shortener_app
docker-compose logs -f user_management
docker-compose logs -f nginx

# ตรวจสอบ health status
docker-compose ps
```

## 5. การใช้งาน

### 5.1 การเข้าถึง Services
- **Web Interface**: https://yourdomain.com/apps
- **API Documentation**: https://yourdomain.com/docs

### 5.2 การจัดการ Services
```bash
# หยุด services
docker-compose stop

# เริ่มต้น services
docker-compose start

# หยุดและลบ containers
docker-compose down

# หยุดและลบ containers พร้อม volumes
docker-compose down -v
```

## 6. การ Backup และ Restore

### 6.1 Backup Database
```bash
# Backup PostgreSQL
docker-compose exec db pg_dump -U myadminuser shortener > backup_shortener.sql
docker-compose exec db pg_dump -U myadminuser user > backup_user.sql
docker-compose exec db pg_dump -U myadminuser blacklist > backup_blacklist.sql
```

### 6.2 Restore Database
```bash
# Restore PostgreSQL
docker-compose exec -T db psql -U myadminuser shortener < backup_shortener.sql
docker-compose exec -T db psql -U myadminuser user < backup_user.sql
docker-compose exec -T db psql -U myadminuser blacklist < backup_blacklist.sql
```

## 7. การแก้ไขปัญหา

### 7.1 ปัญหาการเชื่อมต่อฐานข้อมูล
```bash
# ตรวจสอบ PostgreSQL
docker-compose exec db psql -U myadminuser -l

# ตรวจสอบ Redis
docker-compose exec redis redis-cli ping
```

### 7.2 ปัญหา Permission
```bash
# ตรวจสอบ file permissions
ls -la nginx/certs/
ls -la db_init/
```

### 7.3 การดู logs แบบ real-time
```bash
# ดู logs ทั้งหมด
docker-compose logs -f

# ดู logs เฉพาะ service
docker-compose logs -f shortener_app
```

## 8. การ Update

### 8.1 Update Code
```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose up --build -d
```

### 8.2 Database Migration
```bash
# Run migrations สำหรับ shortener_app
docker-compose exec shortener_app alembic upgrade head

# Run migrations สำหรับ user_management
docker-compose exec user_management flask db upgrade
```

## 9. Security Notes

- เปลี่ยน SECRET_KEY ให้เป็นค่าใหม่
- ตั้งรหัสผ่าน database ให้แข็งแกร่ง
- ใช้ HTTPS เสมอในการ production
- อัพเดท API keys ให้เป็นของคุณเอง
- ไม่ควร commit config.env ที่มี sensitive data

## 10. Port Mappings

- **nginx**: 80 (HTTP), 443 (HTTPS)
- **PostgreSQL**: 5432
- **Internal Services**: รันใน Docker network

---

สร้างโดย: URL Shortener Docker Project
GitHub: https://github.com/kaebmoo/url_shortener_docker
# Production Server Configuration Guide

## Overview
ตัวอย่างการตั้งค่าสำหรับ production server ของระบบ URL Shortener ที่ประกอบด้วย:
- Nginx reverse proxy
- User Management (Flask)
- Shortener App (FastAPI)
- Web Scanner
- PostgreSQL Database
- Redis Cache

## 1. Docker Compose Configuration

```yaml
# docker-compose.yml
services:
  nginx:
    image: nginx:1.25-alpine
    container_name: nginx_proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/certs:/etc/nginx/certs:ro
    depends_on:
      - user_management
      - shortener_app
    networks:
      - app_network
    restart: always

  user_management:
    build: ./user_management
    container_name: user_management_app
    environment:
      - FLASK_APP=manage.py
    env_file:
      - ./user_management/config.env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      shortener_app:
        condition: service_healthy
    networks:
      - app_network
    restart: unless-stopped

  user_management_worker:
    build: ./user_management
    container_name: user_management_worker
    command: rq worker --with-scheduler -u redis://redis:6379
    environment:
      - FLASK_APP=manage.py
    env_file:
      - ./user_management/config.env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      shortener_app:
        condition: service_healthy
    networks:
      - app_network
    restart: unless-stopped

  shortener_app:
    build: ./shortener_app
    container_name: shortener_api_app
    env_file:
      - ./shortener_app/config.env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  web_scan:
    build: ./web_scan
    container_name: web_scanner_tool
    env_file:
      - ./web_scan/config.env
    volumes:
      - shared_data:/app/data
    depends_on:
      db:
        condition: service_healthy
    networks:
      - app_network
    restart: on-failure

  db:
    image: postgres:13-alpine
    container_name: postgres_db
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: myadminuser
      POSTGRES_PASSWORD: mysecretpassword
    volumes:
      - ./db_init:/docker-entrypoint-initdb.d
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app_network
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U myadminuser -d shortener"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:8-alpine
    container_name: redis_cache
    volumes:
      - redis_data:/data
    networks:
      - app_network
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
  shared_data:

networks:
  app_network:
    driver: bridge
```

## 2. Nginx Configuration

```nginx
# nginx/nginx.conf

# การตั้งค่าพื้นฐานของ Nginx
worker_processes auto;
events { worker_connections 1024; }

# บล็อก http ที่รวมทุกอย่างไว้ด้วยกัน
http {
    # ตั้งค่าพื้นฐาน
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # กำหนดกลุ่ม Server ปลายทาง
    upstream api_server {
        # 'shortener_app' คือชื่อ service ใน docker-compose.yml
        # 8000 คือ port ภายในที่แอป shortener_app ทำงาน
        server shortener_app:8000;
    }
    upstream webapp_server {
        # 'user_management' คือชื่อ service ใน docker-compose.yml
        # 5000 คือ port ภายในที่แอป user_management ทำงาน
        server user_management:5000;
    }

    # Server block สำหรับบังคับ redirect HTTP -> HTTPS
    server {
        listen 80;
        server_name url.nt.th; # แก้ไขเป็นโดเมนของคุณ
        return 301 https://$host$request_uri;
    }

    # Server block หลักสำหรับ HTTPS
    server {
        listen 443 ssl;
        http2 on; # เปิดใช้งาน HTTP/2
        server_name url.nt.th; # แก้ไขเป็นโดเมนของคุณ

        # --- SSL Configuration ---
        # ✏️ path นี้จะตรงกับที่ mount ใน docker-compose.yml
        ssl_certificate /etc/nginx/certs/fullchain.pem;
        ssl_certificate_key /etc/nginx/certs/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers on;

        # --- Proxy Headers (สำคัญมาก) ---
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # --- Location สำหรับ User Management App ---
        location /apps {
            # การใส่ / ต่อท้าย proxy_pass เป็นสิ่งสำคัญ
            # มันจะบอกให้ Nginx ส่ง path ส่วนที่อยู่หลัง /apps/ ไปยัง backend
            # เช่น /apps/login จะถูกส่งไปเป็น /login ให้ Flask
            proxy_pass http://webapp_server/;

            # --- Headers ที่จำเป็นสำหรับการทำ Proxy ---
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;

            # ✏️ Header สำคัญที่ ProxyFix ในโค้ด Flask ของคุณมองหา
            # เพื่อให้ Flask สร้าง URL สำหรับไฟล์ CSS/JS ได้ถูกต้อง
            proxy_set_header X-Forwarded-Prefix /apps;

            # รองรับ WebSocket
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";

            client_max_body_size 100M;
        }

        # --- Location สำหรับ Shortener App ---
        location / {
            proxy_pass http://api_server;

            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # รองรับ WebSocket
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
        }
    }
}
```

## 3. User Management Configuration

```bash
# user_management/config.env

FLASK_CONFIG=production
APP_NAME=URL Shortener
SECRET_KEY=47a3384816f103ba606807e4690c884777630eff15870340df5b6adee87687cfbf72a61a9f2633dd2abbf2242915516b7fda61ae163732b1d

ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your_secure_password

# SendGrid Email Configuration
sendgrid_api_key=your_sendgrid_api_key
MAIL_USERNAME=apikey
MAIL_PASSWORD=your_sendgrid_api_key
EMAIL_SENDER=your_email@example.com
MAIL_DEFAULT_SENDER=your_email@example.com

# Redis Configuration
RQ_DEFAULT_HOST=redis
RQ_DEFAULT_PORT=6379

# Infobip Configuration
INFOBIP=your_infobip_api_key

# Database Configuration (Docker)
DATABASE_URL=postgresql+psycopg2://myadminuser:mysecretpassword@db/user
BLACKLIST_DATABASE_URL=postgresql+psycopg2://myadminuser:mysecretpassword@db/blacklist

# Shortener Service Configuration
SHORTENER_HOST=http://shortener_app:8000
SHORTENER_HOST_NAME=https://url.nt.th

# Application Configuration
APP_HOST=https://url.nt.th
APP_PATH=/apps
ASSET_PATH=/apps

# SMS Configuration
NT_SMS_HOST=smsgw.mybynt.com
NT_SMS_API=/service/SMSWebServiceEngine.php
NT_SMS_USER=your_sms_user
NT_SMS_PASS=your_sms_password
NT_SMS_SENDER=YourSender

# System Configuration
TIMEZONE=Asia/Bangkok

# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_NUMBER=whatsapp:+your_number
```

## 4. Web Scanner Configuration

```bash
# web_scan/config.env

INTERVAL_HOURS=2
SLEEP_SECONDS=2

# Database Configuration (Docker)
DATABASE_PATH=postgresql+psycopg2://myadminuser:mysecretpassword@db/shortener
BLACKLIST_DATABASE_PATH=postgresql+psycopg2://myadminuser:mysecretpassword@db/blacklist

# URLhaus API Configuration
URLHAUS_API=https://urlhaus-api.abuse.ch/v1/url/
URLHAUS_AUTH_KEY=your_urlhaus_api_key

# PhishTank Configuration
PHISHTANK_CSV=verified_online.csv

# OpenPhish Configuration
OPENPHISH_FEED_URL=https://raw.githubusercontent.com/openphish/public_feed/refs/heads/main/feed.txt
OPENPHISH_UPDATE_INTERVAL_HOURS=12
OPENPHISH_REQUEST_TIMEOUT=30

# VirusTotal Configuration
VIRUSTOTAL_ANALYSIS_URL=https://www.virustotal.com/api/v3/analyses/
VIRUSTOTAL_URLS_URL=https://www.virustotal.com/api/v3/urls
VIRUSTOTAL_API_KEY=your_virustotal_api_key

# Hybrid Analysis Configuration
HYBRID_ANALYSIS_API_KEY=your_hybrid_analysis_api_key
HYBRID_ANALYSIS_URL=https://www.hybrid-analysis.com/api/v2/quick-scan/url
```

## 5. Shortener App Configuration

```bash
# shortener_app/config.env

ENV_NAME=Production
BASE_URL=https://url.nt.th
HOST=0.0.0.0
PORT=8000

# Database Configuration (Docker)
DB_URL=postgresql+psycopg2://myadminuser:mysecretpassword@db/shortener
DB_API=postgresql+psycopg2://myadminuser:mysecretpassword@db/apikey
DB_BLACKLIST=postgresql+psycopg2://myadminuser:mysecretpassword@db/blacklist

# Security Configuration
SECRET_KEY=47a3384816f103ba606807e4690c884777630eff15870340df5b6adee87687cfbf72a61a9f2633dd2abbf2242915516b7fda61ae163732b1d
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Feature Configuration
USE_API_DB=False  # ใช้กำหนดว่าจะให้ตรวจ role_id หรือไม่ สำหรับการทำ custom key
SAFE_HOST=https://url.nt.th/apps # ใช้กำหนด host ที่จะให้เปิดแทน กรณีที่ url = "DANGER"
```

## 6. Important Notes

### Security Considerations
1. **แก้ไข SECRET_KEY** ให้เป็นค่าที่ปลอดภัยสำหรับ production
2. **แก้ไขรหัสผ่าน database** ให้เป็นรหัสผ่านที่แข็งแรง
3. **ตั้งค่า SSL certificates** ที่ถูกต้องในโฟลเดอร์ `nginx/certs/`
4. **ปกป้อง API keys** และไม่ควรเก็บใน version control

### Environment Variables ที่ต้องแก้ไข
- `server_name` ใน nginx.conf
- Database passwords
- API keys สำหรับบริการต่างๆ
- Email configuration
- SMS gateway configuration

### SSL Certificates
วางไฟล์ SSL certificates ในโฟลเดอร์ `nginx/certs/`:
- `fullchain.pem`
- `privkey.pem`

### Database Initialization
สร้างไฟล์ SQL initialization ในโฟลเดอร์ `db_init/` เพื่อสร้าง database schemas ที่จำเป็น

### Deployment Steps
1. Clone repository และแก้ไข configuration files
2. วาง SSL certificates ใน `nginx/certs/`
3. สร้าง database initialization scripts
4. รัน `docker-compose up -d`
5. ตรวจสอบ logs ด้วย `docker-compose logs`
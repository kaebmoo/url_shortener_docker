-- 1. สร้างผู้ใช้ seal
CREATE USER seal WITH PASSWORD 'your_password';

-- 2. สร้างฐานข้อมูล shortener
CREATE DATABASE shortener;

-- 3. ให้สิทธิ์ทั้งหมดบนฐานข้อมูล shortener แก่ seal
GRANT ALL PRIVILEGES ON DATABASE shortener TO seal;

-- 4. เชื่อมต่อกับฐานข้อมูล shortener
\c shortener;

-- 5. ให้สิทธิ์ทั้งหมดบน schema และ objects แก่ seal
GRANT ALL PRIVILEGES ON SCHEMA public TO seal;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO seal;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO seal;

-- 6. ให้สิทธิ์ทั้งหมดแก่ seal สำหรับ objects ที่จะสร้างในอนาคต
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO seal;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO seal;

# Flask-Base
 User Management from https://github.com/hack4impact/flask-base 
 Modified the code to be compatible with the new version of the library.
 
 URL Shortened Project

# Flask Application

This is a Flask application with various functionalities including database management, user authentication, URL shortening, and task queue processing.

## Features

- User and Role management
- URL shortening
- Redis queue for background tasks
- Database migrations
- Unit testing
- Fake data generation for development
- Multiple environment configurations (Development, Testing, Production, Heroku, Unix)
- Email support
- Analytics integration (Google Analytics, Segment)
- Error tracking with Raygun

## Configuration

The application uses a flexible configuration system that supports multiple environments. The main configuration class is `Config`, with specific subclasses for different environments:

- `DevelopmentConfig`
- `TestingConfig`
- `ProductionConfig`
- `HerokuConfig`
- `UnixConfig`

### Environment Variables

Key configuration variables can be set in a `config.env` file in the root directory or as environment variables. Important variables include:

- `FLASK_CONFIG`: Determines which configuration to use (default is 'development')
- `SECRET_KEY`: Used for cryptographic operations
- `SHORTENER_HOST`: Host for the URL shortener service
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`: Email configuration
- `ADMIN_PASSWORD`, `ADMIN_EMAIL`: Admin account details
- `REDIS_URL`: URL for Redis connection
- `DATABASE_URL`: Main database URL
- `SHORTENER_DATABASE_URL`: Database URL for the URL shortener service
- `GOOGLE_ANALYTICS_ID`: Google Analytics tracking ID
- `SEGMENT_API_KEY`: Segment API key
- `RAYGUN_APIKEY`: Raygun API key for error tracking

### Database Configuration

The application uses SQLAlchemy and supports multiple database bindings:

- Main database: Configured via `SQLALCHEMY_DATABASE_URI`

Different database URLs are used for development, testing, and production environments.

## Setup

1. Create a `config.env` file in the root directory and set the necessary environment variables.
2. Set the `FLASK_CONFIG` environment variable to choose the configuration (options: development, testing, production, heroku, unix).
3. Install the required dependencies (listed in `requirements.txt`).

## Commands

The application provides several CLI commands:

- `flask test`: Run unit tests
- `flask recreate_db`: Recreate the database (use with caution in production)
- `flask add-fake-data`: Add fake data to the database
- `flask setup_dev`: Set up for local development
- `flask setup_prod`: Set up for production
- `flask run_worker`: Start the RQ worker for background tasks
- `flask format`: Run code formatters (isort and yapf)

## Database Models

The application uses SQLAlchemy for database operations. Models include:

- User
- Role

## Running the Application

To run the application:
The application will use the configuration specified by the `FLASK_CONFIG` environment variable, defaulting to 'development' if not set.

## Development

For development:

1. Set `FLASK_CONFIG=development` in your environment or `config.env` file.
2. Set up the development environment: `flask setup_dev`
3. Add fake data if needed: `flask add-fake-data`
4. Run the application: `python app.py`

Remember to run `flask format` before committing changes to ensure consistent code style.

## Production

For production deployment:

1. Ensure all necessary environment variables are set, especially `SECRET_KEY`.
2. Set `FLASK_CONFIG=production`.
3. Run `flask setup_prod` to set up the production environment.
4. Use a production WSGI server like Gunicorn to run the application.

## Testing

Run the test suite using:
This will discover and run all tests in the `tests` directory.

## Background Tasks

The application uses Redis Queue (RQ) for handling background tasks. To start a worker:
Ensure Redis is running and `REDIS_URL` is correctly set.

## Logging

In Unix environments, the application can log to syslog. This is automatically set up when using the `UnixConfig`.

## Error Tracking

Raygun is integrated for error tracking in production. Ensure `RAYGUN_APIKEY` is set in your production environment.


หากคุณต้องการใช้ Alembic ร่วมกับ Flask-Migrate (ซึ่งเป็น wrapper สำหรับ Alembic), คุณสามารถทำตามขั้นตอนต่อไปนี้:

### 1. ติดตั้ง Alembic และ Flask-Migrate
ถ้าคุณยังไม่ได้ติดตั้ง Alembic และ Flask-Migrate คุณสามารถติดตั้งได้โดยใช้คำสั่ง:

```bash
pip install alembic flask-migrate
```

### 2. ตั้งค่า `manage.py` และ `create_app`
จากโค้ดที่คุณให้มา การตั้งค่า `manage.py` และ `create_app` ของคุณถูกต้องแล้วในการรวม Flask-Migrate และ Alembic

### 3. เริ่มต้น Alembic
เริ่มต้นการใช้งาน Alembic โดยการใช้คำสั่ง:

```bash
flask db init
```

คำสั่งนี้จะสร้างไดเรกทอรี `migrations` ในโฟลเดอร์โปรเจคของคุณ ซึ่งจะใช้ในการเก็บสคริปต์การย้ายฐานข้อมูล (migration scripts)

### 4. สร้าง Migration Scripts
เมื่อคุณทำการเปลี่ยนแปลงโมเดล SQLAlchemy หรือสร้างโมเดลใหม่ คุณสามารถสร้างสคริปต์การย้ายฐานข้อมูลด้วยคำสั่ง:

```bash
flask db migrate -m "Your migration message here"
```

คำสั่งนี้จะสร้างสคริปต์ในไดเรกทอรี `migrations/versions` ที่มีการสร้างหรือเปลี่ยนแปลงตารางในฐานข้อมูล

### 5. อัพเดทฐานข้อมูล
หลังจากที่คุณสร้างสคริปต์ migration แล้ว คุณสามารถอัพเดทฐานข้อมูลของคุณด้วยคำสั่ง:

```bash
flask db upgrade
```

คำสั่งนี้จะใช้สคริปต์ migration ที่สร้างขึ้นและอัพเดทฐานข้อมูลตามการเปลี่ยนแปลงที่คุณได้ทำไว้ในโมเดล SQLAlchemy

### 6. Rollback หรือ Downgrade (ถ้าต้องการ)
หากคุณต้องการกลับไปที่สถานะฐานข้อมูลก่อนหน้าการอัพเกรด คุณสามารถใช้คำสั่ง:

```bash
flask db downgrade
```

ซึ่งจะย้อนกลับการเปลี่ยนแปลงที่เกิดขึ้นจากการอัพเกรดล่าสุด

### 7. กำหนดค่าการใช้งานเพิ่มเติม (ถ้าจำเป็น)
คุณสามารถกำหนดค่าเพิ่มเติมในไฟล์ `alembic.ini` หรือในไฟล์ `migrations/env.py` สำหรับการจัดการการอัพเกรดฐานข้อมูลในสภาพแวดล้อมที่แตกต่างกัน

### ตัวอย่างโครงสร้างของโปรเจค
หลังจากทำตามขั้นตอนข้างต้น โครงสร้างของโปรเจคของคุณอาจจะดูคล้ายกับนี้:

```
url_shortener/
├── migrations/
│   ├── versions/
│   │   ├── <migration_script>.py
│   ├── alembic.ini
│   ├── env.py
│   ├── README
├── app/
│   ├── __init__.py
│   ├── models.py
│   └── ...
├── config.py
├── manage.py
└── ...
```

Alembic และ Flask-Migrate ช่วยให้คุณสามารถจัดการและติดตามการเปลี่ยนแปลงโครงสร้างฐานข้อมูลได้อย่างมีประสิทธิภาพในโครงการ Flask ของคุณ หากมีการเปลี่ยนแปลงหรือปัญหาในอนาคต คุณสามารถใช้เครื่องมือนี้เพื่อจัดการการย้ายฐานข้อมูลได้อย่างง่ายดาย


การสร้าง Admin user
คุณต้องสร้าง "application context" ก่อนที่จะเรียกใช้ฟังก์ชัน `setup_general()` ใน Python shell

### ขั้นตอนในการสร้าง Application Context:

1. **นำเข้า `app` จาก `manage.py`:**
   - คุณต้องนำเข้าแอปพลิเคชัน Flask (`app`) ที่ถูกสร้างขึ้นในไฟล์ `manage.py`.

2. **สร้าง Application Context:**
   - ใช้ `app.app_context()` เพื่อสร้าง "application context" ก่อนที่จะเรียกใช้ฟังก์ชันที่ต้องการ context นั้น

3. **เรียกใช้ฟังก์ชัน `setup_general()` ภายใน context:**

### ตัวอย่างโค้ด:
ใน Python shell ให้ทำตามขั้นตอนดังนี้:

```python
from manage import app, setup_general

# สร้าง application context
with app.app_context():
    setup_general()  # เรียกใช้ฟังก์ชันภายใน context
```

### คำอธิบาย:
- การใช้ `with app.app_context():` ทำให้คุณสามารถสร้าง "application context" ที่จำเป็นสำหรับการทำงานของ Flask และ SQLAlchemy
- หลังจากนั้นคุณสามารถเรียกใช้ `setup_general()` ได้โดยไม่เกิดข้อผิดพลาดเกี่ยวกับ context

### เมื่อคุณรันคำสั่งนี้แล้ว:
ฟังก์ชัน `setup_general()` จะทำงานตามปกติและควรสร้างข้อมูล admin user ตามที่คาดหวัง.
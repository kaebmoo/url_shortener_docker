# shortener_app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import get_settings

# เลือกฐานข้อมูลตามการตั้งค่าจาก config
db_url = get_settings().db_url

# ตรวจสอบว่าใช้ SQLite หรือไม่
if db_url.startswith("sqlite"):
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database for API keys (user management or other purposes)
db_api = get_settings().db_api
if db_api.startswith("sqlite"):
    engine_api = create_engine(db_api, connect_args={"check_same_thread": False})
else:
    engine_api = create_engine(db_api)
SessionAPI = sessionmaker(autocommit=False, autoflush=False, bind=engine_api)
BaseAPI = declarative_base()

# Database for Blacklist URL
db_blacklist = get_settings().db_blacklist
if db_blacklist.startswith("sqlite"):
    engine_blacklist = create_engine(db_blacklist, connect_args={"check_same_thread": False})
else:
    engine_blacklist = create_engine(db_blacklist)
SessionBlacklist = sessionmaker(autocommit=False, autoflush=False, bind=engine_blacklist)
BaseBlacklist = declarative_base()


# ฟังก์ชันสร้างตารางสำหรับ URL shortener
# def init_db():
#    Base.metadata.create_all(bind=engine)

# ฟังก์ชันสร้างตารางสำหรับ API keys
# def init_api_db():
#     BaseAPI.metadata.create_all(bind=engine_api)
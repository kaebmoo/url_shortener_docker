# shortener_app/models.py

from datetime import datetime, timedelta

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String, DateTime, event
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.orm import mapper

from database import Base, BaseAPI, BaseBlacklist

class URL(Base):
    __tablename__ = "urls"  # ชื่อ table ใน sqlite

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)                  # primary key
    key = Column(String, unique=True, index=True)           # shorten 
    secret_key = Column(String, unique=True, index=True)    # a secret key to the user to manage their shortened URL and see statistics.
    target_url = Column(String, index=True)                 # to store the URL strings for which your app provides shortened URLs.
    is_active = Column(Boolean, default=True)               # false is delete
    clicks = Column(Integer, default=0)     # this field will increase the integer each time someone clicks the shortened link.
    api_key = Column(String, index=True)  # เพิ่มฟิลด์นี้เพื่อเก็บ API key
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # เพิ่มฟิลด์วันที่และเวลาในการสร้าง
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())       # เพิ่มฟิลด์วันที่และเวลาในการอัปเดต
    is_checked = Column(Boolean, default=False, nullable=True)
    status = Column(String) # เก็บสถานะว่าเป็น url อันตรายหรือไม่ เช่น safe, danger, no info
    title = Column(String(255)) # title page
    favicon_url = Column(String(255)) # favicon url
    ### expiry_info = relationship("URLExpiry", back_populates="url", uselist=False)

class URL2Check(Base):
    __tablename__ = "urls_to_check" # สำหรับ โปรแกรม ตรวจสอบดึงข้อมูลไปอ่านเพื่อทำการ scan 

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    url = Column(String)

class scan_records(Base):
    __tablename__ = "scan_records"  # เก็บข้อมูลการ scan 
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), onupdate=func.now()) 
    url = Column(String)
    status = Column(String)
    scan_type = Column(String)
    result = Column(String)
    submission_type = Column(String)
    scan_id = Column(String)
    sha256 = Column(String)

class APIKey(BaseAPI):
    __tablename__ = "api_key"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey('roles.id'))
    api_key = Column(String(64), unique=True, index=True)
    
class Role(BaseAPI):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(64), unique=True)

class Blacklist(BaseBlacklist):
    __tablename__ = "url"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)                 # primary key
    url = Column(String(500), unique=True, nullable=False)  # URL ที่ต้องการตรวจสอบ
    category = Column(String(100), nullable=False)          # ประเภทของ URL
    date_added = Column(Date, nullable=False)               # วันที่เพิ่ม URL เข้า blacklist
    reason = Column(String(500), nullable=False)            # เหตุผลที่ URL ถูกบล็อค
    source = Column(String(500), nullable=False)            # แหล่งที่มาของ blacklist
    status = Column(Boolean, default=True)                 # สถานะของ URL (true/false)
    

# ฟังก์ชันนี้จะทำให้แน่ใจว่า updated_at ถูกอัปเดตเมื่อมีการอัปเดตแถว
@event.listens_for(URL, 'before_update')
def receive_before_update(mapper, connection, target):
    target.updated_at = func.now()
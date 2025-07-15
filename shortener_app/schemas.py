# shortener_app/schemas.py

from pydantic import ConfigDict, BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional

class URLBase(BaseModel):
    target_url: str
    custom_key: str = Field(None, description="Custom key for shortening the URL. Only available for VIP users.")
    
    class Config:
        json_schema_extra = {
            "example": {
                "target_url": "https://example.com",
                "custom_key": "my-custom-key"
            }
        }

class GuestURLBase(BaseModel):
    target_url: str
    custom_key: str = None

    class Config:
        json_schema_extra = {
            "example": {
                "target_url": "https://example.com"
            }
        }

class URL(URLBase):
    is_active: bool
    clicks: int
    model_config = ConfigDict(from_attributes=True)

class URLInfo(URL):
    """ สำหรับ return ข้อมูล URL Information """
    target_url: str
    is_active: bool
    clicks: int
    url: str
    admin_url: str  # ไม่จำเป็นต้องเก็บในฐานข้อมูล แต่สามารถกำหนดค่าใน response ได้
    secret_key: str
    qr_code: Optional[str] = Field(None, description="Base64 encoded QR code image for the URL")
    title: Optional[str] = None
    favicon_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None  # ยอมรับ None
    # This enhances URL by requiring two additional strings, url and admin_url. 
    # You could also add the two strings url and admin_url to URL. 
    # But by adding url and admin_url to the URLInfo subclass, 
    # you can use the data in your API without storing it in your database.
    class Config:
        json_schema_extra = {
            "example": {
                "target_url": "https://example.com",
                "is_active": True,
                "clicks": 123,
                "url": "https://short.ly/abc123",
                "admin_url": "https://short.ly/abc123_secret",
                "secret_key": "abc123_secret",
                "qr_code": "data:image/png;base64,...",
                "title": "Example Page",
                "favicon_url": "https://example.com/favicon.ico"
            }
        }
        
        json_encoders = {
            datetime: lambda v: v.isoformat(),  # ใช้ ISO format สำหรับ datetime
        }

class URLUser(BaseModel):
    key: str
    secret_key: str
    target_url: str  # เปลี่ยนจาก HttpUrl เป็น str
    is_active: bool
    clicks: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_checked: bool
    status: Optional[str] = Field(default="")
    title: Optional[str] = None
    favicon_url: Optional[str] = None  # เปลี่ยนจาก HttpUrl เป็น str

    model_config = ConfigDict(
        from_attributes=True
    )

class APIKeyCreate(BaseModel):
    api_key: str
    role_id: int  # เพิ่ม role_id

class APIKeyDelete(BaseModel):
    api_key: str
    

class ScanStatus(BaseModel):
    url: str
    status: Optional[str] = None  # Allow status to be None
    result: str
    scan_type: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

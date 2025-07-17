# shortener_app/crud.py

import logging
from datetime import datetime, timedelta, timezone
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from itsdangerous import BadSignature, SignatureExpired

from sqlalchemy.orm import Session
from sqlalchemy import func

import keygen
import models
import schemas


# สร้าง logger
logger = logging.getLogger("uvicorn.error")

# ตั้งค่าระดับการ log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
logging.basicConfig(level=logging.INFO)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def insert_roles(db: Session):
    """
    Creates initial roles in the apikey database if they don't exist.
    """
    # ID และชื่อต้องตรงกับฝั่ง user_management ทุกประการ
    roles_to_create = {
        1: 'User',
        2: 'Administrator',
        3: 'VIP'
    }
    
    for role_id, role_name in roles_to_create.items():
        db_role = db.query(models.Role).filter(models.Role.id == role_id).first()
        if not db_role:
            new_role = models.Role(id=role_id, name=role_name)
            db.add(new_role)
    
    db.commit()
    print("APIKEY DB: Roles are seeded.")
    
def create_db_url(db: Session, url: schemas.URLBase, api_key: str) -> models.URL:
    ''' create short url  '''
    # key = keygen.create_random_key()
    # secret_key = keygen.create_random_key(length=8)
    
    # key = keygen.create_unique_random_key(db)
    key = url.custom_key if url.custom_key else keygen.create_unique_random_key(db)
    secret_key = f"{key}_{keygen.create_random_key(length=8)}"
    
    db_url = models.URL(
        target_url=url.target_url, 
        key=key, 
        secret_key=secret_key,
        api_key=api_key  # Store API key associated with the URL
    )
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url

'''def update_db_url_page_info(db: Session, db_url: models.URL, title: str, favicon_url: str):
    """Update the title and favicon_url of a URL object in the database."""

    db_url.title = title
    db_url.favicon_url = favicon_url
    db.commit()
    db.refresh(db_url)'''

def get_db_url_by_key(db: Session, url_key: str) -> models.URL:
    # , func.lower(models.URL.status) != 'danger' # เงื่อนไขว่าไม่เอา 'danger'
    return (
        db.query(models.URL)
        .filter(models.URL.key == url_key, models.URL.is_active)
        .first()
    )

def get_db_url_by_customkey(db: Session, url_key: str) -> models.URL:
    return (
        db.query(models.URL)
        .filter(models.URL.key == url_key)
        .first()
    )

def get_db_url_by_secret_key(db: Session, secret_key: str, api_key: str) -> models.URL:
    return (
        db.query(models.URL)
        .filter(models.URL.secret_key == secret_key, models.URL.api_key == api_key, models.URL.is_active)
        .first()
    )

def update_db_clicks(db: Session, db_url: schemas.URL) -> models.URL:
    db_url.clicks += 1
    db.commit()
    db.refresh(db_url)
    return db_url

def deactivate_db_url_by_secret_key(db: Session, secret_key: str, api_key: str) -> models.URL:
    db_url = get_db_url_by_secret_key(db, secret_key, api_key=api_key)
    if db_url:
        db_url.is_active = False
        db.commit()
        db.refresh(db_url)
        return db_url
    else:
        return None

def get_api_key(db: Session, api_key: str) -> models.APIKey:
    return db.query(models.APIKey).filter(models.APIKey.api_key == api_key).first()

def get_role_id(db: Session, api_key: str) -> int:
    api_key_data = db.query(models.APIKey).filter(models.APIKey.api_key == api_key).first()
    if api_key_data:
        return api_key_data.role_id
    return None

def get_role_name(api_db: Session, role_id: int) -> str:
    role = api_db.query(models.Role).filter(models.Role.id == role_id).first()
    if role:
        return role.name
    return None

# def is_url_existing_for_key(db: Session, target_url: str, api_key: str) -> bool:
#     return db.query(models.URL).filter(models.URL.target_url == target_url, models.URL.api_key == api_key, models.URL.is_active).first() is not None

def is_url_existing_for_key(db: Session, target_url: str, api_key: str) -> models.URL | None:
    """Checks if a URL exists for a given target_url and api_key. 
    Returns the URL object if found, or None if not found."""

    return db.query(models.URL).filter(
        models.URL.target_url == target_url, 
        models.URL.api_key == api_key, 
        models.URL.is_active
    ).first()  # This will return the URL object itself or None

# เพิ่มใน shortener_app/crud.py
def is_url_in_blacklist(db: Session, url: str) -> bool:
    """Checks if a URL is in the blacklist."""
    return db.query(models.Blacklist).filter(models.Blacklist.url == url).first() is not None

def create_verification_token(user, expiration=604800):
    """Generate a confirmation token to a new user. - open api"""
    """ กูสร้างมาทำไมวะ จำไม่ได้ ha ha ha หยุดทำไปสามเดือนเอง """

    s = Serializer('SECRET_KEY')
    token = s.dumps({'confirm': user})
    s.loads(token, max_age=expiration)
    return token

def verify_user_token(user, token):
    """Verify that the provided token is for this user's. - open api"""
    """ กูสร้างมาทำไมวะ จำไม่ได้ ha ha ha หยุดทำไปสามเดือนเอง """

    s = Serializer('SECRET_KEY')
    try:
        data = s.loads(token)
    except (BadSignature, SignatureExpired):
        return False
    if data.get('confirm') != user:
        return False
    # confirmed = True
    # db.session.add(self)
    # db.session.commit()
    return True

def register_api_key(db: Session, api_key: str, role_id: int):
    existing_api_key = get_api_key(db, api_key)
    
    if existing_api_key:
        if existing_api_key.role_id != role_id:
            existing_api_key.role_id = role_id
            db.commit()
            db.refresh(existing_api_key)
            return {"message": "API key role updated", "status_code": 200}
        else:
            return {"message": "API key already exists with the same role", "status_code": 200}
    else:
        new_api_key = models.APIKey(api_key=api_key, role_id=role_id)
        db.add(new_api_key)
        db.commit()
        db.refresh(new_api_key)
        return {"message": "API key registered", "status_code": 201}
    
def deactivate_api_key(db: Session, api_key: str):
    existing_api_key = get_api_key(db, api_key)
    if existing_api_key:
        db.delete(existing_api_key)
        db.commit()
        return {"message": "API key deleted", "status_code": 200}
    else:
        return {"message": "API key not found", "status_code": 404}

    
def is_url_info_updated(db: Session, secret_key: str, api_key: str) -> bool:
    """Check if the title or favicon_url of a URL has been updated."""

    db_url = get_db_url_by_secret_key(db, secret_key, api_key=api_key)
    if db_url is None:
        return False  # URL not found

    return db_url.title is not None or db_url.favicon_url is not None

def is_url_owner(db: Session, secret_key: str, api_key: str) -> bool:
    """Check if the user with the given API key is the owner of the URL."""

    db_url = get_db_url_by_secret_key(db, secret_key, api_key=api_key)
    if db_url is None:
        return False  # URL not found
    else:
        return True
    
def verify_secret_and_api_key(db: Session, secret_key: str, api_key: str, api_db: Session) -> bool:
    ''' First, verify the api_key exists in the APIKey table using api_db session '''
    api_key_record = api_db.query(models.APIKey).filter(models.APIKey.api_key == api_key).first()
    
    if not api_key_record:
        return False

    # Then, verify the secret_key exists in the URL table using db session
    db_url = db.query(models.URL).filter(
        models.URL.secret_key == secret_key,
        models.URL.api_key == api_key,
        models.URL.is_active
    ).first()

    # Return True if a matching record is found in both databases, otherwise False
    return bool(db_url)

def is_url_expired(db_url, expiration_delta):
    """Check if a URL has expired based on the created_at field."""
    if db_url.api_key is None:  # Checking for guest URLs (without API key)
        expiration_date = db_url.created_at + expiration_delta
        # Make datetime.now() timezone-aware
        if datetime.now(timezone.utc) > expiration_date:
            return True
        return False
    else:
        # URLs with an API key are not considered expired based on time limits
        return False  # or some other logic based on your requirement

def remove_expired_urls(db: Session, expiry_timedelta: timedelta):
    """ Remove expired URLs based on custom expiry timedelta """
    current_time = datetime.now()  # ใช้ offset-naive datetime เพื่อให้สอดคล้องกับเวลาที่บันทึกในฐานข้อมูล
    expired_time = current_time - expiry_timedelta
    
    expired_urls = db.query(models.URL).filter(
        models.URL.api_key == None,  # URLs created by guest
        models.URL.created_at < expired_time
    ).all()

    for url in expired_urls:
        db.delete(url)
        logger.warning(f"deleting: {url.key}, {url.target_url}")
    db.commit()

def deactivate_expired_urls(db: Session, expiry_timedelta: timedelta):
    """Deactivate URLs that have expired by setting is_active to False."""
    current_time = datetime.now()  # ใช้ offset-naive datetime เพื่อให้สอดคล้องกับเวลาที่บันทึกในฐานข้อมูล
    expired_urls = db.query(models.URL).filter(
        models.URL.api_key == None,  # URLs created by guest
        models.URL.is_active == True,  # Only consider active URLs
        models.URL.created_at < (current_time - expiry_timedelta)
    ).all()

    for db_url in expired_urls:
        db_url.is_active = False
        db.add(db_url)
        logger.warning(f"deactivating: {db_url.key}, {db_url.target_url}")
    db.commit()
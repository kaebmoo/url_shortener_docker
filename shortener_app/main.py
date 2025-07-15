# shortener_app/main.py
import asyncio
import base64
import io
import json
import logging
import os
import secrets
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from functools import partial
from typing import List, Optional
from urllib.parse import urljoin, urlparse, unquote

import aiohttp
import httpx
import jwt
import requests  # Import for checking website existence
import validators
from bs4 import BeautifulSoup
from fastapi import (BackgroundTasks, Body, Depends, FastAPI, Header,
                     HTTPException, Request, Security, WebSocket,
                     WebSocketDisconnect, status)
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.models import APIKey, APIKeyIn, SecurityScheme
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import (APIKeyHeader, HTTPAuthorizationCredentials,
                              HTTPBearer)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image
from qrcodegen import QrCode
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from starlette.datastructures import URL

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_settings
from database import (SessionAPI, SessionBlacklist, SessionLocal, engine,
                      engine_api, engine_blacklist)
from phishing import phishing_data
from utils import (capture_screenshot, has_trailing_asterisks,
                   remove_trailing_asterisks, validate_and_correct_url)


import crud
import keygen
import models
import schemas


@asynccontextmanager
async def lifespan(app: FastAPI):
    ''' Startup: Fetch phishing URLs '''
    # Startup: Fetch phishing URLs
    phishing_data.fetch_phishing_urls()  # เรียกใช้งาน fetch_phishing_urls จากอินสแตนซ์ของ PhishingData

    # Start a background task to periodically deactivate expired URLs
    cleanup_task = asyncio.create_task(deactivate_expired_urls_periodically())
    remove_expired_task = asyncio.create_task(remove_expired_urls_periodically())

    yield
    # Shutdown: Any cleanup code would go here (ถ้ามี)

    # You might want to cancel the cleanup_task, remove_expired_task when the application shuts down
    cleanup_task.cancel()
    remove_expired_task.cancel()
    try:
        await cleanup_task
        await remove_expired_task
    except asyncio.CancelledError:
        print("Cleanup task was cancelled")

app = FastAPI(root_path="", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # อนุญาตทุก origin หรือสามารถระบุเป็น ["http://localhost:8000"]
    allow_credentials=True,
    allow_methods=["*"],  # อนุญาตทุก method เช่น GET, POST, OPTIONS
    allow_headers=["*"],  # อนุญาตทุก header
)

# Initialize Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# templates = Jinja2Templates(directory="shortener_app/templates")
templates = Jinja2Templates(directory="templates")

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# กำหนด Security scheme สำหรับ X-API-KEY Header    
api_key_header = APIKeyHeader(name="X-API-KEY")

# Security scheme สำหรับ BearerAuth
http_bearer = HTTPBearer()

SECRET_KEY = get_settings().secret_key  # for jwt token
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30
SECRET_TOKEN = SECRET_KEY   # for preview url

RESERVED_KEYS = {"apps", "docs", "redoc", "openapi", "about", "api", "url", "user", "admin", "login", "register"}

# ใช้สร้าง database tables
# models.Base.metadata.create_all(bind=engine)
# models.BaseAPI.metadata.create_all(bind=engine_api)
# models.BaseBlacklist.metadata.create_all(bind=engine_blacklist)

logging.basicConfig(level=logging.INFO)

async def deactivate_expired_urls_periodically():
    """Periodically deactivate expired URLs every 24 hours."""
    try:
        while True:
            db = next(get_db())
            # กำหนดระยะเวลาหมดอายุเป็น 30 นาที
            # crud.deactivate_expired_urls(db, timedelta(minutes=30))
            # กำหนดระยะเวลาหมดอายุเป็น 7 วัน
            crud.deactivate_expired_urls(db, timedelta(days=7))
            await asyncio.sleep(86400)  # ทุก 24 ชั่วโมง

    except asyncio.CancelledError:
        print("Periodic cleanup was cancelled")
        raise  # Re-raise to allow proper shutdown handling

async def remove_expired_urls_periodically():
    """Periodically deactivate expired URLs every 24 hours."""
    try:
        while True:
            db = next(get_db())
            # ลบ URL ที่หมดอายุหลังจาก 30 นาที
            # crud.remove_expired_urls(db, timedelta(minutes=30))
            # ลบ URL ที่หมดอายุหลังจาก 30 วัน
            crud.remove_expired_urls(db, timedelta(days=30))
            await asyncio.sleep(86400)  # ทุก 24 ชั่วโมง

    except asyncio.CancelledError:
        print("Periodic cleanup was cancelled")
        raise  # Re-raise to allow proper shutdown handling

def get_secret_key(authorization: str = Header(...)):
    ''' get secret key for Authorization '''
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Authorization header",
        )
    return authorization[len("Bearer "):]

    
@app.get("/check-phishing/", tags=["url"])
async def check_phishing(url: str, background_tasks: BackgroundTasks):
    ''' add background tasks for update phishing urls '''
    # Schedule the feed to be updated if necessary
    """Check if the provided URL is flagged as phishing."""
    if datetime.now() - phishing_data.last_update_time > timedelta(hours=12):
        background_tasks.add_task(phishing_data.update_phishing_urls)
    
    url = normalize_url(unquote(url), trailing_slash=False)
    if url in phishing_data.phishing_urls:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "message":
                    "The URL is flagged as a phishing site based on data from "
                    "OpenPhish and Phishing Army. Access to this URL is restricted.",
                "status_code": 403,
            },
        )
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message":
                "The URL is not flagged as a phishing site based on data from "
                "OpenPhish and Phishing Army. Access is permitted.",
            "status_code": 200},
    )

def get_admin_info(db_url: models.URL) -> schemas.URLInfo:
    ''' get url information '''
    base_url = URL(get_settings().base_url)
    admin_endpoint = app.url_path_for(
        "administration info", secret_key=db_url.secret_key
    )
    db_url.url = str(base_url.replace(path=db_url.key))
    db_url.admin_url = str(base_url.replace(path=admin_endpoint))
    qr_code_base64 = generate_qr_code(db_url.url)
    
    # ต้องดู Model ด้วย
    # สร้าง response โดยใช้ URLInfo
    response = schemas.URLInfo(
        target_url=db_url.target_url,
        is_active=db_url.is_active,
        clicks=db_url.clicks,
        url=db_url.url,
        admin_url=db_url.admin_url,  # ส่งค่า admin_url ที่คำนวณไว้
        secret_key=db_url.secret_key,
        qr_code=f"data:image/png;base64,{qr_code_base64}",
        title=db_url.title,
        favicon_url=db_url.favicon_url,
        created_at=db_url.created_at,
        updated_at=db_url.updated_at 
    )
    # แปลง Pydantic model เป็น dict ก่อนส่งกลับ
    # ใช้ json.dumps() แปลง model เป็น JSON string
    return JSONResponse(content=json.loads(response.model_dump_json()), status_code=200)
    # return db_url
    

def raise_not_found(request):
    ''' raise exception url doesn't exit '''
    message = f"URL '{request.url}' doesn't exist"
    raise HTTPException(status_code=404, detail=message)

def raise_forbidden(message):
    ''' raise exception 403 '''
    if not message:
        message = "You do not have permission to access this resource. Please check your credentials or contact support."
    raise HTTPException(status_code=403, detail=message)

def raise_bad_request(message):
    ''' raise exception bad request '''
    if not message:
        message = "The request could not be processed due to invalid input. Please check your request parameters."
    raise HTTPException(status_code=400, detail=message)

def raise_already_used(message):
    ''' raise exception already use '''
    if not message:
        message = "The requested resource is already in use. Please try a different value."
    raise HTTPException(status_code=400, detail=message)

def raise_not_reachable(message):
    ''' raise exception 504 '''
    if not message:
        message = "The target server is not responding or cannot be reached. Please try again later or check if the URL is correct."
    raise HTTPException(status_code=504, detail=message)

def raise_api_key(api_key: str):
    ''' raise exception 401. Raise an exception when the API key is missing or invalid. '''
    message = (
        f"API key '{api_key}' is missing or invalid. "
        "Ensure you provide a valid API key in the 'X-API-KEY' header. "
        "If you do not have an API key, please register for one."
    )
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)

def normalize_url(url: str, trailing_slash: bool = False) -> str:
    """Normalizes a URL by optionally adding or removing trailing slashes.

    Args:
        url: The URL to normalize.
        trailing_slash: Whether to ensure a trailing slash (True) or remove it (False).

    Returns:
        The normalized URL.
    """
    # Strip leading and trailing whitespace from the URL
    url = url.strip()

    parsed_url = urlparse(url)
    path = parsed_url.path.rstrip("/")  # Remove all trailing slashes from the path
    
    if trailing_slash:
        path += "/"  # Add a single trailing slash if requested

    return parsed_url._replace(path=path).geturl()

# ฐานข้อมูลหลัก main database
def get_db():
    ''' main database '''
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ฟังก์ชันสำหรับการเชื่อมต่อกับฐานข้อมูล API keys
def get_api_db():
    ''' api database '''
    db = SessionAPI()
    try:
        yield db
    finally:
        db.close()

def get_blacklist_db():
    ''' blacklist database '''
    db = SessionBlacklist()
    try:
        yield db
    finally:
        db.close()

def get_optional_api_db():
    ''' optional api database '''
    if get_settings().use_api_db:
        return next(get_api_db())
    return None

def verify_jwt_token(authorization: str = Header(None)):
    ''' verify jwt token. Verify the JWT token and raise appropriate errors.'''
    try:
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header is missing. Please provide a valid JWT token."
            )
        
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload["sub"] != "user_management":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Invalid token subject. Ensure you are using a token "
                    "issued for user management purposes."
                ),
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The provided token has expired. Please request a new token.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The provided token is invalid. Ensure the token is correct.",
        )
    
def create_access_token():
    ''' create access token '''
    now = datetime.now(timezone.utc)
    payload = {
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": now,
        "sub": "user_management"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    

# Updated API key verification function
async def verify_api_key(
    request: Request, db: Session = Depends(get_api_db)
):
    ''' verify api key '''
    api_key = request.headers.get("X-API-KEY")  # Get API key from headers
    if not api_key:
        raise_api_key(api_key) 

    db_api_key = crud.get_api_key(db, api_key)
    if not db_api_key:
        raise_api_key(api_key)
    else:
        return api_key
    
@app.websocket("/ws/url_update/{secret_key}")
async def websocket_endpoint(
    websocket: WebSocket, 
    secret_key: str, 
    db: Session = Depends(get_db)
):
    ''' provide websocket return url information '''
    await websocket.accept()

    try:
        # รับข้อความแรกที่มี api_key
        auth_data = await websocket.receive_json()
        api_key = auth_data.get("api_key")

        # ตรวจสอบว่าผู้ใช้มีสิทธิ์เข้าถึง URL นี้หรือไม่
        if not crud.is_url_owner(db, secret_key, api_key): 
            await websocket.close(code=1008, reason="Unauthorized")  # ปิดการเชื่อมต่อหากไม่ได้รับอนุญาต
            return

        is_updated = False
        timeout = 10  # กำหนด timeout เป็น 10 วินาที (หรือค่าที่เหมาะสม)
        start_time = time.time()

        while not is_updated and time.time() - start_time < timeout:
            is_updated = crud.is_url_info_updated(db, secret_key, api_key)

            if is_updated:
                db_url = crud.get_db_url_by_secret_key(db, secret_key=secret_key, api_key=api_key)
                url_info = get_admin_info(db_url)

                # Decode the JSONResponse body before accessing elements
                url_info_dict = json.loads(url_info.body.decode("utf-8"))

                # ส่งข้อมูลผ่าน WebSocket
                await websocket.send_json(url_info_dict)  # Send the content of the JSONResponse 

            await asyncio.sleep(5)

    except WebSocketDisconnect:
        logging.warning("WebSocket disconnected unexpectedly by the client.")
        await websocket.send_json(
            {"message": "Connection lost. Please reconnect to continue."}
        )
    except Exception as e:
        logging.error("Unexpected error in WebSocket connection: %s", e)
        await websocket.send_json(
            {"message": "An unexpected error occurred. Please try again later."}
        )
    finally:
        # ถ้าออกจาก loop แสดงว่าไม่มีการอัพเดต หรือมีการอัพเดตแล้ว ให้ปิดการเชื่อมต่อ
        try:
            await websocket.close()
        except RuntimeError as e:
            logging.error("Error closing WebSocket: %s", e)

    
async def fetch_page_info(url: str):
    """Fetch title and favicon from the given URL asynchronously."""

    try:
        async with aiohttp.ClientSession() as session:  # ใช้ aiohttp สำหรับ async request
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                content = await response.text()  # รอรับเนื้อหาของหน้าเว็บ

        soup = BeautifulSoup(content, 'html.parser')

        title = soup.find('title')
        title = title.text.strip() if title else 'No title found'

        favicon = soup.find('link', rel='icon')
        if favicon:
            favicon_url = favicon['href']
            if not favicon_url.startswith('http'):
                favicon_url = urljoin(url, favicon_url)
        else:
            favicon_url = None

        return title, favicon_url

    except aiohttp.ClientError as e:
        logging.error(f"HTTP request error: {e}")
        return None, None
    except Exception as e:
        logging.error(f"Unexpected error occurred while fetching page info: {e}")
        return None, None
    
# Create a thread pool executor (you can adjust the max_workers if needed)
executor = ThreadPoolExecutor(max_workers=2)

def fetch_page_info_and_update_sync(db_url: models.URL):
    """ Fetch page info and update the database synchronously."""
    with SessionLocal() as db:
        loop = asyncio.new_event_loop()  # Create a new event loop
        asyncio.set_event_loop(loop)  # Set the new event loop as the current one
        title, favicon_url = loop.run_until_complete(fetch_page_info(db_url.target_url))  # Await the coroutine
        loop.close()  # Close the event loop

        db_url = db.merge(db_url)
        db_url.title = title
        db_url.favicon_url = favicon_url
        db.commit()

async def fetch_page_info_and_update(db_url: models.URL):
    """Wrapper to run the synchronous function in a separate thread."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        executor, partial(fetch_page_info_and_update_sync, db_url)
    )

def generate_qr_code(data):
    ''' generate qr code '''
    qr = QrCode.encode_text(data, QrCode.Ecc.MEDIUM)
    size = qr.get_size()
    scale = 5
    img_size = size * scale
    img = Image.new('1', (img_size, img_size), 'white')

    for y in range(size):
        for x in range(size):
            if qr.get_module(x, y):
                for dy in range(scale):
                    for dx in range(scale):
                        img.putpixel((x * scale + dx, y * scale + dy), 0)

    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

@app.get("/")
def read_root():
    ''' root api '''
    return "Welcome to the URL shortener API :)"

@app.get("/about", response_class=HTMLResponse)
async def read_about(request: Request):
    ''' about page '''
    return templates.TemplateResponse("about.html", {"request": request, "title": "About Page"})

@app.get("/shorten", response_class=HTMLResponse)
async def shorten_example(request: Request):
    ''' shorten example page '''
    return templates.TemplateResponse("shorten.html", {"request": request})


@app.post("/api/register_api_key", tags=["api key"])
def register_api_key(
    api_key: schemas.APIKeyCreate, 
    db: Session = Depends(get_api_db), 
    _: str = Depends(verify_jwt_token)):

    ''' register api key '''
    result = crud.register_api_key(db, api_key.api_key, api_key.role_id)
    return JSONResponse(content={"message": result["message"]}, status_code=result["status_code"])

@app.post("/api/deactivate_api_key", tags=["api key"])
def deactivate_api_key(
    api_key: schemas.APIKeyDelete, 
    db: Session = Depends(get_api_db), 
    _: str = Depends(verify_jwt_token)):

    ''' deactivate api key '''
    result = crud.deactivate_api_key(db=db, api_key=api_key.api_key)
    return JSONResponse(content={"message": result["message"]}, status_code=result["status_code"])


@app.post("/api/refresh_token", tags=["api key"])
def refresh_token(refresh_token: str):
    ''' refresh jwt token '''
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload["sub"] != "user_management":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token subject",
            )
        new_access_token = create_access_token()
        return {"access_token": new_access_token}
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired refresh token",
        )

@app.post("/capture_screen")
async def capture_screen(
    url_key: str, 
    api_key: str = Depends(verify_api_key), 
    db: Session = Depends(get_db)):
    ''' capture screen save to file
        args:
            a) url key
    '''

    # ค้นหา URL จากฐานข้อมูลโดยใช้ url_key
    db_url = crud.get_db_url_by_key(db=db, url_key=url_key)
    
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    # ตรวจสอบสถานะของ URL
    # if db_url.status.lower() != "danger":
    #     raise HTTPException(status_code=400, detail="URL is not marked as dangerous or does not exist")
    
    try:
        # ส่ง target_url ไป capture_screenshot
        screenshot_file_name = await capture_screenshot(db_url.target_url)
        screenshot_path = f"/static/screenshots/{screenshot_file_name}"
        
        # Optionally update the database (commented out)
        # db_url.screenshot_path = screenshot_path
        # db_url.updated_at = func.now()
        # db.commit()
        
    except aiohttp.ClientError as e:
        logging.error(f"Network error occurred: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch the webpage for screenshot.")
    except OSError as e:
        logging.error(f"File system error occurred: {e}")
        raise HTTPException(status_code=500, detail="Failed to save the screenshot.")
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Unable to capture screenshot.")
    
    return {"base_url": get_settings().base_url, "screenshot_path": screenshot_path, "url": db_url.target_url}

@app.get("/preview_url")
async def preview_url(
    request: Request, 
    url: str, 
    token: str = Header(...), 
    heading_text_h1: str = None, 
    heading_text_h3: str = None):
    ''' call capture screen return preview.thml
        args:
            a) url
            b) heading text h1, h3 [option]
    '''

    if token != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    url = validate_and_correct_url(url)
    screenshot_file_name = await capture_screenshot(url)
    screenshot_path = f"/static/screenshots/{screenshot_file_name}"

    # กำหนดข้อความ default ถ้าไม่ได้ระบุ heading_text
    heading_text_h1 = heading_text_h1 or "URL Safety Warning"
    heading_text_h3 = heading_text_h3 or "Warning: This URL may be dangerous!"

    return templates.TemplateResponse("preview.html", {
        "request": request, 
        "url": url, 
        "screenshot_path": screenshot_path, 
        "heading_text_h1": heading_text_h1,
        "heading_text_h3": heading_text_h3,
        "app_path": get_settings().safe_host
    })

async def call_preview_url_async(url: str, token: str, heading_text_h1: str = None, heading_text_h3: str = None):
    ''' asynchonous call preview url 
        args:
            a) url
            b) heading text h1, h3 [option]
    '''
    base_url = get_settings().base_url
    preview_url_route = base_url + "/preview_url"
    retries = 3
    async with httpx.AsyncClient(timeout=60.0) as client:
        for _ in range(retries):
            try:
                params = {"url": url}
                if heading_text_h1:
                    params["heading_text_h1"] = heading_text_h1
                if heading_text_h3:
                    params["heading_text_h3"] = heading_text_h3

                response = await client.get(
                    preview_url_route,
                    params=params,
                    headers={"token": token}
                )
                if response.status_code == 200:
                    return response.text
                else:
                    raise Exception(f"Failed to call preview_url: {response.status_code}")
            except httpx.ReadTimeout:
                if _ == retries - 1:
                    raise Exception("Max retries exceeded with url")  



@app.get("/{url_key}")
async def forward_to_target_url(
        url_key: str,
        request: Request,
        db: Session = Depends(get_db)
    ):
    ''' forward short url to target url
        preview target url
        args:
            a) url key
    '''

    # has asterisk at the end of url_key  
    has_wildcard = False
    if has_trailing_asterisks(url_key):
        has_wildcard = True
        url_key = remove_trailing_asterisks(url_key)

    if db_url := crud.get_db_url_by_key(db=db, url_key=url_key):
        # ตรวจสอบว่าลิงก์หมดอายุแล้วหรือยัง
        if crud.is_url_expired(db_url, timedelta(days=7)):
            raise HTTPException(status_code=410, detail=(
            "The URL has expired and is no longer available. "
            "Shortened URLs are only valid for 7 days unless extended."
        ),)
        
        if db_url.status is not None and db_url.status.lower() == "danger":
            # เรียกใช้ call_preview_url_async และส่ง HTML กลับไปยังไคลเอนต์
            # html_content = await call_preview_url_async(db_url.target_url, SECRET_TOKEN)
            html_content = await call_preview_url_async(
                db_url.target_url, SECRET_TOKEN,
                heading_text_h1="Warning: Dangerous URL",
                heading_text_h3="This URL has been flagged as potentially harmful."
            )
            return HTMLResponse(content=html_content)
        
        if has_wildcard:
            # เรียกใช้ call_preview_url_async และส่ง HTML กลับไปยังไคลเอนต์
            html_content = await call_preview_url_async(db_url.target_url, SECRET_TOKEN, heading_text_h1="Link Inspector", heading_text_h3="Inspect a short link to make sure it's safe to click on.")
            return HTMLResponse(content=html_content)
            
        crud.update_db_clicks(db=db, db_url=db_url) # นับจำนวนการเข้า url
        return RedirectResponse(db_url.target_url)  # ไปยัง url ปลายทาง
            
    else:
        raise_not_found(request)

    # The := operator is colloquially known as the walrus operator and gives you a new syntax for assigning variables in the middle of expressions.
    # If db_url is a database entry, then you return your RedirectResponse to target_url. Otherwise, you call raise_not_found()


@app.post("/url", response_model=schemas.URLInfo, tags=["url"]) # , dependencies=[Security(verify_api_key)]
async def create_url(
    url: schemas.URLBase,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
    api_db: Optional[Session] = Depends(get_optional_api_db),
    blacklist_db: Session = Depends(get_blacklist_db)
):
    ''' create short url
        args:
            a) target url
            b) custom key (Custom key for shortening the URL. Only available for VIP users.)
    '''
    url.target_url = normalize_url(unquote(url.target_url), trailing_slash=False)

    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")

    # ตรวจสอบว่า URL อยู่ใน blacklist หรือไม่
    if crud.is_url_in_blacklist(blacklist_db, url.target_url):
        raise_forbidden(message=(
            "The provided URL is in the blacklist and cannot be shortened. "
            "This is to prevent abuse or potential harm to users."
        ))

    # ตรวจสอบว่า URL เป็น phishing หรือไม่โดยใช้ check_phishing
    phishing_check_response = await check_phishing(url.target_url, background_tasks)
    if phishing_check_response.status_code == 403:
        raise_forbidden(message=phishing_check_response.content["message"])
    
    # ดึง role_id จาก database ถ้ามีการกำหนดให้ใช้งาน
    role_id = None
    if api_db:
        role_id = crud.get_role_id(api_db, api_key)
        if role_id is None:
            raise HTTPException(status_code=400, detail="Invalid API key")
        
        # ดึง role_name จากฐานข้อมูล Role
        role_name = crud.get_role_name(api_db, role_id)
        if role_name is None:
            raise HTTPException(status_code=400, detail="Role not found")
        
    
    # role_id = crud.get_role_id(api_db, api_key)
    # ได้ role_id มาก็ขึ้นอยู่กับว่าจะเอาไปใช้ทำอะไรต่อ
    
    if url.custom_key:
        if role_id is not None and role_id not in [2, 3]:
            raise_forbidden(message="Custom keys are only available for VIP users. Please upgrade your account to use this feature.")

        if not keygen.is_valid_custom_key(url.custom_key):
            raise_bad_request(message="Your provided custom key is not valid. It should only contain letters and digits.")
        
        if len(url.custom_key) > 15:
            raise_bad_request(message="Your provided custom key is too long. It should not exceed 15 characters.")
        
        if crud.get_db_url_by_customkey(db, url.custom_key):
            raise_already_used(message=(
            f"The custom key '{url.custom_key}' is already in use. "
            "Please choose a different key or leave it empty to use an auto-generated key."
        ))

        if url.custom_key.lower() in RESERVED_KEYS:
            raise_bad_request(message=f"The custom key '{url.custom_key}' is reserved and cannot be used.")
    
    # ตรวจสอบว่ามี  URL Target นี้อยู่แล้วหรือไม่สำหรับ API key นี้
    # ต้องทำเพิ่มกรณีที่มีการ custom key shorten url ให้มีการซ้ำได้ แต่ custom key ต้องไม่ซ้ำ
    
    existing_url = crud.is_url_existing_for_key(db, url.target_url, api_key)
    if existing_url:
        base_url = get_settings().base_url
        # qr_code_base64 = generate_qr_code(f"{base_url}/{existing_url.key}")
        url_data = {
            "target_url": existing_url.target_url,
            "is_active": existing_url.is_active,
            "clicks": existing_url.clicks,
            "url": f"{base_url}/{existing_url.key}", 
            "admin_url": f"{base_url}/{existing_url.secret_key}",
            # "qr_code": f"data:image/png;base64,{qr_code_base64}",
            "secret_key": existing_url.secret_key,
            "title": existing_url.title,
            "favicon_url": existing_url.favicon_url,
            "message": f"A short link for this website already exists."
        }
        return JSONResponse(content=url_data, status_code=409) 

    db_url = crud.create_db_url(db=db, url=url, api_key=api_key)

    # เพิ่ม task การดึงข้อมูล title และ favicon ลงใน background
    background_tasks.add_task(fetch_page_info_and_update, db_url)

    return get_admin_info(db_url)

@app.post("/url/guest", response_model=schemas.URLInfo, tags=["url"])
@limiter.limit("30/minute")  # 30 requests per minute per IP
async def create_url_guest(
    request: Request,  # Include the request argument for slowapi to apply rate limiting based on the request's IP address or other properties. 
    url: schemas.GuestURLBase,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    blacklist_db: Session = Depends(get_blacklist_db)
):
    ''' create short url for guest (without API key)
        args:
            a) target url
    '''
    # บังคับให้ custom_key เป็น None เสมอสำหรับผู้ใช้ guest
    url.custom_key = None

    # Normalize and validate the target URL
    # url.target_url = normalize_url(url.target_url, trailing_slash=False)
    url.target_url = normalize_url(unquote(url.target_url), trailing_slash=False)

    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")

    # Check if the URL is blacklisted
    if crud.is_url_in_blacklist(blacklist_db, url.target_url):
        raise_forbidden(message="The provided URL is blacklisted and cannot be shortened.")

    # Check if the URL is a phishing site
    phishing_check_response = await check_phishing(url.target_url, background_tasks)
    if phishing_check_response.status_code == 403:
        raise_forbidden(message=phishing_check_response.content["message"])

    # Create a new URL entry in the database for a guest user (without an API key)
    db_url = crud.create_db_url(db=db, url=url, api_key=None)

    # Add a background task to fetch title and favicon
    background_tasks.add_task(fetch_page_info_and_update, db_url)

    # Return the URL info including the admin URL for managing the short URL
    return get_admin_info(db_url)


@app.get("/user/url_count", tags=["info"])
async def get_url_count(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    '''
    Query the count of URLs created with the given API key
    args:
        a) api key
    '''
    # Query the count of URLs created with the given API key
    url_count = db.query(models.URL).filter(models.URL.api_key == api_key, models.URL.is_active == True).count()

    # Return the count as a JSON response
    return JSONResponse(content={"url_count": url_count}, status_code=200)

@app.get("/user/urls", tags=["info"])
async def get_user_url(
    api_key: str = Depends(verify_api_key), 
    db: Session = Depends(get_db)
):
    ''' Query the database to get the URLs
        args:
            a) api key
    '''
    # Query the database to get the URLs
    user_urls = db.query(models.URL).filter(models.URL.api_key == api_key, models.URL.is_active == True).all()
    
    # Convert the results to JSON serializable form
    user_urls_json = jsonable_encoder(user_urls)

    # Use Pydantic models to filter and return the desired fields
    ## filtered_urls = [schemas.URLUser(**url).model_dump() for url in user_urls_json]

    # Use Pydantic models to filter and return the desired fields
    filtered_urls = []
    for url in user_urls_json:
        if url.get('status') is None:
            url['status'] = ''  # or another default value
        filtered_urls.append(schemas.URLUser(**url).model_dump())

 
    # ใช้ jsonable_encoder เพื่อแปลง datetime ให้เป็น string
    json_compatible_data = jsonable_encoder(filtered_urls)
    
    return JSONResponse(content=json_compatible_data, status_code=200)
    # return JSONResponse(content=user_urls_json, status_code=200) # return all value

@app.post("/user/url/status", response_model=List[schemas.ScanStatus], tags=["info"])
def get_url_scan_status(
    secret_key: str = Body(...),  # รับค่า secret_key จาก body
    target_url: str = Body(...),  # รับค่า target_url จาก body
    scan_type: str = Body(None),  # รับค่า scan_type จาก body ถ้ามี
    api_key: str = Depends(verify_api_key), 
    db: Session = Depends(get_db),
    api_db: Session = Depends(get_api_db),
):
    ''' get malware information, scan results
    args:
        a) secret key
        b) target url
        c) scan type: name of scan vendor ex. google [option]
        d) api key
    '''
    is_valid = crud.verify_secret_and_api_key(db, secret_key=secret_key, api_key=api_key, api_db=api_db)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Secret key or API key not found or invalid."
        )

    # Decode URL before normalization
    decoded_target_url = unquote(target_url)

    # Normalize URL (strip trailing slashes, etc.)
    normalized_url = normalize_url(decoded_target_url, trailing_slash=False)
    # target_url = normalize_url(target_url, trailing_slash=False)

    query = db.query(models.scan_records).filter(models.scan_records.url == normalized_url)
    # query = db.query(models.scan_records).filter(models.scan_records.url.ilike(f"%{target_url}%"))

    
    if scan_type:
        query = query.filter(models.scan_records.scan_type == scan_type)

    scan_records = query.order_by(models.scan_records.timestamp.desc()).all()

    if not scan_records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No scan records found for the specified URL and scan type."
        )

    return [
        schemas.ScanStatus(
            url=record.url,
            status=record.status if record.status is not None else "None",
            result=record.result,
            scan_type=record.scan_type,
            timestamp=record.timestamp
        )
        for record in scan_records
    ]

@app.get(
    "/admin/{secret_key}",
    name="administration info",
    response_model=schemas.URLInfo,
    tags=["admin"],
)  # Removed Security dependency
def get_url_info(
    secret_key: str,
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)  # Added api_key dependency
):
    '''get url information 
        args:
            a) secret key of url
            b) api key
    '''
    if db_url := crud.get_db_url_by_secret_key(db, secret_key=secret_key, api_key=api_key):
        return get_admin_info(db_url)
    else:
        raise_not_found(request)


@app.delete("/admin/{secret_key}", tags=["admin"])  # Removed Depends dependency
def delete_url(
    secret_key: str,
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)  # Added api_key dependency
):
    """delete url in database"""
    if db_url := crud.deactivate_db_url_by_secret_key(db, secret_key=secret_key, api_key=api_key):
        message = f"Successfully deleted shortened URL for '{unquote(db_url.target_url)}'"
        return {"detail": message}
    else:
        raise_not_found(request)

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="URL Shortener API",
        version="1.0.0",
        description="API for shortening URLs and managing shortened URLs",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-KEY",
        },

    }
    # ให้ทุก endpoint ใช้ ApiKeyAuth เป็นค่าเริ่มต้น
    openapi_schema["security"] = [
        {"ApiKeyAuth": []},
    ]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=get_settings().host, port=get_settings().port)
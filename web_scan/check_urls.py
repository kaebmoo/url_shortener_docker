#tools/web_scan/check_urls.py
import os
from dotenv import load_dotenv

import asyncio
import sqlite3
from aiohttp import ClientSession
import time  # Import time for sleep functionality

# Google Web Risk
import json
from google.api_core.exceptions import PermissionDenied
from google.cloud import webrisk_v1
from google.cloud.webrisk_v1 import ThreatType

from sqlalchemy import create_engine, Boolean, Column, Integer, String, Date, DateTime, func, Enum, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base


# VirusTotal
import vt

# เน้นไปที่ phishing: phishtank
import pandas as pd

# เน้นไปที่ malware: urlhaus
import sys
import aiohttp  # Import aiohttp for asynchronous requests

# โหลดค่าจาก .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'config.env'))

# อ่านค่าจาก config.env
INTERVAL_HOURS = int(os.getenv("INTERVAL_HOURS", 2))  # ค่า default 1 ถ้าไม่มีในไฟล์
SLEEP_SECONDS = int(os.getenv("SLEEP_SECONDS", 2))
DATABASE_PATH = os.getenv("DATABASE_PATH")
URLHAUS_API = os.getenv("URLHAUS_API")
URLHAUS_AUTH_KEY = os.getenv("URLHAUS_AUTH_KEY")
PHISHTANK_CSV = os.getenv("PHISHTANK_CSV")
VIRUSTOTAL_ANALYSIS_URL = os.getenv("VIRUSTOTAL_ANALYSIS_URL")
VIRUSTOTAL_URLS_URL = os.getenv("VIRUSTOTAL_URLS_URL")
OPENPHISH_FEED_URL = os.getenv("OPENPHISH_FEED_URL", "https://raw.githubusercontent.com/openphish/public_feed/refs/heads/main/feed.txt")
OPENPHISH_UPDATE_INTERVAL_HOURS = int(os.getenv("OPENPHISH_UPDATE_INTERVAL_HOURS", 12))
OPENPHISH_REQUEST_TIMEOUT = int(os.getenv("OPENPHISH_REQUEST_TIMEOUT", 30))
BLACKLIST_DATABASE_PATH = os.getenv("BLACKLIST_DATABASE_PATH")

# ตรวจสอบว่าอ่านค่าได้ถูกต้อง
print(f"Database Path: {DATABASE_PATH}")
if not DATABASE_PATH:
    raise ValueError("DATABASE_PATH is not set in the environment variables.")
# เพิ่มหลังจากการตรวจสอบ DATABASE_PATH
if not BLACKLIST_DATABASE_PATH:
    raise ValueError("BLACKLIST_DATABASE_PATH is not set in the environment variables.")

# Database setup
# Base = declarative_base() 
# engine = create_engine(DATABASE_PATH, echo=False) 
# Base.metadata.create_all(engine)
# Session = sessionmaker(bind=engine)

# Setup สำหรับ Database หลัก (shortener)
BaseShortener = declarative_base()
engine_shortener = create_engine(DATABASE_PATH, echo=False)
SessionShortener = sessionmaker(bind=engine_shortener)

# Setup สำหรับ Database ที่สอง (blacklist)
BaseBlacklist = declarative_base()
engine_blacklist = create_engine(BLACKLIST_DATABASE_PATH, echo=False)
SessionBlacklist = sessionmaker(bind=engine_blacklist)

# กำหนด class scan_records ภายในโปรแกรม
class scan_records(BaseShortener):
    __tablename__ = "scan_records"  # เก็บข้อมูลการ scan 
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())  
    url = Column(String)
    status = Column(
        Enum(
            '0', 
            'Dangerous', 
            'Safe', 
            'In queue for scanning', 
            '-1', 
            '1', 
            'No conclusive information', 
            'No classification', 
            name='status_enum',  # กำหนดชื่อให้กับ ENUM type
            create_type=False  # กำหนดเป็น False เพื่อไม่สร้างใหม่ซ้ำ
        ),
        default='0'
    )
    scan_type = Column(String)
    result = Column(String)
    submission_type = Column(String)
    scan_id = Column(String)
    sha256 = Column(String)

class URL(BaseShortener):
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

# กำหนด class URLsToCheck สำหรับ urls_to_check table
class URLsToCheck(BaseShortener):
    __tablename__ = 'urls_to_check'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)    
    url = Column(String)
class BlacklistURL(BaseBlacklist):
    __tablename__ = "url"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, unique=True, index=True)  # unique เพื่อไม่ให้ซ้ำ
    category = Column(String, default="phishing")
    # date_added = Column(DateTime(timezone=True), server_default=func.now())
    date_added = Column(Date, default=func.current_date())
    reason = Column(String)
    status = Column(Boolean, default=True)  # true = active, false = inactive
    source = Column(String, default="openphish")

# สั่งสร้างตารางในแต่ละ Database
# BaseShortener.metadata.create_all(engine_shortener)
# BaseBlacklist.metadata.create_all(engine_blacklist)

# Path to the credentials file
# ไฟล์ JSON Credential จาก Google Cloud
credentials_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api-project-744419703652-f520f5308dff.json")

# Set the environment variable for authentication
if os.path.exists(credentials_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
else:
    print("Google Credential file not found.")

# Create the client
webrisk_client = webrisk_v1.WebRiskServiceClient()

# กำหนด API Key ของ VirusTotal
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")


# Database Trigger Function
def create_database_trigger(db_type):
    if db_type == "sqlite":
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS check_new_url AFTER INSERT ON urls
                BEGIN
                    INSERT INTO urls_to_check (url) VALUES (NEW.target_url);
                END;
            """)
            conn.commit()
            print("create_database_trigger(), Database trigger created successfully for SQLite.")
        except sqlite3.Error as e:
            print(f"create_database_trigger(), Error creating database trigger: {e}")
        finally:
            if conn:
                conn.close()

    elif db_type == "postgresql":
        try:
            with engine_shortener.connect() as conn:
                # ลบ Trigger เดิมถ้ามีอยู่แล้ว
                conn.execute(text("DROP TRIGGER IF EXISTS check_new_url ON urls;"))
                conn.execute(text("DROP FUNCTION IF EXISTS insert_url_to_check();"))

                # สร้างฟังก์ชันใหม่
                conn.execute(text("""
                    CREATE OR REPLACE FUNCTION insert_url_to_check()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        INSERT INTO urls_to_check (url) VALUES (NEW.target_url);
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """))

                # สร้าง Trigger ใหม่
                conn.execute(text("""
                    CREATE TRIGGER check_new_url
                    AFTER INSERT ON urls
                    FOR EACH ROW
                    EXECUTE FUNCTION insert_url_to_check();
                """))
            print("Trigger and function created successfully in PostgreSQL.")
        except Exception as e:
            print(f"create_database_trigger(), Error creating database trigger for PostgreSQL: {e}")



# Asynchronous Function for Periodic Full Checks
async def periodic_full_check(interval_hours=1):
    while True:
        urls_to_check = get_new_urls_from_database()  # Change function to get new URLs
        if urls_to_check:
            await main(urls_to_check)
        await asyncio.sleep(interval_hours * 3600)  # Sleep for the specified interval


# ฟังก์ชันจาก google_web_risk.py
async def check_google_web_risk(url):
    # print("Google Web Risk: ", end="")
    try:
        # The URL to be checked
        uri = url
        threat_types = ["MALWARE", "SOCIAL_ENGINEERING"]

        # Search the URI
        response = webrisk_client.search_uris(uri=uri, threat_types=threat_types)

        # Check the response
        if response.threat:
            #print(f"The URL {url} is not safe.")
            for threat in response.threat.threat_types:
                #print(f"Threat type: {threat} {ThreatType(threat).name}")
                pass
            return True
        else:
            # print(f"The URL {url} is safe.")
            return False

    except PermissionDenied as exc:
        print("check_google_web_risk(), Permission denied: ", exc)
        print("check_google_web_risk(), Please ensure the service account has the correct permissions and the Web Risk API is enabled.")
    
    return None

async def check_virustotal(url, session):  # Pass the aiohttp session
    """Asynchronously checks the reputation of a URL using the VirusTotal API.

    Args:
        url: The URL to check.
        session: An aiohttp ClientSession for making asynchronous requests.

    Returns:
        True if the URL is considered malicious, False if safe, or None if the analysis is inconclusive.
    """
    try:
        # Use the session for the VirusTotal request
        payload = { "url": url }
        headers = {
            "accept": "application/json",
            "x-apikey": VIRUSTOTAL_API_KEY,
            "content-type": "application/x-www-form-urlencoded"
}
        async with session.post(VIRUSTOTAL_URLS_URL, data = payload, headers = headers) as response:
            result = await response.json()  # Get the JSON response
            scan_id = result["data"]["id"]  # Extract the scan ID

        # Poll for results (replace 10 with the desired number of retries)
        for _ in range(10):
            async with session.get(f"{VIRUSTOTAL_ANALYSIS_URL}{scan_id}", headers={"x-apikey": VIRUSTOTAL_API_KEY}) as response:
                analysis = await response.json()
                if analysis["data"]["attributes"]["status"] == "completed":
                    break   # Stop polling if analysis is complete
            await asyncio.sleep(5)  # Wait for 5 seconds before retrying

        # Check analysis results
        if analysis["data"]["attributes"]["status"] == "completed":
            stats = analysis["data"]["attributes"]["stats"]
            if stats["malicious"] > 0:
                return True  # Malicious
            else:
                return False  # Not malicious
        else:
            return None  # Inconclusive

    except vt.error.APIError as e:
        print(f"VirusTotal Error: {e}")
        return None
    except Exception as e:  # Catch more general exceptions
        print(f"VirusTotal Unexpected error: {e}")
        return None


# ฟังก์ชันจาก check_url_with_phishtank.py
# file จาก phishtank
csv_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), str(PHISHTANK_CSV))
# อ่านไฟล์ CSV
data_phishtank = pd.read_csv(csv_file)

async def check_phishtank(url):
    # print("PhishTank: ", end="")
    try:
        # ตรวจสอบว่ามี URL ในไฟล์ CSV หรือไม่
        if url in data_phishtank['url'].values:
            # ค้นหาข้อมูลของ URL ที่ตรงกัน
            phish_info = data_phishtank[data_phishtank['url'] == url].iloc[0]
            '''
            print(f"The URL {url} is a phishing site.")
            print(f"Phish ID: {phish_info['phish_id']}")
            print(f"Phish detail URL: {phish_info['phish_detail_url']}")
            print(f"Submission time: {phish_info['submission_time']}")
            print(f"Verification time: {phish_info['verification_time']}")
            print(f"Target: {phish_info['target']}")
            '''
            return True
        else:
            # print(f"The URL {url} is not in the PhishTank CSV database.")
            return False
    except FileNotFoundError:
        print(f"PhishTank Error: The file {csv_file} was not found.")
        
    except pd.errors.EmptyDataError:
        print(f"PhishTank Error: The file {csv_file} is empty.")
        
    except Exception as e:
        print(f"PhishTank An unexpected error occurred: {e}")
        

    return None

async def update_openphish_blacklist(session: aiohttp.ClientSession):
    """
    Fetches the OpenPhish feed and updates the local blacklist database.
    """
    print("Starting OpenPhish blacklist update...")
    try:
        # เพิ่ม timeout
        timeout = aiohttp.ClientTimeout(total=OPENPHISH_REQUEST_TIMEOUT)
        async with session.get(OPENPHISH_FEED_URL, timeout=timeout) as response:
            if response.status == 200:
                text_data = await response.text()
                
                # ปรับปรุงการ filter URLs
                urls_from_feed = {
                    url.strip() for url in text_data.strip().split('\n') 
                    if url.strip() and url.strip().startswith(('http://', 'https://'))
                }
                
                if not urls_from_feed:
                    print("OpenPhish feed is empty. No updates to process.")
                    return
                    
                print(f"Fetched {len(urls_from_feed)} valid URLs from OpenPhish feed.")
                
                with SessionBlacklist() as db_session:
                    try:
                        # ค้นหา URL ที่มีอยู่แล้วในฐานข้อมูล
                        existing_urls_query = db_session.query(BlacklistURL.url).filter(
                            BlacklistURL.url.in_(urls_from_feed)
                        )
                        existing_urls = {url[0] for url in existing_urls_query}
                        new_urls = urls_from_feed - existing_urls
                        
                        if new_urls:
                            new_records = [
                                BlacklistURL(
                                    url=url, 
                                    source='openphish', 
                                    category='phishing', 
                                    status=True,
                                    reason='OpenPhish public feed'
                                ) 
                                for url in new_urls
                            ]
                            db_session.bulk_save_objects(new_records)
                            db_session.commit()
                            print(f"Added {len(new_urls)} new URLs to the blacklist.")
                        else:
                            print("No new URLs to add. Blacklist is up-to-date.")
                            
                    except Exception as db_error:
                        db_session.rollback()
                        print(f"Database error during blacklist update: {db_error}")
                        
            else:
                print(f"Error fetching OpenPhish feed. Status: {response.status}")
                
    except aiohttp.ClientError as e:
        print(f"Network error during OpenPhish update: {e}")
    except asyncio.TimeoutError:
        print(f"Timeout error: Request took longer than {OPENPHISH_REQUEST_TIMEOUT} seconds")
    except Exception as e:
        print(f"Unexpected error during OpenPhish update: {e}")

async def periodic_openphish_update(interval_hours=None):
    """
    Runs the OpenPhish update function periodically.
    """
    if interval_hours is None:
        interval_hours = OPENPHISH_UPDATE_INTERVAL_HOURS
        
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                await update_openphish_blacklist(session)
        except Exception as e:
            print(f"Error in periodic OpenPhish update: {e}")
            
        print(f"OpenPhish update finished. Waiting for {interval_hours} hours...")
        await asyncio.sleep(interval_hours * 3600)

# เพิ่มฟังก์ชันตรวจสอบ blacklist (ยังคงใช้วิธีเดิม)
async def check_blacklist(url):
    """Check if URL exists in local blacklist"""
    try:
        with SessionBlacklist() as session:
            existing_record = session.query(BlacklistURL).filter_by(
                url=url, 
                status=True
            ).first()
            
            return existing_record is not None
                
    except Exception as e:
        print(f"Error checking blacklist: {e}")
        return None

# ฟังก์ชันจาก urlhaus_lookup_url.py
async def check_urlhaus(url, session):
    # print("URLHaus: ", end="")
    try:
        # ตรวจสอบว่ามี Auth-Key หรือไม่
        if not URLHAUS_AUTH_KEY:
            print("URLhaus Auth-Key not configured. Please add URLHAUS_AUTH_KEY to config.env")
            return None
        
        # Construct the HTTP request
        data_urlhaus = {'url': url}
        headers = {
            "Auth-Key": URLHAUS_AUTH_KEY
        }
        
        # Use aiohttp.ClientSession for asynchronous POST request
        async with session.post(URLHAUS_API, data=data_urlhaus, headers=headers) as response:
            # Check if the response status is OK
            if response.status != 200:
                print(f"URLhaus API returned status {response.status}")
                return None
            
            # Check if the response content type is JSON
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type:
                print(f"URLhaus API returned non-JSON content type: {content_type}")
                return None
            
            # Parse the response from the API
            json_response = await response.json()
            
            # Check if json_response is None or empty
            if json_response is None:
                print("URLhaus API returned None response")
                return None
            
            # Check if the required key exists
            if 'query_status' not in json_response:
                print("URLhaus API response missing 'query_status' key")
                return None
            
            if json_response['query_status'] == 'ok':
                # print(json.dumps(json_response, indent=4, sort_keys=False))
                return True
            elif json_response['query_status'] == 'no_results':
                # print("No results")
                return False
            else:
                print(f"URLhaus unexpected query_status: {json_response.get('query_status', 'unknown')}")
                return None
                
    except aiohttp.ClientError as e:
        print(f"URLhaus Client Error: {e}")
        return None
    except aiohttp.ClientResponseError as e:
        print(f"URLhaus Response Error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"URLhaus JSON Decode Error: {e}")
        return None
    except KeyError as e:
        print(f"URLhaus Key Error: {e}")
        return None
    except Exception as e:
        print(f"URLhaus Unexpected Error: {e}")
        return None    

# ฟังก์ชันในการอัพเดตฐานข้อมูล
def update_database(url, status):
    """Update the status of a URL in the database."""
    with SessionShortener() as session:
        try:
            session.query(URL).filter(URL.target_url == url).update({URL.status: status})
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"update_database(), Unexpected error: {e}")


# ฟังก์ชันในการอ่านข้อมูลจากฐานข้อมูล อ่านเฉพาะที่ยังไม่เคย scan
def get_new_urls_from_database():
    # session = Session()
    with SessionShortener() as session:  # ใช้ context manager เพื่อสร้าง session
        try:
            urls = session.query(URL.target_url).filter(
                (URL.is_checked == None) | (URL.is_checked == False)
            ).all()
            return [url[0] for url in urls]
        except Exception as e:
            print(f"get_new_urls_from_database(), Unexpected error: {e}")
            return []  # Return an empty list if there is an error

# ฟังก์ชันในการอ่านข้อมูลจาก urls_to_check table ซึ่งข้อมูลจะเพิ่มเข้ามาเมื่อมีการทำ shorten url ใหม่ 
def get_urls_from_database():

    with SessionShortener() as session:
        urls = []
        try:
            # อ่าน URL จาก urls_to_check โดยการใช้ SQLAlchemy query
            urls = session.query(URLsToCheck.url).distinct().all()
            urls = [url[0] for url in urls]

            # ลบ URL ที่อ่านแล้วออกจากคิว
            session.query(URLsToCheck).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"get_urls_from_database(), Database error: {e}")
        return urls

def mark_urls_as_checked(urls):
    with SessionShortener() as session:
        try:
            session.query(URL).filter(URL.target_url.in_(urls)).update({URL.is_checked: True}, synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"mark_urls_as_checked(), Database error: {e}")
        finally:
            session.close()

# ฟังก์ชันหลักในการตรวจสอบ URL
async def check_url(url, session):
    '''
    tasks = [
        check_google_web_risk(url),
        check_virustotal(url, session),
        check_phishtank(url),
        check_urlhaus(url, session)
    ]
    results = await asyncio.gather(*tasks)
    '''
    tasks = {
        "Blacklist": check_blacklist(url),
        "Google Web Risk": check_google_web_risk(url),
        "VirusTotal": check_virustotal(url, session),
        "Phishtank": check_phishtank(url),
        "URLhaus": check_urlhaus(url, session)
    }  # Use a dictionary to map functions to their names
    results = await asyncio.gather(*tasks.values())  # Gather results
    is_dangerous = False  # Flag to track if the URL is marked dangerous

    with SessionShortener() as db_session:  # Proper session handling
        # db_session = Session()  # Create a database session

        for function_name, result in zip(tasks.keys(), results):
            # Determine the result string
            if result is True:
                result_str = "DANGER"
                is_dangerous = True
                print(f"The URL {url} is dangerous according to {function_name}.")
            elif result is False:
                result_str = "SAFE"
                print(f"The URL {url} is safe according to {function_name}.")
            else:
                result_str = "INCONCLUSIVE"
                print(f"No conclusive information for the URL {url} in {function_name}.")

            # ตรวจสอบว่ามี record ของ URL นี้และ scan_type นี้อยู่แล้วหรือไม่
            with db_session.no_autoflush:  # Disable autoflush temporarily
                existing_record = db_session.query(scan_records).filter_by(url=url, scan_type=function_name).first()

            # ถ้ามี record อยู่แล้ว ให้อัพเดตเฉพาะ timestamp และ result
            if existing_record:
                existing_record.timestamp = func.now()
                existing_record.result = result_str 
            else:  # ถ้ายังไม่มี record ให้สร้างใหม่
                # Create a new scan record
                new_record = scan_records(
                    url=url,
                    scan_type=function_name,
                    result=result_str  # You can add more details here if needed
                )
                db_session.add(new_record)

        db_session.commit()  # Commit the changes to the database
        # db_session.close()

    # Update the main 'urls' table only once
    if is_dangerous:
        update_database(url, "DANGER")
    else:  # Update to SAFE only if all results are False or None
        if all(result is False or result is None for result in results):
            update_database(url, "SAFE")

# ฟังก์ชันหลักในการรับ URL และตรวจสอบ
async def main(urls, batch_size=10):
    if isinstance(urls, str):  # Check if urls is a string
        urls = [urls]  # Convert the single string to a list
    async with aiohttp.ClientSession() as session:  # Create session here
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]  # Get a batch of URLs
            tasks = [check_url(url, session) for url in batch]
            await asyncio.gather(*tasks)

            # Delay after each batch
            await asyncio.sleep(SLEEP_SECONDS)  # Adjust delay time as needed
        mark_urls_as_checked(urls)

# ฟังก์ชันหลักในการเรียกใช้ main
def run_main(urls):
    asyncio.run(main(urls)) # Changed to asyncio.run()

# ตัวอย่างการเรียกใช้งาน
if __name__ == "__main__":
    # อ่าน URL จากฐานข้อมูล ทั้งหมด
    # urls_to_check = get_urls_from_database()

    # อ่านเฉพาะ record ที่ยังไม่ได้ scan
    # urls_to_check = get_new_urls_from_database()
    # run_main(urls_to_check)

    # เริ่มการตรวจสอบ URL ใหม่และตรวจสอบเป็นระยะ
    # สร้าง Trigger ใน Database สำหรับตรวจสอบ URL ใหม่
    if DATABASE_PATH.startswith("sqlite"):
        create_database_trigger("sqlite")
    elif DATABASE_PATH.startswith("postgresql"):
        create_database_trigger("postgresql")

    async def main_task():
        try:
            print("Performing initial blacklist update...")
            try:
                async with aiohttp.ClientSession() as session:
                    await update_openphish_blacklist(session)
            except Exception as e:
                print(f"Failed to perform initial blacklist update: {e}")
                print("Continuing with URL checking tasks...")

            # เริ่มการตรวจสอบ URL ใหม่และตรวจสอบเป็นระยะ
            async def check_urls_task():
                while True:
                    try:
                        urls_to_check = get_urls_from_database()
                        if urls_to_check:
                            await main(urls_to_check)
                    except Exception as e:
                        print(f"Error in check_urls_task: {e}")
                    await asyncio.sleep(SLEEP_SECONDS)  # รอ 2 วินาทีก่อนตรวจสอบรอบถัดไป (ปรับได้ตามต้องการ)

            loop = asyncio.get_event_loop()

            loop.create_task(periodic_full_check(interval_hours=INTERVAL_HOURS))  # สร้าง task ตรวจสอบทุก 2 ชั่วโมง
            loop.create_task(check_urls_task())  # เริ่ม Task ตรวจสอบ URL ใหม่
            loop.create_task(periodic_openphish_update(interval_hours=12))

            await asyncio.Event().wait()  # รอ event loop ทำงาน
        except Exception as e:
            print(f"main_task(), Unexpected error: {e}")

    try:
        asyncio.run(main_task())  # เริ่ม event loop และรัน main_task
    except KeyboardInterrupt:
        print("Task terminated by user.")



    

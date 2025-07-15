## คู่มือการใช้งานระบบตรวจสอบ URL โดยใช้ Google Web Risk, VirusTotal, PhishTank และ URLhaus

### บทนำ
โค้ดนี้มีจุดประสงค์ในการตรวจสอบ URL ที่เก็บอยู่ในฐานข้อมูลว่ามีความเสี่ยงหรือเป็นภัยคุกคามหรือไม่ โดยใช้บริการจาก Google Web Risk, VirusTotal, PhishTank และ URLhaus ซึ่งจะทำงานในรูปแบบ asynchronous เพื่อเพิ่มประสิทธิภาพในการตรวจสอบ

### การตั้งค่าเบื้องต้น

#### 1. การตั้งค่าไฟล์ `.env`
- สร้างไฟล์ `config.env` ในโฟลเดอร์เดียวกันกับโค้ดและกำหนดค่าต่อไปนี้:
  ```env
  INTERVAL_HOURS=2
  SLEEP_SECONDS=2
  DATABASE_PATH=/path/to/your/database.db
  URLHAUS_API=https://urlhaus-api.abuse.ch/v1/url/
  PHISHTANK_CSV=/path/to/your/verified_online.csv
  VIRUSTOTAL_ANALYSIS_URL=https://www.virustotal.com/api/v3/analyses/
  VIRUSTOTAL_URLS_URL=https://www.virustotal.com/api/v3/urls
  VIRUSTOTAL_API_KEY=your_virustotal_api_key
  ```

- โหลดค่าจากไฟล์ `.env`:
  ```python
  import os
  from dotenv import load_dotenv

  load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'config.env'))

  INTERVAL_HOURS = int(os.getenv("INTERVAL_HOURS", 2))
  SLEEP_SECONDS = int(os.getenv("SLEEP_SECONDS", 2))
  DATABASE_PATH = os.getenv("DATABASE_PATH")
  URLHAUS_API = os.getenv("URLHAUS_API")
  PHISHTANK_CSV = os.getenv("PHISHTANK_CSV")
  VIRUSTOTAL_ANALYSIS_URL = os.getenv("VIRUSTOTAL_ANALYSIS_URL")
  VIRUSTOTAL_URLS_URL = os.getenv("VIRUSTOTAL_URLS_URL")
  API_KEY = os.getenv("VIRUSTOTAL_API_KEY")

  print(f"Database Path: {DATABASE_PATH}")
  ```

#### 2. การตั้งค่า Google Web Risk
- คุณต้องมีไฟล์ JSON Credential จาก Google Cloud ซึ่งสามารถสร้างได้จาก Google Cloud Console
- กำหนด path ของไฟล์ credential:
  ```python
  credentials_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api-project-xxxxxx.json")
  ```

- ตั้งค่า environment variable สำหรับการ authentication:
  ```python
  if os.path.exists(credentials_path):
      os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
  else:
      print("Google Credential file not found.")
  ```

- สร้าง client สำหรับ Google Web Risk:
  ```python
  from google.cloud import webrisk_v1

  webrisk_client = webrisk_v1.WebRiskServiceClient()
  ```

#### 3. การตั้งค่า VirusTotal
- คุณต้องมี API Key ของ VirusTotal ซึ่งสามารถสร้างได้จาก VirusTotal
- อ่านค่า API Key จากไฟล์ `.env`:
  ```python
  import vt

  API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
  vt_client = vt.Client(API_KEY)
  ```

#### 4. การตั้งค่า PhishTank
- ไฟล์ CSV จาก PhishTank ต้องถูกดาวน์โหลดและเก็บไว้ใน path ที่กำหนด:
  ```python
  import pandas as pd

  csv_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), str(PHISHTANK_CSV))
  data_phishtank = pd.read_csv(csv_file)
  ```

#### 5. การตั้งค่า URLhaus
- ไม่จำเป็นต้องมีการตั้งค่าเพิ่มเติมสำหรับ URLhaus เนื่องจากใช้ API ที่เปิดให้บริการฟรี

### การสร้าง Trigger ในฐานข้อมูล
Trigger จะถูกสร้างขึ้นเพื่อเพิ่ม URL ใหม่ที่เข้ามาในตาราง `urls_to_check` สำหรับการตรวจสอบ:
```python
import sqlite3

def create_database_trigger():
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
        print("create_database_trigger(), Database trigger created successfully.")
    except sqlite3.Error as e:
        print(f"create_database_trigger(), Error creating database trigger: {e}")
    finally:
        if conn:
            conn.close()
```

### ฟังก์ชันการตรวจสอบ URL
ฟังก์ชันเหล่านี้จะทำการตรวจสอบ URL โดยใช้บริการต่างๆ:

#### Google Web Risk:
```python
import json
from google.api_core.exceptions import PermissionDenied

async def check_google_web_risk(url):
    try:
        uri = url
        threat_types = ["MALWARE", "SOCIAL_ENGINEERING"]
        response = webrisk_client.search_uris(uri=uri, threat_types=threat_types)
        if response.threat:
            return True
        else:
            return False
    except PermissionDenied as exc:
        print("check_google_web_risk(), Permission denied: ", exc)
        print("check_google_web_risk(), Please ensure the service account has the correct permissions and the Web Risk API is enabled.")
    return None
```

#### VirusTotal:
```python
import aiohttp

async def check_virustotal(url, session):
    try:
        async with session.post(
            VIRUSTOTAL_URLS_URL,
            data={"url": url},
            headers={"x-apikey": API_KEY},
        ) as response:
            result = await response.json()
            scan_id = result["data"]["id"]
        for _ in range(10):
            async with session.get(
                f"{VIRUSTOTAL_ANALYSIS_URL}{scan_id}",
                headers={"x-apikey": API_KEY},
            ) as response:
                analysis = await response.json()
                if analysis["data"]["attributes"]["status"] == "completed":
                    break
            await asyncio.sleep(5)
        if analysis["data"]["attributes"]["status"] == "completed":
            stats = analysis["data"]["attributes"]["stats"]
            if stats["malicious"] > 0:
                return True
            else:
                return False
        else:
            return None
    except vt.error.APIError as e:
        print(f"VirusTotal Error: {e}")
        return None
    except Exception as e:
        print(f"VirusTotal Unexpected error: {e}")
        return None
```

#### PhishTank:
```python
async def check_phishtank(url):
    try:
        if url in data_phishtank['url'].values:
            return True
        else:
            return False
    except FileNotFoundError:
        print(f"PhishTank Error: The file {csv_file} was not found.")
    except pd.errors.EmptyDataError:
        print(f"PhishTank Error: The file {csv_file} is empty.")
    except Exception as e:
        print(f"PhishTank An unexpected error occurred: {e}")
    return None
```

#### URLhaus:
```python
async def check_urlhaus(url, session):
    try:
        data_urlhaus = {'url' : url}
        async with session.post(URLHAUS_API, data=data_urlhaus) as response:
            json_response = await response.json()
            if json_response['query_status'] == 'ok':
                return True
            elif json_response['query_status'] == 'no_results':
                return False
            else:
                print("URLHAUS Something went wrong")
                return None
    except (
        aiohttp.ClientError,
        aiohttp.ClientResponseError,
        json.JSONDecodeError,
        KeyError,
    ) as e:
        print(f"Error checking URLhaus: {e}")
        return None
```

### ฟังก์ชันการจัดการฐานข้อมูล
ฟังก์ชันเหล่านี้จะจัดการกับฐานข้อมูล SQLite:

#### อัปเดตฐานข้อมูล:
```python
def update_database(url, status):
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE urls SET status = ? WHERE target_url = ?", (status, url))
        conn.commit()
    except sqlite3.Error as e:
        print(f"UPDATE Database error: {e}")
    except Exception as e:
        print(f"update_database(), Unexpected error: {e}")
    finally:
        if conn:
            conn.close()
```

#### อ่าน URL ใหม่ที่ต้องตรวจสอบ:
```python
def get_new_urls_from_database():
    urls = []
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT target_url FROM urls WHERE is_checked IS NULL OR is_checked = 0 ")
        urls = [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"get_new_urls_from_database(), Database error: {e}")
    except Exception as e:
        print(f"get_new_urls_from_database(), Unexpected error: {e}")
    finally:
        if conn:
            conn.close()
    return urls
```

#### อ่าน URL จากคิว:
```python
def get_urls_from_database():
    urls = []
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM urls_to_check GROUP BY url")
        urls = [row[0] for row in

 cursor.fetchall()]
        cursor.execute("DELETE FROM urls_to_check")
        conn.commit()
    except sqlite3.Error as e:
        print(f"get_urls_from_database(), Database error: {e}")
    finally:
        if conn:
            conn.close()
    return urls
```

#### อัปเดตสถานะ URL ที่ตรวจสอบแล้ว:
```python
def mark_urls_as_checked(urls):
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.executemany("UPDATE urls SET is_checked = 1 WHERE target_url = ?", [(url,) for url in urls])
        conn.commit()
    except sqlite3.Error as e:
        print(f"mark_urls_as_checked(), Database error: {e}")
    except Exception as e:
        print(f"mark_urls_as_checked(), Unexpected error: {e}")
    finally:
        if conn:
            conn.close()
```

### ฟังก์ชันหลักในการตรวจสอบ URL
ฟังก์ชันนี้จะทำการตรวจสอบ URL โดยใช้บริการต่างๆ และอัปเดตสถานะในฐานข้อมูล:

```python
async def check_url(url, session):
    tasks = {
        "Google Web Risk": check_google_web_risk(url),
        "VirusTotal": check_virustotal(url, session),
        "Phishtank": check_phishtank(url),
        "URLhaus": check_urlhaus(url, session)
    }
    results = await asyncio.gather(*tasks.values())
    is_dangerous = False

    for function_name, result in zip(tasks.keys(), results):
        if any(result is True for result in results):
            if result is True:
                print(f"The URL {url} is dangerous according to {function_name}.")
            elif result is False:
                print(f"No conclusive information for the URL {url} in {function_name}.")
            is_dangerous = True
        elif all(result is False for result in results if result is not None):
            print(f"The URL {url} is safe according to {function_name}.")
        else:
            print(f"No conclusive information for the URL {url} in {function_name}.")

    if is_dangerous:
        update_database(url, -1)
    else:
        update_database(url, 1)
```

### ฟังก์ชันหลักในการรับ URL และตรวจสอบ
ฟังก์ชันนี้จะทำการตรวจสอบ URL เป็น batch เพื่อเพิ่มประสิทธิภาพ:

```python
async def main(urls, batch_size=10):
    if isinstance(urls, str):
        urls = [urls]
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            tasks = [check_url(url, session) for url in batch]
            await asyncio.gather(*tasks)
            await asyncio.sleep(SLEEP_SECONDS)
        mark_urls_as_checked(urls)
```

### ฟังก์ชันการเรียกใช้งานหลัก
ฟังก์ชันนี้จะทำการเรียกใช้งานฟังก์ชันหลักในการตรวจสอบ URL:

```python
def run_main(urls):
    asyncio.run(main(urls))
```

### ฟังก์ชันตรวจสอบ URL เป็นระยะ
ฟังก์ชันนี้จะทำการตรวจสอบ URL ที่ยังไม่ได้ตรวจสอบในช่วงเวลาที่กำหนด:

```python
async def periodic_full_check(interval_hours=1):
    while True:
        urls_to_check = get_new_urls_from_database()
        if urls_to_check:
            await main(urls_to_check)
        await asyncio.sleep(interval_hours * 3600)
```

### ฟังก์ชันการตรวจสอบ URL ใหม่และตรวจสอบเป็นระยะ
ฟังก์ชันนี้จะทำการตรวจสอบ URL ใหม่ที่เข้ามาในคิวและทำการตรวจสอบ URL ที่ยังไม่ได้ตรวจสอบเป็นระยะ:

```python
async def main_task():
    async def check_urls_task():
        while True:
            urls_to_check = get_urls_from_database()
            if urls_to_check:
                await main(urls_to_check)
            await asyncio.sleep(SLEEP_SECONDS)

    loop = asyncio.get_event_loop()
    loop.create_task(periodic_full_check(interval_hours=INTERVAL_HOURS))
    loop.create_task(check_urls_task())
    await asyncio.Event().wait()
```

### ตัวอย่างการเรียกใช้งาน
โค้ดนี้จะสร้าง trigger ในฐานข้อมูลและเริ่มการตรวจสอบ URL:

```python
if __name__ == "__main__":
    create_database_trigger()
    asyncio.run(main_task())
```

### สรุป
- โค้ดนี้ถูกออกแบบมาให้ทำงานแบบ asynchronous เพื่อเพิ่มประสิทธิภาพในการตรวจสอบ URL
- มีการใช้บริการต่างๆ ในการตรวจสอบ URL ได้แก่ Google Web Risk, VirusTotal, PhishTank และ URLhaus
- มีการสร้าง trigger ในฐานข้อมูลเพื่อเพิ่ม URL ใหม่ที่เข้ามาในคิวสำหรับการตรวจสอบ
- มีฟังก์ชันในการตรวจสอบ URL ใหม่ที่เข้ามาและการตรวจสอบ URL เป็นระยะ

## URL Checker System User Guide Using Google Web Risk, VirusTotal, PhishTank, and URLhaus

### Introduction
This code aims to check URLs stored in a database for risks or threats using services from Google Web Risk, VirusTotal, PhishTank, and URLhaus. It operates asynchronously to enhance checking efficiency.

### Initial Setup

#### 1. Setting up the `.env` file
- Create a `config.env` file in the same folder as the code and define the following values:
  ```env
  INTERVAL_HOURS=2
  SLEEP_SECONDS=2
  DATABASE_PATH=/path/to/your/database.db
  URLHAUS_API=https://urlhaus-api.abuse.ch/v1/url/
  PHISHTANK_CSV=/path/to/your/verified_online.csv
  VIRUSTOTAL_ANALYSIS_URL=https://www.virustotal.com/api/v3/analyses/
  VIRUSTOTAL_URLS_URL=https://www.virustotal.com/api/v3/urls
  VIRUSTOTAL_API_KEY=your_virustotal_api_key
  ```

- Load values from the `.env` file:
  ```python
  import os
  from dotenv import load_dotenv

  load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'config.env'))

  INTERVAL_HOURS = int(os.getenv("INTERVAL_HOURS", 2))
  SLEEP_SECONDS = int(os.getenv("SLEEP_SECONDS", 2))
  DATABASE_PATH = os.getenv("DATABASE_PATH")
  URLHAUS_API = os.getenv("URLHAUS_API")
  PHISHTANK_CSV = os.getenv("PHISHTANK_CSV")
  VIRUSTOTAL_ANALYSIS_URL = os.getenv("VIRUSTOTAL_ANALYSIS_URL")
  VIRUSTOTAL_URLS_URL = os.getenv("VIRUSTOTAL_URLS_URL")
  API_KEY = os.getenv("VIRUSTOTAL_API_KEY")

  print(f"Database Path: {DATABASE_PATH}")
  ```

#### 2. Google Web Risk Setup
- You need a JSON credential file from Google Cloud, which can be created from the Google Cloud Console.
- Specify the path of the credential file:
  ```python
  credentials_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api-project-xxxxxx.json")
  ```

- Set the environment variable for authentication:
  ```python
  if os.path.exists(credentials_path):
      os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
  else:
      print("Google Credential file not found.")
  ```

- Create a client for Google Web Risk:
  ```python
  from google.cloud import webrisk_v1

  webrisk_client = webrisk_v1.WebRiskServiceClient()
  ```

#### 3. VirusTotal Setup
- You need a VirusTotal API key, which can be generated from VirusTotal.
- Read the API key value from the `.env` file:
  ```python
  import vt

  API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
  vt_client = vt.Client(API_KEY)
  ```

#### 4. PhishTank Setup
- The CSV file from PhishTank needs to be downloaded and stored in the specified path:
  ```python
  import pandas as pd

  csv_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), str(PHISHTANK_CSV))
  data_phishtank = pd.read_csv(csv_file)
  ```

#### 5. URLhaus Setup
- No additional setup is required for URLhaus as it uses a freely available API.

### Creating a Database Trigger
A trigger will be created to add new URLs that enter the `urls_to_check` table for checking:
```python
import sqlite3

def create_database_trigger():
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
        print("create_database_trigger(), Database trigger created successfully.")
    except sqlite3.Error as e:
        print(f"create_database_trigger(), Error creating database trigger: {e}")
    finally:
        if conn:
            conn.close()
```

### URL Checking Functions
These functions will check URLs using various services:

#### Google Web Risk:
```python
import json
from google.api_core.exceptions import PermissionDenied

async def check_google_web_risk(url):
    try:
        uri = url
        threat_types = ["MALWARE", "SOCIAL_ENGINEERING"]
        response = webrisk_client.search_uris(uri=uri, threat_types=threat_types)
        if response.threat:
            return True
        else:
            return False
    except PermissionDenied as exc:
        print("check_google_web_risk(), Permission denied: ", exc)
        print("check_google_web_risk(), Please ensure the service account has the correct permissions and the Web Risk API is enabled.")
    return None
```

#### VirusTotal:
```python
import aiohttp

async def check_virustotal(url, session):
    try:
        async with session.post(
            VIRUSTOTAL_URLS_URL,
            data={"url": url},
            headers={"x-apikey": API_KEY},
        ) as response:
            result = await response.json()
            scan_id = result["data"]["id"]
        for _ in range(10):
            async with session.get(
                f"{VIRUSTOTAL_ANALYSIS_URL}{scan_id}",
                headers={"x-apikey": API_KEY},
            ) as response:
                analysis = await response.json()
                if analysis["data"]["attributes"]["status"] == "completed":
                    break
            await asyncio.sleep(5)
        if analysis["data"]["attributes"]["status"] == "completed":
            stats = analysis["data"]["attributes"]["stats"]
            if stats["malicious"] > 0:
                return True
            else:
                return False
        else:
            return None
    except vt.error.APIError as e:
        print(f"VirusTotal Error: {e}")
        return None
    except Exception as e:
        print(f"VirusTotal Unexpected error: {e}")
        return None
```

#### PhishTank:
```python
async def check_phishtank(url):
    try:
        if url in data_phishtank['url'].values:
            return True
        else:
            return False
    except FileNotFoundError:
        print(f"PhishTank Error: The file {csv_file} was not found.")
    except pd.errors.EmptyDataError:
        print(f"PhishTank Error: The file {csv_file} is empty.")
    except Exception as e:
        print(f"PhishTank An unexpected error occurred: {e}")
    return None
```

#### URLhaus:
```python
async def check_urlhaus(url, session):
    try:
        data_urlhaus = {'url' : url}
        async with session.post(URLHAUS_API, data=data_urlhaus) as response:
            json_response = await response.json()
            if json_response['query_status'] == 'ok':
                return True
            elif json_response['query_status'] == 'no_results':
                return False
            else:
                print("URLHAUS Something went wrong")
                return None
    except (
        aiohttp.ClientError,
        aiohttp.ClientResponseError,
        json.JSONDecodeError,
        KeyError,
    ) as e:
        print(f"Error checking URLhaus: {e}")
        return None
```

### Database Management Functions
These functions will manage the SQLite database:

#### Update Database:
```python
def update_database(url, is_active):
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE urls SET is_active = ? WHERE target_url = ?", (is_active, url))
        conn.commit()
    except sqlite3.Error as e:
        print(f"UPDATE Database error: {e}")
    except Exception as e:
        print(f"update_database(), Unexpected error: {e}")
    finally:
        if conn:
            conn.close()
```

#### Read New URLs to Check:
```python
def get_new_urls_from_database():
    urls = []
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT target_url FROM urls WHERE is_checked IS NULL OR is_checked = 0 ")
        urls = [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"get_new_urls_from_database(), Database error: {e}")
    except Exception as e:
        print(f"get_new_urls_from_database(), Unexpected error: {e}")
    finally:
        if conn:
            conn.close()
    return urls
```

#### Read URLs from Queue:
```python
def get_urls_from_database():
    urls = []
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM urls_to_check GROUP BY url")
        urls = [row[0] for row in cursor.fetchall()]
        cursor.execute("DELETE FROM urls_to_check")
        conn.commit()
    except sqlite3.Error as e:
        print(f"get_urls_from_database(), Database error: {e}")
    finally:
        if conn:
            conn.close()
    return urls
```

#### Update Status of Checked URLs:
```python
def mark_urls_as_checked(urls):
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.executemany("UPDATE urls SET is_checked = 1 WHERE target_url = ?", [(url,) for url in urls])
        conn.commit()
    except sqlite3.Error as e:
        print(f"mark_urls_as_checked(), Database error: {e}")
    except Exception as e:
        print(f"mark_urls_as_checked(), Unexpected error: {e}")
    finally:
        if conn:
            conn.close()
```

### Main URL Checking Function
This function checks URLs using various services and updates their status in the database:

```python
async def check_url(url, session):
    tasks = {
        "Google Web Risk": check_google_web_risk(url),
        "VirusTotal": check_virustotal(url, session),
        "PhishTank": check_phishtank(url),
        "URLhaus": check_urlhaus(url, session)
    }
    results = await asyncio.gather(*tasks.values())
    is_dangerous = False

    for function_name, result in zip(tasks.keys(), results):
        if any(result is True for result in results):
            if result is True:
                print(f"The URL {url} is dangerous according to {function_name}.")
            elif result is False:
                print(f"No conclusive information for the URL {url} in {function_name}.")
            is_dangerous = True
        elif all(result is False for result in results if result is not None):
            print(f"The URL {url} is safe according to {function_name}.")
        else:
            print(f"No conclusive information for the URL {url} in {function_name}.")

    if is_dangerous:
        update_database(url, -1)
    else:
        update_database(url, 1)
```

### Main Function to Get and Check URLs
This function checks URLs in batches for improved efficiency:

```python
async def main(urls, batch_size=10):
    if isinstance(urls, str):
        urls = [urls]
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            tasks = [check_url(url, session) for url in batch]
            await asyncio.gather(*tasks)
            await asyncio.sleep(SLEEP_SECONDS)
        mark_urls_as_checked(urls)
```

### Main Execution Function
This function calls the main URL checking function:

```python
def run_main(urls):
    asyncio.run(main(urls))
```

### Periodic URL Check Function
This function checks unchecked URLs at specified intervals:

```python
async def periodic_full_check(interval_hours=1):
    while True:
        urls_to_check = get_new_urls_from_database()
        if urls_to_check:
            await main(urls_to_check)
        await asyncio.sleep(interval_hours * 3600)
```

### Function to Check New URLs and Periodically Check
This function checks new URLs entering the queue and periodically checks unchecked URLs:

```python
async def main_task():
    async def check_urls_task():
        while True:
            urls_to_check = get_urls_from_database()
            if urls_to_check:
                await main(urls_to_check)
            await asyncio.sleep(SLEEP_SECONDS)

    loop = asyncio.get_event_loop()
    loop.create_task(periodic_full_check(interval_hours=INTERVAL_HOURS))
    loop.create_task(check_urls_task())
    await asyncio.Event().wait()
```

### Example Usage
This code creates a database trigger and starts the URL checking process:

```python
if __name__ == "__main__":
    create_database_trigger()
    asyncio.run(main_task())
```

### Summary
- This code is designed to run asynchronously for efficient URL checking.
- It utilizes various services for URL checking: Google Web Risk, VirusTotal, PhishTank, and URLhaus.
- A database trigger is created to add new URLs to the checking queue.
- Functions are provided for checking new URLs and periodically checking unchecked URLs.

### Run by pm2
```
pm2 start check_urls.py --name check_urls --interpreter /home/seal/venv/bin/python
```

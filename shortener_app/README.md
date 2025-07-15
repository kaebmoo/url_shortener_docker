# gogoth
## Secure Shortened URL

### Build a URL Shortener With FastAPI and Python

> _Adapted from_ [https://realpython.com/build-a-python-url-shortener-with-fastapi/](https://realpython.com/build-a-python-url-shortener-with-fastapi/)

**Key Updates:**

*   **Pydantic V2 Support:** The source code has been enhanced to seamlessly work with pydantic version 2.
*   **Additional Settings:** `pydantic-settings` has been integrated for more configuration options.
*   **Migration Guide:** For detailed information on the migration process, refer to [https://docs.pydantic.dev/latest/migration/](https://docs.pydantic.dev/latest/migration/)
*   **Code Transformation:** The source code has been modified using `bump-pydantic`, with the `config.py` file being the primary target of changes.
*   **Websocket Integration:** Real-time URL updates are now supported through websockets.
*   **Asynchronous Page Info Retrieval:** Title and favicon extraction from target URLs is performed asynchronously using `asyncio` and `aiohttp` to improve responsiveness.
*   **API Key Management:** A new endpoint for registering API keys has been added, along with enhanced API key verification and role-based access control.
*   **Blacklisting:** URLs can now be blacklisted to prevent shortening of undesired content.
*   **Custom Key Support:** Users with appropriate permissions can now create short URLs with custom keys.
*   **User Information:** Endpoints for retrieving the count of shortened URLs and a list of shortened URLs for a specific user have been added.
*   **Enhanced Error Handling:** Improved HTTP exception handling and informative error messages.

**Running the Live Server**

You have two options for launching the live server:

1.  **Using uvicorn:**

    ```bash
    uvicorn shortener_app.main:app --reload
    ```

2.  **With Python3:**

    ```bash
    python3 -m uvicorn shortener_app.main:app --reload
    ```

### Key Functions and Endpoints in `main.py`

The `main.py` file serves as the core of your URL shortening API, housing essential functions and endpoints to handle various aspects of the application. Here's a breakdown of its key components:

**Helper Functions**

*   **`get_admin_info`:** Constructs user-friendly URLs for managing shortened link data, incorporating QR code generation.
*   **`raise_*` functions:** Define custom HTTP exceptions for common error scenarios like 404 (Not Found), 400 (Bad Request), 401 (Unauthorized), and others, enhancing error handling and user experience.
*   **`get_db`, `get_api_db`, `get_blacklist_db`:** Establish database connections for the main URL data, API keys, and blacklisted URLs, respectively, ensuring proper database interaction.
*   **`verify_jwt_token`, `create_access_token`, `refresh_token`:** Implement JWT-based authentication and token management for secure user access control.
*   **`verify_api_key`:** Validates API keys against the database, ensuring only authorized requests are processed.
*   **`fetch_page_info`, `fetch_page_info_and_update_sync`, `fetch_page_info_and_update`:** Asynchronously retrieve title and favicon information from target URLs using `asyncio` and `aiohttp`, improving application responsiveness.
*   **`normalize_url`:** Standardizes URLs by handling trailing slashes consistently.
*   **`generate_qr_code`:** Generates QR codes for shortened URLs, enhancing user experience and sharing capabilities.
*   **`custom_openapi`:** Customizes the OpenAPI schema for improved documentation and clarity.

**API Endpoints**

*   **`/`:** A simple welcome message endpoint.
*   **`/about`:** An HTML page providing information about the URL shortener.
*   **`/api/register_api_key`:** Registers new API keys, enabling secure access to the API.
*   **`/api/deactivate_api_key`:** Deactivates API keys, disabling further access.
*   **`/api/refresh_token`:** Refreshes JWT tokens for continued authentication.
*   **`/capture_screen`:** Captures a screenshot of a target website and stores the image.
*   **`/check-phishing`:** Checks if a target URL is associated with phishing activities.
*   **`/preview_url`:** Displays a preview of the target URL, including title and favicon.
*   **`/{url_key}`:** Redirects users from shortened URLs to their original targets, handling potential errors gracefully.
*   **`/url`:** Creates new shortened URLs, optionally with custom keys (for authorized users), and initiates background tasks to fetch page information.
*   **`/user/url_count`:** Provides user-specific information like the count of shortened URLs.
*   **`/user/urls`:** Retrieves a list of shortened URLs created by a specific user.
*   **`/user/url/status`:** Updates the status of a specific URL owned by the user.
*   **`/admin/{secret_key}`:** Fetches detailed information and management options for a shortened URL based on its secret key.
*   **`/admin/{secret_key}` (DELETE):** Deletes a shortened URL based on its secret key.
*   **`/ws/url_update/{secret_key}`:** A websocket endpoint for real-time updates on URL information.

### การนำ title, favicon url เพิ่มในฐานข้อมูล

## ความสัมพันธ์ของ 3 ฟังก์ชัน `fetch_page_info`, `fetch_page_info_and_update_sync`, `fetch_page_info_and_update`

ทั้งสามฟังก์ชันนี้ทำงานร่วมกันเพื่อดึงข้อมูล title และ favicon จาก URL ที่กำหนดให้ และอัปเดตข้อมูลเหล่านี้ลงในฐานข้อมูล โดยมีการแบ่งหน้าที่และการทำงานแบบ asynchronous และ synchronous ดังนี้

1. **`fetch_page_info(url: str)`**

* **หน้าที่:** ดึงข้อมูล title และ favicon จาก URL ที่กำหนดให้
* **ลักษณะการทำงาน:** เป็น asynchronous coroutine ที่ใช้ `aiohttp` ในการส่งคำร้องขอ HTTP และ `BeautifulSoup` ในการ parse HTML เพื่อดึงข้อมูล
* **อินพุต:** URL ของหน้าเว็บที่ต้องการดึงข้อมูล
* **เอาต์พุต:** คืนค่า tuple `(title, favicon_url)` หรือ `(None, None)` หากเกิดข้อผิดพลาด

2. **`fetch_page_info_and_update_sync(db_url: models.URL)`**

* **หน้าที่:** ดึงข้อมูล title และ favicon จาก URL ที่อยู่ในออบเจกต์ `db_url` แล้วอัปเดตข้อมูลเหล่านี้ลงในฐานข้อมูล
* **ลักษณะการทำงาน:** เป็น synchronous function ที่เรียกใช้ `fetch_page_info` แบบ asynchronous ภายใน thread pool เพื่อหลีกเลี่ยงการบล็อก event loop หลัก
* **อินพุต:** ออบเจกต์ `db_url` ที่มีข้อมูล URL ที่ต้องการดึงข้อมูลและอัปเดต
* **เอาต์พุต:** ไม่มีการคืนค่าโดยตรง แต่จะทำการอัปเดตข้อมูล title และ favicon ในฐานข้อมูล

3. **`async def fetch_page_info_and_update(db_url: models.URL)`**

* **หน้าที่:** เป็น wrapper สำหรับ `fetch_page_info_and_update_sync` เพื่อให้สามารถเรียกใช้ฟังก์ชัน synchronous ภายใน asynchronous context ได้
* **ลักษณะการทำงาน:** เป็น asynchronous coroutine ที่ใช้ `loop.run_in_executor` เพื่อเรียกใช้ `fetch_page_info_and_update_sync` ใน thread pool แบบ asynchronous
* **อินพุต:** ออบเจกต์ `db_url` ที่มีข้อมูล URL ที่ต้องการดึงข้อมูลและอัปเดต
* **เอาต์พุต:** ไม่มีการคืนค่าโดยตรง แต่จะทำการอัปเดตข้อมูล title และ favicon ในฐานข้อมูลผ่าน `fetch_page_info_and_update_sync`

**สรุปความสัมพันธ์**

* `fetch_page_info` เป็นฟังก์ชันหลักที่ทำหน้าที่ดึงข้อมูล title และ favicon
* `fetch_page_info_and_update_sync` เป็นฟังก์ชัน synchronous ที่เรียกใช้ `fetch_page_info` และอัปเดตฐานข้อมูล
* `fetch_page_info_and_update` เป็น wrapper asynchronous ที่เรียกใช้ `fetch_page_info_and_update_sync` ใน thread pool เพื่อให้สามารถทำงานร่วมกับส่วนอื่นๆ ของแอปพลิเคชันที่เป็น asynchronous ได้

**การทำงานร่วมกัน**

เมื่อมีการสร้าง short URL ใหม่ ฟังก์ชัน `create_url` จะเพิ่ม `fetch_page_info_and_update` ลงใน `BackgroundTasks` ทำให้ FastAPI เรียกใช้ฟังก์ชันนี้ในเบื้องหลังหลังจากส่ง response กลับไปให้ client แล้ว `fetch_page_info_and_update` จะเรียกใช้ `fetch_page_info_and_update_sync` ใน thread pool เพื่อดึงข้อมูล title และ favicon และอัปเดตฐานข้อมูล ทำให้การสร้าง short URL ไม่ถูกบล็อกโดยการดึงข้อมูล และแอปพลิเคชันยังคงตอบสนองต่อผู้ใช้ได้อย่างรวดเร็ว


**`nginx.conf`**

```
location / {
                # rewrite ^/api/v1/(.*)$ /$1 break;
                proxy_pass http://127.0.0.1:8000;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;

		        # รองรับ WebSocket

                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "Upgrade";
}
```

---

ตัวอย่างการใช้งาน API ด้วย `curl`:

### 1. **POST /api/register_api_key**
   **Request:**
   ```bash
   curl -X POST "https://kaebmoo.com/api/register_api_key" \
   -H "Authorization: Bearer YOUR_JWT_TOKEN" \
   -H "Content-Type: application/json" \
   -d '{"api_key": "YOUR_API_KEY", "role_id": 1}'
   ```

### 2. **POST /api/deactivate_api_key**
   **Request:**
   ```bash
   curl -X POST "https://kaebmoo.com/api/deactivate_api_key" \
   -H "Authorization: Bearer YOUR_JWT_TOKEN" \
   -H "Content-Type: application/json" \
   -d '{"api_key": "YOUR_API_KEY"}'
   ```

### 3. **POST /api/refresh_token**
   **Request:**
   ```bash
   curl -X POST "https://kaebmoo.com/api/refresh_token" \
   -H "Content-Type: application/json" \
   -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
   ```

### 4. **POST /capture_screen**
   **Request:**
   ```bash
   curl -X POST "https://kaebmoo.com/capture_screen" \
   -H "X-API-KEY: YOUR_API_KEY" \
   -H "Content-Type: application/json" \
   -d '{"url_key": "YOUR_URL_KEY"}'
   ```

### 5. **GET /preview_url**
   **Request:**
   ```bash
   curl -X GET "https://kaebmoo.com/preview_url" \
   -H "token: YOUR_SECRET_TOKEN" \
   -d "url=https://example.com"
   ```

### 6. **GET /check-phishing/**
   **Request:**
   ```bash
   curl -X GET "https://kaebmoo.com/check-phishing/?url=https://example.com"
   ```

### 7. **GET /{url_key}**
   **Request:**
   ```bash
   curl -X GET "https://kaebmoo.com/{url_key}"
   ```

### 8. **POST /url**
   **Request:**
   ```bash
   curl -X POST "https://kaebmoo.com/url" \
   -H "X-API-KEY: YOUR_API_KEY" \
   -H "Content-Type: application/json" \
   -d '{"target_url": "https://example.com", "custom_key": "custom-key"}'
   ```

### 9. **GET /user/url_count**
   **Request:**
   ```bash
   curl -X GET "https://kaebmoo.com/user/url_count" \
   -H "X-API-KEY: YOUR_API_KEY"
   ```

### 10. **GET /user/urls**
   **Request:**
   ```bash
   curl -X GET "https://kaebmoo.com/user/urls" \
   -H "X-API-KEY: YOUR_API_KEY"
   ```

### 11. **POST /user/url/status**
   **Request:**
   ```bash
   curl -X POST "https://kaebmoo.com/user/url/status" \
   -H "X-API-KEY: YOUR_API_KEY" \
   -H "Content-Type: application/json" \
   -d '{"secret_key": "YOUR_SECRET_KEY", "target_url": "https://example.com"}'
   ```

### 12. **GET /admin/{secret_key}**
   **Request:**
   ```bash
   curl -X GET "https://kaebmoo.com/admin/{secret_key}" \
   -H "X-API-KEY: YOUR_API_KEY"
   ```

### 13. **DELETE /admin/{secret_key}**
   **Request:**
   ```bash
   curl -X DELETE "https://kaebmoo.com/admin/{secret_key}" \
   -H "X-API-KEY: YOUR_API_KEY"
   ```

**หมายเหตุ:** โปรดแทนที่ `YOUR_JWT_TOKEN`, `YOUR_API_KEY`, `YOUR_URL_KEY`, `YOUR_SECRET_KEY`, และ `YOUR_SECRET_TOKEN` ด้วยค่าจริงที่เหมาะสม.

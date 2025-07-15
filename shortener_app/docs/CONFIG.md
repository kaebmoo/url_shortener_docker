```
# .env
ENV_NAME=Development
BASE_URL=http://127.0.0.1:8000
HOST=127.0.0.1
PORT=8080
DB_URL=sqlite:////shortener.db # shortener database
DB_API=sqlite:////apikey.db # api key database
DB_BLACKLIST=sqlite:////blacklist.db    # blacklist database
SECRET_KEY= # secret key เดียวกันกับ user_management ใช้เป็น api token, jwt token
ACCESS_TOKEN_EXPIRE_MINUTES=30
USE_API_DB=False  # ใช้กำหนดว่าจะให้ตรวจ role_id หรือไม่ สำหรับการทำ custom key, ยังไม่ได้ใช้งาน โปรแกรมตรวจ role_id เสมอ
SAFE_HOST=https://kaebmoo.com/apps # ใช้กำหนด host ที่จะให้เปิดแทน กรณีที่ url = "DANGER" 
```

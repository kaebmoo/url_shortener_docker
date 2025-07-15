```
-- urls definition

CREATE TABLE urls (
	id INTEGER NOT NULL, 
	"key" VARCHAR, 
	secret_key VARCHAR, 
	target_url VARCHAR, 
	is_active BOOLEAN, 
	clicks INTEGER, 
	api_key VARCHAR, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	updated_at DATETIME, 
	is_checked BOOLEAN, 
	status VARCHAR, 
	title VARCHAR(255), 
	favicon_url VARCHAR(255), 
	PRIMARY KEY (id)
);

CREATE INDEX ix_urls_api_key ON urls (api_key);
CREATE UNIQUE INDEX ix_urls_key ON urls ("key");
CREATE UNIQUE INDEX ix_urls_secret_key ON urls (secret_key);
CREATE INDEX ix_urls_target_url ON urls (target_url);

shortener_app/models.py

class URL(Base):
    __tablename__ = "urls"  # ชื่อ table ใน sqlite

    id = Column(Integer, primary_key=True)                  # primary key
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

```

ในกรณีของ FastAPI การสร้างฐานข้อมูลจาก models.py ที่คุณให้มาสามารถทำได้โดยใช้ Alembic ซึ่งเป็นเครื่องมือสำหรับจัดการ migration ของ SQLAlchemy

**ขั้นตอน:**

1. **ติดตั้ง Alembic:**

   ```bash
   pip install alembic
   ```

2. **กำหนดค่า Alembic:**

   * สร้างไฟล์ `alembic.ini` ใน root directory ของโปรเจ็กต์ของคุณ โดยมีเนื้อหาดังนี้ (ปรับแต่งตามการตั้งค่าฐานข้อมูลของคุณ):

   ```ini
   [alembic]
   script_location = alembic
   sqlalchemy.url = sqlite:///./shortener.db 
   ```

3. **เริ่มต้น Alembic:**

   ```bash
   alembic init alembic
   ```

   คำสั่งนี้จะสร้างโฟลเดอร์ `alembic` ที่มีไฟล์สำหรับจัดการ migration

4. **สร้าง migration แรก:**

   ```bash
   alembic revision --autogenerate -m "create initial tables"
   ```

   Alembic จะตรวจสอบ models.py ของคุณ และสร้างไฟล์ migration ในโฟลเดอร์ `alembic/versions` ที่มีคำสั่ง SQL สำหรับสร้างตารางต่างๆ

5. **ปรับใช้ migration:**

   ```bash
   alembic upgrade head
   ```

   คำสั่งนี้จะดำเนินการ migration และสร้างตารางในฐานข้อมูลของคุณ

**ตัวอย่างการใช้งานใน FastAPI:**

```python
from fastapi import FastAPI
from database import engine  # Assuming you have an engine defined in database.py

app = FastAPI()

# ... other FastAPI code ...

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # ตรวจสอบว่าตารางมีอยู่หรือไม่ (อาจใช้ metadata.tables.contains() หรือวิธีอื่น)
        if not engine.dialect.has_table(conn, "urls"): 
            await conn.run_sync(Base.metadata.create_all) 
```

**คำอธิบายเพิ่มเติม:**

* **Alembic** ช่วยให้คุณสามารถจัดการการเปลี่ยนแปลงโครงสร้างฐานข้อมูลได้อย่างมีระบบ โดยสร้างไฟล์ migration ที่บันทึกการเปลี่ยนแปลงแต่ละครั้ง ทำให้คุณสามารถย้อนกลับหรือปรับใช้การเปลี่ยนแปลงได้ง่าย
* ในตัวอย่าง FastAPI เราใช้ `app.on_event("startup")` เพื่อตรวจสอบและสร้างตารางเมื่อแอปพลิเคชันเริ่มทำงาน ถ้าตารางยังไม่มีอยู่ ก็จะสร้างตารางทั้งหมดจาก models ที่กำหนดไว้ใน `Base.metadata`

**ข้อควรระวัง:**

* ตรวจสอบให้แน่ใจว่าการตั้งค่าฐานข้อมูลใน `alembic.ini` และ `database.py` ถูกต้อง
* ระมัดระวังในการปรับใช้ migration ในสภาพแวดล้อม production เพราะอาจส่งผลกระทบต่อข้อมูลที่มีอยู่
* พิจารณาใช้ `--run-syncdb` ในกรณีที่คุณต้องการสร้างฐานข้อมูลใหม่ทั้งหมด แต่ควรใช้ด้วยความระมัดระวังเพราะจะลบข้อมูลที่มีอยู่ทั้งหมด

**เพิ่มเติม:**

* คุณสามารถเรียนรู้เพิ่มเติมเกี่ยวกับ Alembic ได้จากเอกสารอย่างเป็นทางการ: [https://alembic.sqlalchemy.org/](https://alembic.sqlalchemy.org/)
* หากคุณต้องการปรับแต่งวิธีการสร้างตารางหรือมี logic เพิ่มเติม คุณสามารถแก้ไขไฟล์ migration ที่ Alembic สร้างขึ้นได้


การสร้างฐานข้อมูลแยกกันรวมถึงวิธีการแก้ไขไฟล์ `env.py` สำหรับแต่ละฐานข้อมูล:

### 1. Initialize Alembic สำหรับแต่ละฐานข้อมูล
เริ่มต้น Alembic environment สำหรับแต่ละฐานข้อมูล:

```bash
alembic init alembic       # สำหรับฐานข้อมูล shortener.db
alembic init apikey        # สำหรับฐานข้อมูล apikey.db
alembic init blacklist     # สำหรับฐานข้อมูล blacklist.db
```

### 2. แก้ไขไฟล์ `env.py` สำหรับแต่ละฐานข้อมูล
สำหรับแต่ละฐานข้อมูล คุณต้องแก้ไขไฟล์ `env.py` ในโฟลเดอร์ Alembic ที่ถูกสร้างขึ้น

#### 2.1 `env.py` สำหรับ `shortener.db`

แก้ไขไฟล์ `shortener_app/alembic/env.py` ดังนี้:

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# เพิ่ม path ของโปรเจคให้ถูกต้อง
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# นำเข้า Base ที่ใช้กับ shortener.db
from shortener_app.database import Base
from shortener_app.models import *  # นำเข้าทุก model ที่เกี่ยวข้องกับ shortener.db

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

#### 2.2 `env.py` สำหรับ `apikey.db`

แก้ไขไฟล์ `shortener_app/apikey/env.py` ดังนี้:

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# เพิ่ม path ของโปรเจคให้ถูกต้อง
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# นำเข้า BaseAPI ที่ใช้กับ apikey.db
from shortener_app.database import BaseAPI
from shortener_app.models import APIKey, Role  # นำเข้าทุก model ที่เกี่ยวข้องกับ apikey.db

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = BaseAPI.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

#### 2.3 `env.py` สำหรับ `blacklist.db`

แก้ไขไฟล์ `shortener_app/blacklist/env.py` ดังนี้:

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# เพิ่ม path ของโปรเจคให้ถูกต้อง
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# นำเข้า BaseBlacklist ที่ใช้กับ blacklist.db
from shortener_app.database import BaseBlacklist
from shortener_app.models import Blacklist  # นำเข้าทุก model ที่เกี่ยวข้องกับ blacklist.db

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = BaseBlacklist.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 3. สร้าง Migrations แยกกันสำหรับแต่ละฐานข้อมูล
ใช้คำสั่ง `alembic revision --autogenerate` สำหรับแต่ละ environment เพื่อสร้าง migration files:

```bash
alembic alembic revision --autogenerate -m "create initial tables for shortener.db"
alembic -n apikey revision --autogenerate -m "create initial tables for apikey.db"
alembic -n blacklist revision --autogenerate -m "create initial tables for blacklist.db"
```

### 4. Apply Migrations ให้กับแต่ละฐานข้อมูล
ใช้คำสั่ง `alembic upgrade head` เพื่อปรับใช้ migration ที่สร้างขึ้นกับแต่ละฐานข้อมูล:

```bash
alembic upgrade head                       # อัปเกรดฐานข้อมูล shortener.db
alembic -n apikey upgrade head             # อัปเกรดฐานข้อมูล apikey.db
alembic -n blacklist upgrade head          # อัปเกรดฐานข้อมูล blacklist.db
```

การทำตามขั้นตอนนี้จะช่วยให้คุณสามารถจัดการ migrations สำหรับแต่ละฐานข้อมูลได้อย่างแยกส่วนและเป็นระเบียบครับ

```
# ยังไม่จำเป็นต้องใช้ เพราะ ใน URL มี field วันที่สร้างอยู่แล้ว 
class URLExpiry(Base):
    ''' Short URLs for guests will expire in 30 days.'''
    __tablename__ = "url_expiry"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    key = Column(String, ForeignKey('urls.key'), unique=True, index=True)
    expiry_date = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=30))

    url = relationship("URL", back_populates="expiry_info")
```
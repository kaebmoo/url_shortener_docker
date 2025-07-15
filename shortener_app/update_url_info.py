import asyncio
import aiohttp
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import urljoin

from shortener_app.models import URL
from shortener_app.config import get_settings

DATABASE_URL = get_settings().db_url  # ควรเปลี่ยนเป็น URL ของฐานข้อมูลที่คุณใช้

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def fetch_page_info(url: str):
    """Fetch title and favicon from the given URL asynchronously."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                content = await response.text()

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

    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None, None

def update_db_url_page_info(db: Session, db_url: URL, title: str, favicon_url: str):
    """Update the title and favicon_url of a URL object in the database."""
    db_url.title = title
    db_url.favicon_url = favicon_url
    db_url.is_checked = True  # อัปเดต is_checked เป็น True
    db.commit()
    db.refresh(db_url)

async def update_url_info(db: Session):
    """Fetch and update URL info for all URLs in the database."""
    urls = db.query(URL).filter(URL.status == "SAFE").all()
    for db_url in urls:
        title, favicon_url = await fetch_page_info(db_url.target_url)
        update_db_url_page_info(db, db_url, title, favicon_url)

def main():
    db = SessionLocal()
    asyncio.run(update_url_info(db))
    db.close()

if __name__ == "__main__":
    main()

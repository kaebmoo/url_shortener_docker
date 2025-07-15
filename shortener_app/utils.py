import os
from pathlib import Path
import re
import socket
import logging 

from ipaddress import ip_network, ip_address, IPv6Address, IPv4Address
from urllib.parse import urlparse
from playwright.async_api import async_playwright
import aiohttp
from aiohttp.client_exceptions import ClientConnectorError

INTERNAL_IP_RANGES = [
    # IPv4 private address ranges
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
    
    # IPv6 private address ranges
    ip_network("fc00::/7"),  # Unique Local Addresses (ULA)
    ip_network("fe80::/10"), # Link-Local Addresses
]

def has_trailing_asterisks(url_key: str) -> bool:
    """ตรวจสอบว่า url_key มีเครื่องหมาย * ต่อท้ายหรือไม่

    Args:
        url_key (str): สตริงที่ต้องการตรวจสอบ

    Returns:
        bool: True ถ้ามีเครื่องหมาย * ต่อท้าย, False ถ้าไม่มี
    """

    # ตัวอย่าง Regex ที่ยืดหยุ่น:
    # - \*$: ตรวจสอบเครื่องหมาย * หนึ่งตัวขึ้นไปที่ท้ายสตริง
    # - .*:\*: อนุญาตให้มีตัวอักษรหรือตัวเลขใดๆ ก่อนเครื่องหมาย *
    # ปรับเปลี่ยน Regex ตามความต้องการ
    pattern = r'\*$'  # ตรวจสอบ * หนึ่งตัวขึ้นไปที่ท้ายสตริง
    return re.search(pattern, url_key) is not None

def remove_trailing_asterisks(url_key: str) -> str:
    """ลบเครื่องหมาย * ทั้งหมดที่อยู่ท้ายของ url_key

    Args:
        url_key (str): สตริงที่ต้องการลบเครื่องหมาย *

    Returns:
        str: สตริงที่ลบเครื่องหมาย * ออกแล้ว
    """

    # ตัวอย่าง Regex ที่ครอบคลุม:
    # - \*+: ตรวจสอบเครื่องหมาย * หนึ่งตัวขึ้นไปที่ท้ายสตริง
    pattern = r'\*+'
    return re.sub(pattern, '', url_key)


def validate_and_correct_url(url: str) -> str:
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        # Add 'http' if no scheme is present
        url = 'http://' + url
    return url

def validate_url(url):
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return False
    return True


async def fetch_content_type(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url) as response:
                return response.headers.get('Content-Type')
    except ClientConnectorError as e:
        print(f"Connection error: {e}")
        return None
        
# async def capture_screenshot(url: str):
    '''content_type = await fetch_content_type(url)
    if 'text/html' not in content_type:
        print(f"URL is not an HTML page, content type: {content_type}")
        return None
    '''    
async def capture_screenshot(url: str):
    async with async_playwright() as playwright:
        parsed_url = urlparse(url)
        file_name = f"{parsed_url.netloc}{parsed_url.path.replace('/', '_')}.png"
        
        # Define the correct directory path relative to the project structure
        base_dir = os.path.dirname(__file__)  # Get the directory of the current script
        output_dir = os.path.join(base_dir, "static", "screenshots")
        os.makedirs(output_dir, exist_ok=True)  # Create the directory if it doesn't exist

        # Construct the full path to save the screenshot
        output_path = os.path.join(output_dir, file_name)

        # Launch the browser and take the screenshot
        firefox = playwright.firefox
        browser = await firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(url, timeout=30000, wait_until="networkidle")
        except Exception as e:
            logging.error(f"Error: {e}")
            return None

        await page.screenshot(path=output_path, full_page=False)
        await browser.close()

        return file_name  # Return only the file name, not the full path
    

def is_host_active(target_url):
    ''' check target url is active '''
    try:
        # แยก hostname และ port จาก URL
        parsed_url = urlparse(target_url)
        hostname = parsed_url.hostname
        port = parsed_url.port

        # ถ้าไม่มี port ใน URL ให้กำหนดค่า default ตาม scheme
        if port is None:
            if parsed_url.scheme == "https":
                port = 443
            else:
                port = 80

        # สร้าง socket และเชื่อมต่อ
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # กำหนด timeout
        sock.connect((hostname, port))
        sock.close()  # ปิด socket หลังจากเชื่อมต่อสำเร็จ
        return True
    except (socket.timeout, socket.error):
        return False

def is_internal_url(url):
    ''' is intranet host '''
    hostname = urlparse(url).hostname
    try:
        addr_info = socket.getaddrinfo(hostname, None)  # Resolves both IPv4 and IPv6
        for addr in addr_info:
            ip = ip_address(addr[4][0])
            if any(ip in network for network in INTERNAL_IP_RANGES):
                return True
        return False  # If none of the IPs are in the internal ranges
    except socket.gaierror:
        # Handle case where the hostname cannot be resolved by treating it as internal
        return True
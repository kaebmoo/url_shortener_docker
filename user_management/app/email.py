import os
import smtplib
import ssl
import logging
import traceback
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr

from flask import render_template, current_app
from app import create_app

# ตั้งค่า logger สำหรับไฟล์นี้โดยเฉพาะ
logger = logging.getLogger(__name__)

def send_email_via_smtp(recipient, subject, text_content, html_content, sender_name, sender_address):
    """ส่งอีเมลผ่าน SMTP (วิธีเดิม)"""
    try:
        smtp_server = current_app.config.get('MAIL_SERVER')
        smtp_port = int(current_app.config.get('MAIL_PORT', 465))
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')
        subject_prefix = current_app.config.get('EMAIL_SUBJECT_PREFIX', '')
        
        if not smtp_server or not mail_username or not mail_password:
            logger.error("SMTP is not configured properly.")
            return False
        
        message = MIMEMultipart('alternative')
        full_subject = f"{subject_prefix} {subject}".strip()
        message["Subject"] = str(Header(full_subject, 'utf-8'))
        message["From"] = formataddr((sender_name, sender_address))
        message["To"] = recipient
        
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')
        message.attach(part1)
        message.attach(part2)
        
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(mail_username, mail_password)
            server.send_message(message)
        
        logger.info(f"✅ Email sent via SMTP to: {recipient}")
        return True
        
    except Exception as e:
        logger.error(f"❌ SMTP error: {str(e)}")
        return False


def send_email_via_mailgun(recipient, subject, text_content, html_content, sender_name, sender_address):
    """ส่งอีเมลผ่าน Mailgun API"""
    try:
        mailgun_api_key = current_app.config.get('MAILGUN_API_KEY')
        mailgun_domain = current_app.config.get('MAILGUN_DOMAIN')
        mailgun_api_url = current_app.config.get('MAILGUN_API_URL', 'https://api.mailgun.net/v3')
        subject_prefix = current_app.config.get('EMAIL_SUBJECT_PREFIX', '')
        
        if not mailgun_api_key or not mailgun_domain:
            logger.error("Mailgun is not configured properly.")
            return False
        
        full_subject = f"{subject_prefix} {subject}".strip()
        from_email = formataddr((sender_name, sender_address))
        
        url = f"{mailgun_api_url}/{mailgun_domain}/messages"
        
        response = requests.post(
            url,
            auth=("api", mailgun_api_key),
            data={
                "from": from_email,
                "to": recipient,
                "subject": full_subject,
                "text": text_content,
                "html": html_content
            }
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Email sent via Mailgun to: {recipient}")
            return True
        else:
            logger.error(f"❌ Mailgun API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Mailgun error: {str(e)}")
        return False


def send_email(recipient, subject, template, **kwargs):
    """
    ส่งอีเมลโดยเลือก provider ตาม config
    Interface เดิมไม่เปลี่ยนแปลง
    """
    # สร้าง app context เพื่อให้ render_template และ current_app.config ใช้งานได้
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    
    with app.app_context():
        try:
            # 1. ตรวจสอบ Config พื้นฐาน
            sender_name = current_app.config.get('MAIL_FROM_NAME') or \
                         current_app.config.get('APP_NAME', 'App Admin')
            
            sender_address = current_app.config.get('MAIL_FROM') or \
                           current_app.config.get('MAIL_USERNAME')
            
            if not sender_address:
                logger.error("Email send failed: 'MAIL_FROM' or 'MAIL_USERNAME' must be set.")
                return False
            
            # 2. สร้างเนื้อหาอีเมล
            text_content = render_template(template + '.txt', **kwargs)
            html_content = render_template(template + '.html', **kwargs)
            
            # 3. เลือก provider ตาม config
            provider = current_app.config.get('MAIL_PROVIDER', 'smtp').lower()
            
            if provider == 'mailgun':
                return send_email_via_mailgun(
                    recipient, subject, text_content, html_content, 
                    sender_name, sender_address
                )
            else:  # default เป็น smtp
                return send_email_via_smtp(
                    recipient, subject, text_content, html_content,
                    sender_name, sender_address
                )
                
        except Exception as e:
            logger.error(f"❌ Failed to send email to {recipient}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
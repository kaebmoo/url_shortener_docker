import os
import smtplib
import ssl
import logging
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr

from flask import render_template, current_app
from app import create_app

# ตั้งค่า logger สำหรับไฟล์นี้โดยเฉพาะ
logger = logging.getLogger(__name__)

def send_email(recipient, subject, template, **kwargs):
    """
    ส่งอีเมลโดยใช้ smtplib.SMTP_SSL (จาก logic ที่ใช้ได้ผล)
    แต่ยังคง interface เดิมที่รับ template และ kwargs
    และยังคงสร้าง app_context เพื่อให้ทำงานใน Queue ได้
    """
    
    # สร้าง app context เพื่อให้ render_template และ current_app.config ใช้งานได้
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    
    with app.app_context():
        try:
            # 1. ดึงค่า Config จาก app.config
            smtp_server = current_app.config.get('MAIL_SERVER')
            smtp_port = int(current_app.config.get('MAIL_PORT', 465))
            mail_username = current_app.config.get('MAIL_USERNAME')
            mail_password = current_app.config.get('MAIL_PASSWORD')
            subject_prefix = current_app.config.get('EMAIL_SUBJECT_PREFIX', '')
            
            # --- START: ส่วนที่แก้ไข ---
            
            # 2. ดึงค่าผู้ส่ง พร้อม Fallback ที่ปลอดภัย
            
            # Fallback for sender_name: MAIL_FROM_NAME -> APP_NAME -> 'App Admin'
            sender_name = current_app.config.get('MAIL_FROM_NAME')
            if not sender_name:
                sender_name = current_app.config.get('APP_NAME', 'App Admin')

            # Fallback for sender_address: MAIL_FROM -> MAIL_USERNAME
            sender_address = current_app.config.get('MAIL_FROM')
            if not sender_address:
                sender_address = mail_username # ซึ่ง mail_username อาจจะเป็น None

            # 3. [สำคัญ] ตรวจสอบค่า Config ก่อนส่ง
            if not smtp_server or not mail_username or not mail_password:
                logger.error("Email server (SMTP) is not configured. Missing MAIL_SERVER, MAIL_USERNAME, or MAIL_PASSWORD.")
                return False
                
            if not sender_address:
                logger.error("Email send failed: 'MAIL_FROM' or 'MAIL_USERNAME' must be set in config.")
                # หยุดการทำงานก่อนที่จะไป formataddr (จุดที่เกิด error)
                return False

            # --- END: ส่วนที่แก้ไข ---

            # 4. สร้างเนื้อหาอีเมล (เหมือนเดิม)
            text_content = render_template(template + '.txt', **kwargs)
            html_content = render_template(template + '.html', **kwargs)

            # 5. สร้างข้อความอีเมล (MIMEMultipart)
            message = MIMEMultipart('alternative')
            
            full_subject = f"{subject_prefix} {subject}".strip()
            message["Subject"] = str(Header(full_subject, 'utf-8'))
            
            # ณ จุดนี้ sender_address จะไม่เป็น None แล้ว
            message["From"] = formataddr((sender_name, sender_address))
            
            recipient_name = None
            if 'user' in kwargs and hasattr(kwargs['user'], 'name'):
                recipient_name = kwargs['user'].name
            elif 'user' in kwargs and hasattr(kwargs['user'], 'username'):
                recipient_name = kwargs['user'].username
            
            message["To"] = formataddr((recipient_name or recipient, recipient))

            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            
            message.attach(part1)
            message.attach(part2)

            # 6. ส่งอีเมล (เหมือนเดิม)
            context = ssl.create_default_context()
            
            with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
                server.login(mail_username, mail_password)
                server.send_message(message)
                
            logger.info(f"✅ Email '{subject}' sent successfully to: {recipient} via smtplib")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication failed. Check MAIL_USERNAME/MAIL_PASSWORD. Error: {str(e)}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error for {recipient}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to send email to {recipient}: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
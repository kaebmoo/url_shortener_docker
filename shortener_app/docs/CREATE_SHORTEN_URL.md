
1. **Start: POST /url**
   - เริ่มต้นการทำงานเมื่อมีการส่ง POST request มาที่ endpoint `/url` พร้อมกับข้อมูล URL ที่ต้องการทำการ shorten

2. **Normalize URL**
   - ทำการปรับรูปแบบของ URL ที่ได้รับมาให้เป็นรูปแบบที่ถูกต้อง (normalize) เช่น ลบ `trailing slash` ที่ไม่จำเป็นออก

3. **Validate URL**
   - ตรวจสอบความถูกต้องของ URL ที่ได้รับว่ามีรูปแบบที่ถูกต้องตามที่กำหนดไว้หรือไม่
   - **If Invalid**: ถ้า URL ไม่ถูกต้อง, ส่งข้อความแสดงข้อผิดพลาด "Your provided URL is not valid" และยุติการทำงาน

4. **Check if URL is in Blacklist**
   - ตรวจสอบว่า URL นั้นถูกบันทึกอยู่ใน blacklist หรือไม่
   - **If in Blacklist**: ถ้า URL อยู่ใน blacklist, ส่งข้อความแสดงข้อผิดพลาด "The provided URL is blacklisted and cannot be shortened." และยุติการทำงาน

5. **Check for Phishing**
   - เรียกใช้บริการภายนอกเพื่อตรวจสอบว่า URL ที่ได้รับมาเป็น phishing site หรือไม่
   - **If Phishing Detected**: ถ้าพบว่า URL นั้นเป็น phishing site, ส่งข้อความแสดงข้อผิดพลาด "The provided URL is flagged as phishing and cannot be shortened." และยุติการทำงาน

6. **Check API Key and Role**
   - ตรวจสอบ API key ที่ได้รับมาและดึงข้อมูล role ของผู้ใช้งานจากฐานข้อมูล
   - **If Invalid API Key**: ถ้า API key ไม่ถูกต้อง, ส่งข้อความแสดงข้อผิดพลาด "Invalid API key" และยุติการทำงาน

7. **Handle Custom Key**
   - ถ้ามีการกำหนด custom key สำหรับ URL นั้น, ตรวจสอบความถูกต้องของ custom key (เช่น ความยาว, รูปแบบ) และตรวจสอบว่ามี key นี้อยู่ในระบบหรือไม่
   - **If Custom Key Invalid or Already Used**: ถ้า custom key ไม่ถูกต้อง หรือถูกใช้ไปแล้ว, ส่งข้อความแสดงข้อผิดพลาดและยุติการทำงาน

8. **Check if URL Exists for API Key**
   - ตรวจสอบว่ามีการสร้าง short URL สำหรับ URL นี้อยู่แล้วหรือไม่สำหรับ API key ที่ให้มา
   - **If URL Already Exists**: ถ้ามี short URL อยู่แล้ว, ส่งข้อมูลของ short URL นั้นกลับไปที่ผู้ใช้

9. **Create DB URL Entry**
   - ถ้า URL ยังไม่มีในฐานข้อมูล, ทำการสร้าง record ใหม่ในฐานข้อมูลสำหรับ URL นั้นพร้อมกับ API key ที่ใช้

10. **Add Background Task for Page Info**
    - เพิ่ม task ใน background เพื่อดึงข้อมูลเพิ่มเติมเกี่ยวกับ URL เช่น title และ favicon

11. **Return Admin Info**
    - ส่งข้อมูล admin URL และข้อมูลอื่น ๆ ที่เกี่ยวข้องกลับไปที่ผู้ใช้


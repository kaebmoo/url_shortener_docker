
1. **Start: Load Environment Variables**
   - เริ่มต้นด้วยการโหลดค่า environment variables จากไฟล์ `config.env` เพื่อกำหนดค่าต่างๆ เช่น `INTERVAL_HOURS`, `DATABASE_PATH`, และ API keys

2. **Load Environment Variables**
   - โหลดและกำหนดค่าจาก environment variables ที่จำเป็นต่อการทำงานของโปรแกรม เช่น เวลาระหว่างการตรวจสอบ (interval), เส้นทางฐานข้อมูล, และ URLs สำหรับบริการภายนอก

3. **Setup Database and Create Trigger**
   - ตั้งค่าฐานข้อมูล SQLite และสร้าง trigger ในตาราง `urls` เพื่อเพิ่ม URL ใหม่ที่ถูกเพิ่มเข้ามาในฐานข้อมูลไปยังคิวการตรวจสอบ (urls_to_check)

4. **Get URLs from Database**
   - ดึง URL ที่ยังไม่ถูกตรวจสอบจากฐานข้อมูลโดยอ่านข้อมูลจากตาราง `urls_to_check` หรือ `urls` ที่มีการกำหนดค่าให้ตรวจสอบ

5. **Run Asynchronous URL Checks**
   - เรียกใช้การตรวจสอบ URL โดยทำงานแบบ asynchronous เพื่อตรวจสอบความปลอดภัยของแต่ละ URL ที่ได้จากฐานข้อมูล

6. **Google Web Risk**
   - ตรวจสอบ URL กับบริการ Google Web Risk เพื่อตรวจหาภัยคุกคามต่าง ๆ เช่น malware หรือ social engineering

7. **VirusTotal Check**
   - ตรวจสอบ URL กับบริการ VirusTotal เพื่อประเมินความปลอดภัยและดึงข้อมูลการวิเคราะห์ที่เกี่ยวข้อง

8. **PhishTank Check**
   - ตรวจสอบ URL กับฐานข้อมูล PhishTank เพื่อดูว่า URL นั้นเป็น phishing site หรือไม่

9. **URLHaus Check**
   - ตรวจสอบ URL กับฐานข้อมูล URLHaus เพื่อดูว่า URL นั้นเป็นแหล่งที่มีความเสี่ยงจาก malware หรือภัยคุกคามอื่น ๆ

10. **Update Database with Scan Results**
    - อัปเดตฐานข้อมูลด้วยผลลัพธ์การตรวจสอบ URL ที่ได้จากแต่ละบริการ โดยจะบันทึกสถานะของ URL เช่น `DANGER`, `SAFE`, หรือ `INCONCLUSIVE`

11. **Run Periodic URL Checks**
    - เริ่มต้นกระบวนการตรวจสอบ URL ใหม่จากคิวทุกครั้งตามเวลาที่กำหนด (interval) เพื่อตรวจสอบ URL ใหม่ที่ถูกเพิ่มเข้ามาในฐานข้อมูลอย่างต่อเนื่อง


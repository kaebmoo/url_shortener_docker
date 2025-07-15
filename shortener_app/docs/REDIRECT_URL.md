
1. **เริ่มต้น (Start)**: 
   - รับ HTTP GET request ที่เส้นทาง `/{url_key}`

2. **ดึง URL จากฐานข้อมูล**:
   - ใช้ `crud.get_db_url_by_key(db=db, url_key=url_key)` เพื่อดึง `db_url`

3. **ตรวจสอบว่า URL มีอยู่หรือไม่**:
   - **ถ้า `db_url` มีอยู่**: ดำเนินการต่อไปยังขั้นตอนถัดไป
   - **ถ้า `db_url` ไม่มีอยู่**: เรียก `raise_not_found(request)`

4. **ตรวจสอบสถานะของ URL**:
   - **ถ้า `db_url.status` คือ "danger"**: 
     - เรียกใช้ `call_preview_url_async(db_url.target_url, SECRET_TOKEN)`
     - ส่งคืน HTML preview ที่สร้างขึ้น
   - **ถ้า `db_url.status` ไม่ใช่ "danger"**: ดำเนินการต่อไปยังขั้นตอนถัดไป

5. **ตรวจสอบว่า URL เป็น Internal หรือไม่**:
   - ใช้ `is_internal_url(db_url.target_url)` เพื่อตรวจสอบ
   - **ถ้า URL เป็น Internal**:
     - อัปเดตจำนวนการคลิกด้วย `crud.update_db_clicks(db=db, db_url=db_url)`
     - Redirect ไปที่ `db_url.target_url`
   - **ถ้า URL ไม่ใช่ Internal**: ดำเนินการต่อไปยังขั้นตอนถัดไป

6. **ข้ามการตรวจสอบการเข้าถึง (Reachability Check)**:
   - อัปเดตจำนวนการคลิกด้วย `crud.update_db_clicks(db=db, db_url=db_url)`
   - Redirect ไปที่ `db_url.target_url`

7. **สิ้นสุด (End)**.



**ทำตามขั้นตอนต่อไปนี้:**

1.  **Build Image ใหม่:** สั่งให้ Docker สร้าง Image ใหม่

    ```bash
    docker-compose up --build -d
    ```
2.  **รันคำสั่ง `setup_prod`:** หลังจากที่ Container ทั้งหมดทำงานแล้ว (ขึ้นสถานะ `running` หรือ `healthy`) ให้รันคำสั่งนี้ใน Terminal:

    ```bash
    docker-compose exec user_management flask setup_prod
    ```

คำสั่งนี้จะเข้าไปใน Container `user_management_app` แล้วรัน `flask setup_prod` ซึ่งจะเรียกใช้ฟังก์ชัน `setup_general()` ที่คุณมีอยู่ ผลลัพธ์คือ:

  * ตาราง `roles` จะถูกสร้างข้อมูลทั้ง 3 roles (User, VIP, Administrator)
  * Admin user เริ่มต้นจะถูกสร้างขึ้นและผูกกับ Role 'Administrator'
 
`docker-compose exec user_management python -c 'from manage import setup_prod; setup_prod()'`

แต่การสร้างแบบนี้จะไม่มีการสร้าง API Key ในฝั่งของ URL API Service ให้ใช้การเรียก `seed()` แทน

สร้าง admin user และ roles
`docker-compose exec user_management flask seed`
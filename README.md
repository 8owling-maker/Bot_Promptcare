# SLA Bot — PTT Digital Ticket → MS Teams

แจ้งเตือน Ticket ที่ **Tar Date ≤ 1 วัน** ไปยัง MS Teams Channel ทุกวันทำงาน เวลา 09:00 น.

---

## โครงสร้างไฟล์

```
sla-bot/
├── main.py           # Entry point
├── scraper.py        # Login + Web Scraping
├── teams_notify.py   # ส่ง Adaptive Card ไป Teams
├── config.py         # ⚙️ ตั้งค่าทั้งหมดที่นี่
├── requirements.txt
└── sla_bot.log       # Log file (สร้างอัตโนมัติ)
```

---

## ขั้นตอนติดตั้ง

### 1. ติดตั้ง Python 3.9+
ดาวน์โหลดที่ https://www.python.org/downloads/

### 2. ติดตั้ง Dependencies
```bash
cd sla-bot
pip install -r requirements.txt
playwright install chromium
```

### 3. ตั้งค่าใน config.py
```python
USERNAME          = "your_username"       # Username ระบบ Ticket
PASSWORD          = "your_password"       # Password
TEAMS_WEBHOOK_URL = "https://outlook.office.com/webhook/..."   # Webhook URL
```

#### วิธีสร้าง Teams Webhook URL
1. เปิด MS Teams → ไปที่ Channel ที่ต้องการ
2. คลิก `...` → **Connectors**
3. ค้นหา **Incoming Webhook** → Configure
4. ตั้งชื่อ เช่น "SLA Bot" → Copy URL มาใส่ใน config.py

### 4. ทดสอบรันครั้งแรก
```bash
python main.py --run-now
```

---

## ตั้งค่า Windows Task Scheduler (รันอัตโนมัติทุกวัน 09:00)

1. เปิด **Task Scheduler** (พิมพ์ใน Start Menu)
2. **Create Basic Task**
   - Name: `SLA Bot`
   - Trigger: **Daily** → เวลา 09:00
3. Action: **Start a program**
   - Program: `C:\Python39\python.exe` (หรือ path ที่ติดตั้ง)
   - Arguments: `C:\sla-bot\main.py`
   - Start in: `C:\sla-bot`
4. ✅ Finish

> **หมายเหตุ:** เครื่องที่รัน Bot ต้องเปิดอยู่ในเวลา 09:00 น.

---

## ตัวอย่างข้อความใน Teams

```
⚠️ แจ้งเตือน Ticket ใกล้/เกิน SLA
วันที่ 08/06/2026 | พบ 3 รายการ

┌─────────────────────────────────────┐
│ TK-00123 — ปัญหาระบบ e-Auction       │
│ สถานะ   : In Progress               │
│ Priority: High                      │
│ Assignee: สมชาย ใจดี               │
│ Tar Date: 09/06/2026                │
│ เวลาคงเหลือ: 🟠 เหลือ 1 วัน        │
└─────────────────────────────────────┘
```

---

## การปรับแต่งเพิ่มเติม

| ต้องการ | แก้ไขที่ |
|---|---|
| เปลี่ยนจำนวนวันแจ้งเตือน | `ALERT_DAYS_BEFORE` ใน config.py |
| เปลี่ยนเวลารัน | `RUN_TIME` ใน config.py |
| รันทุกวัน (รวมเสาร์-อาทิตย์) | `WORKDAYS_ONLY = False` |
| ดู Browser ขณะรัน (Debug) | `HEADLESS = False` |
| ปรับ Search Criteria | `SEARCH_PARAMS` ใน config.py |

---

## แก้ปัญหาที่พบบ่อย

**Login ไม่ผ่าน**
→ เปิด `HEADLESS = False` แล้วดูว่า element ชื่ออะไร แก้ selector ใน `scraper.py` ฟังก์ชัน `login()`

**ไม่พบ Column Tar Date**
→ ดู Header ที่ print ใน log แล้วเพิ่ม keyword ใน `find_col(["tar date", ...])` ใน `scraper.py`

**Teams ไม่รับข้อความ**
→ ตรวจสอบ Webhook URL ใน config.py และสิทธิ์ Connector ใน Teams Channel

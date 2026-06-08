# ============================================================
#  Dockerfile — สำหรับ deploy บน Railway
#  ใช้ image ที่มี Chromium พร้อมใช้งาน
# ============================================================

FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# ติดตั้ง dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Railway จะ set PORT อัตโนมัติ แต่ Bot นี้ไม่ต้องการ HTTP server
# รัน Bot เลย
CMD ["python", "main.py", "--schedule"]

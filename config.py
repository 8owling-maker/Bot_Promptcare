# ============================================================
#  config.py — อ่านค่าจาก Environment Variables (Railway)
#  หรือใส่ค่าตรงนี้สำหรับรันบนเครื่อง Local
# ============================================================

import os

# --- Ticket System ---
TICKET_URL = os.getenv("TICKET_URL", "https://promptcare.pttdigital.com/TicketSearch/Index")
LOGIN_URL  = os.getenv("LOGIN_URL",  "https://promptcare.pttdigital.com/Account/Login")
USERNAME   = os.getenv("TICKET_USERNAME", "your_username")   # ← ตั้งใน Railway Variables
PASSWORD   = os.getenv("TICKET_PASSWORD", "your_password")   # ← ตั้งใน Railway Variables

# --- Search Criteria ---
SEARCH_PARAMS = {
    "SearchType"     : "Ticket",
    "BusinessService": "Client Service",
    "CategoryTier1"  : "Application",
    "CategoryTier2"  : "PTT - Smart Procurement (SP)",
    "AssignmentGroup": "AOU/F - PTT - Smart Procurement",
}

# --- SLA Alert ---
ALERT_DAYS_BEFORE = int(os.getenv("ALERT_DAYS_BEFORE", "1"))

# --- MS Teams Webhook ---
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL", "https://outlook.office.com/webhook/XXX")  # ← ตั้งใน Railway Variables

# --- Schedule ---
RUN_TIME      = os.getenv("RUN_TIME", "09:00")   # Bangkok = UTC+7 → ต้องตั้ง TZ ด้วย
WORKDAYS_ONLY = os.getenv("WORKDAYS_ONLY", "true").lower() == "true"

# --- Browser (Railway ต้องใช้ headless=True เสมอ) ---
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

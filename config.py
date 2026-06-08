# ============================================================
#  config.py — อ่านค่าจาก Environment Variables (Railway)
#  หรือใส่ค่าตรงนี้สำหรับรันบนเครื่อง Local
# ============================================================

import os

# --- Ticket System ---
TICKET_URL = os.getenv("TICKET_URL", "https://promptcare.pttdigital.com/TicketSearch/Index")
LOGIN_URL  = os.getenv("LOGIN_URL",  "https://promptcare.pttdigital.com/")
USERNAME   = os.getenv("TICKET_USERNAME", "your_username")   # ← ตั้งใน Railway Variables
PASSWORD   = os.getenv("TICKET_PASSWORD", "your_password")   # ← ตั้งใน Railway Variables

# --- Search Criteria (หลายระบบ) ---
SYSTEMS = [
    {
        "name"           : "PTT Smart Procurement",
        "BusinessService": "Client Service",
        "CategoryTier1"  : "Application",
        "CategoryTier2"  : "PTT - Smart Procurement (SP)",
        "AssignmentGroup": "AOU/F - PTT - Smart Procurement",
    },
    {
        "name"           : "PTTTANK PR/PO Online",
        "BusinessService": "Client Service",
        "CategoryTier1"  : "Application",
        "CategoryTier2"  : "PTTTANK - PR PO Online",
        "AssignmentGroup": "AOU/F – PTTTANK – PR PO Online",
    },
    {
        "name"           : "PTT e-Tax Vendor",
        "BusinessService": "Client Service",
        "CategoryTier1"  : "Application",
        "CategoryTier2"  : "PTT - E-Tax Vendor",
        "AssignmentGroup": "AOU/F – PTT – E-Tax Vendor",
    },
    {
        "name"           : "PTT PPA",
        "BusinessService": "Client Service",
        "CategoryTier1"  : "Application",
        "CategoryTier2"  : "PTT - Procurement Policy Advisory System (PPA)",
        "AssignmentGroup": "AOU/F – PTT– Procurement Policy Advisory System (PPA)",
    },
]

# --- SLA Alert ---
ALERT_DAYS_BEFORE = int(os.getenv("ALERT_DAYS_BEFORE", "1"))

# --- Email (Resend) ---
RESEND_API_KEY   = os.getenv("RESEND_API_KEY",   "")
EMAIL_SENDER     = os.getenv("EMAIL_SENDER",     "onboarding@resend.dev")
EMAIL_RECIPIENTS = os.getenv("EMAIL_RECIPIENTS", "zphanumas.c@pttdigital.com").split(",")

# --- Schedule ---
RUN_TIME      = os.getenv("RUN_TIME", "09:00")   # Bangkok = UTC+7 → ต้องตั้ง TZ ด้วย
WORKDAYS_ONLY = os.getenv("WORKDAYS_ONLY", "true").lower() == "true"

# --- Browser (Railway ต้องใช้ headless=True เสมอ) ---
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

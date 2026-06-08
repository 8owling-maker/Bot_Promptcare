# ============================================================
#  main.py — Entry Point
#  รันตรง : python main.py --run-now
#  Schedule: python main.py --schedule  (Railway ใช้แบบนี้)
# ============================================================

import argparse
import logging
import sys
import json
import requests
from datetime import datetime
import pytz

import schedule
import time

from config import RUN_TIME, WORKDAYS_ONLY, TEAMS_WEBHOOK_URL
from scraper import get_sla_tickets
from teams_notify import send_teams_message

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],  # Railway ดู log จาก stdout
)
logger = logging.getLogger(__name__)

# Timezone กรุงเทพ
BKK_TZ = pytz.timezone("Asia/Bangkok")


def run_job():
    """งานหลัก: ดึง Ticket → แจ้ง Teams"""
    now_bkk = datetime.now(BKK_TZ)

    # ข้ามวันหยุดสุดสัปดาห์ (weekday: 0=จันทร์, 5=เสาร์, 6=อาทิตย์)
    if WORKDAYS_ONLY and now_bkk.weekday() >= 5:
        logger.info(f"วันนี้ ({now_bkk.strftime('%A')}) — ข้ามวันหยุดสุดสัปดาห์")
        return

    logger.info("=" * 55)
    logger.info(f"🤖 SLA Bot เริ่มทำงาน — {now_bkk.strftime('%d/%m/%Y %H:%M')} (Bangkok)")
    logger.info("=" * 55)

    try:
        tickets = get_sla_tickets()
        send_teams_message(tickets)
        logger.info(f"✅ จบงาน — พบ Ticket แจ้งเตือน {len(tickets)} รายการ")
    except Exception as e:
        logger.exception(f"❌ เกิดข้อผิดพลาด: {e}")
        _notify_error(str(e))


def _notify_error(error_msg: str):
    """แจ้ง Teams เมื่อ Bot มีปัญหา"""
    try:
        payload = {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [{
                        "type": "TextBlock",
                        "text": f"❌ SLA Bot Error: {error_msg[:300]}",
                        "color": "attention",
                        "wrap": True
                    }]
                }
            }]
        }
        requests.post(TEAMS_WEBHOOK_URL,
                      headers={"Content-Type": "application/json"},
                      data=json.dumps(payload), timeout=10)
    except Exception:
        pass


def schedule_job():
    """
    ตั้ง Schedule โดยแปลงเวลา Bangkok → UTC
    Railway server รันที่ UTC ดังนั้นต้องลบ 7 ชั่วโมง
    """
    import datetime as dt

    # แปลง RUN_TIME (Bangkok) เป็น UTC
    run_h, run_m = map(int, RUN_TIME.split(":"))
    bkk_time = BKK_TZ.localize(
        dt.datetime.now().replace(hour=run_h, minute=run_m, second=0)
    )
    utc_time = bkk_time.astimezone(pytz.utc)
    utc_str  = utc_time.strftime("%H:%M")

    logger.info(f"📅 Schedule: {RUN_TIME} Bangkok = {utc_str} UTC")
    schedule.every().day.at(utc_str).do(run_job)

    logger.info("⏳ กำลังรอ Schedule... (Ctrl+C เพื่อหยุด)")
    while True:
        schedule.run_pending()
        time.sleep(30)


def main():
    parser = argparse.ArgumentParser(description="SLA Bot — PTT Ticket → MS Teams")
    parser.add_argument("--schedule",  action="store_true", help="รันแบบ Schedule (Railway)")
    parser.add_argument("--run-now",   action="store_true", help="รันทันที (Test)")
    args = parser.parse_args()

    if args.schedule:
        schedule_job()
    else:
        # default = run-now (รวมถึงกรณีไม่ระบุ argument)
        run_job()


if __name__ == "__main__":
    main()

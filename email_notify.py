# ============================================================
#  email_notify.py — ส่งแจ้งเตือน SLA ทาง Gmail
# ============================================================

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
from config import (
    EMAIL_SENDER, EMAIL_APP_PASSWORD,
    EMAIL_RECIPIENTS, ALERT_DAYS_BEFORE
)

logger = logging.getLogger(__name__)


def _days_badge(days_left: int) -> str:
    if days_left < 0:
        return f"🔴 เกิน SLA ไปแล้ว {abs(days_left)} วัน"
    if days_left == 0:
        return "🔴 ครบกำหนดวันนี้!"
    if days_left == 1:
        return "🟠 เหลือ 1 วัน (พรุ่งนี้)"
    return f"🟡 เหลือ {days_left} วัน"


def _row_color(days_left: int) -> str:
    if days_left <= 0:
        return "#ffe5e5"
    if days_left == 1:
        return "#fff4e5"
    return "#fffff0"


def build_html(tickets: list) -> str:
    today_str = date.today().strftime("%d/%m/%Y")

    if not tickets:
        return f"""
        <html><body style="font-family:sans-serif;padding:20px">
        <h2 style="color:#2e7d32">✅ ไม่มี Ticket ใกล้/เกิน SLA</h2>
        <p>📅 วันที่ {today_str}</p>
        <p>ไม่พบ Ticket ที่ Target Date เหลือ ≤ {ALERT_DAYS_BEFORE} วัน</p>
        </body></html>
        """

    rows = ""
    for t in tickets:
        days_left = t.get("days_left", 0)
        bg = _row_color(days_left)
        rows += f"""
        <tr style="background:{bg}">
            <td style="{td}"><b>{t.get('ticket_id','-')}</b></td>
            <td style="{td}">{t.get('subject','-')}</td>
            <td style="{td}">{t.get('status','-')}</td>
            <td style="{td}">{t.get('priority','-')}</td>
            <td style="{td}">{t.get('assignee','-')}</td>
            <td style="{td}">{t.get('target_date','-')}</td>
            <td style="{td}">{_days_badge(days_left)}</td>
        </tr>
        """

    return f"""
    <html><body style="font-family:sans-serif;padding:20px">
    <h2 style="color:#c62828">⚠️ แจ้งเตือน Ticket ใกล้/เกิน SLA</h2>
    <p>📅 วันที่ {today_str} &nbsp;|&nbsp; 📋 พบ <b>{len(tickets)}</b> รายการ
       &nbsp;|&nbsp; ⏱ Target Date เหลือ ≤ {ALERT_DAYS_BEFORE} วัน</p>
    <table border="1" cellspacing="0" cellpadding="6"
           style="border-collapse:collapse;width:100%;font-size:13px">
        <thead style="background:#1565c0;color:white">
            <tr>
                <th style="{th}">Ticket ID</th>
                <th style="{th}">Subject</th>
                <th style="{th}">Status</th>
                <th style="{th}">Priority</th>
                <th style="{th}">Assignee</th>
                <th style="{th}">Target Date</th>
                <th style="{th}">เวลาคงเหลือ</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    <br>
    <a href="https://promptcare.pttdigital.com/TicketSearch/Index"
       style="background:#1565c0;color:white;padding:8px 16px;
              text-decoration:none;border-radius:4px">
       🔗 เปิดระบบ Ticket
    </a>
    </body></html>
    """


th = "padding:8px;text-align:left"
td = "padding:6px;border:1px solid #ccc"


def send_email(tickets: list):
    today_str = date.today().strftime("%d/%m/%Y")
    subject = (
        f"✅ ไม่มี Ticket ใกล้ SLA — {today_str}"
        if not tickets
        else f"⚠️ แจ้งเตือน SLA {len(tickets)} รายการ — {today_str}"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(EMAIL_RECIPIENTS)
    msg.attach(MIMEText(build_html(tickets), "html", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENTS, msg.as_bytes())

    logger.info(f"✅ ส่ง Email สำเร็จ ({len(tickets)} รายการ) → {EMAIL_RECIPIENTS}")

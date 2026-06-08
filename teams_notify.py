# ============================================================
#  teams_notify.py — ส่ง Adaptive Card ไป MS Teams Webhook
#  Fields: ticket_id, subject, assignment_group, assignee,
#          type, priority, status, target_date, days_left
# ============================================================

import json
import logging
import requests
from datetime import date
from config import TEAMS_WEBHOOK_URL, ALERT_DAYS_BEFORE

logger = logging.getLogger(__name__)


def _card_style(days_left: int) -> str:
    """สีกรอบ Card ตามความเร่งด่วน"""
    if days_left < 0:
        return "attention"   # แดง — เกิน SLA แล้ว
    if days_left == 0:
        return "attention"   # แดง — วันนี้วันสุดท้าย
    if days_left == 1:
        return "warning"     # เหลือง — พรุ่งนี้ครบกำหนด
    return "default"


def _days_badge(days_left: int) -> str:
    if days_left < 0:
        return f"🔴 เกิน SLA ไปแล้ว {abs(days_left)} วัน"
    if days_left == 0:
        return "🔴 ครบกำหนดวันนี้!"
    if days_left == 1:
        return "🟠 เหลือ 1 วัน (พรุ่งนี้)"
    return f"🟡 เหลือ {days_left} วัน"


def build_adaptive_card(tickets: list) -> dict:
    today_str = date.today().strftime("%d/%m/%Y")

    body = [
        {
            "type": "TextBlock",
            "text": "⚠️ แจ้งเตือน Ticket ใกล้/เกิน SLA",
            "size": "Large",
            "weight": "Bolder",
            "wrap": True
        },
        {
            "type": "TextBlock",
            "text": (
                f"📅 วันที่ {today_str}   |   "
                f"📋 พบ **{len(tickets)}** รายการ   |   "
                f"⏱ Target Date เหลือ ≤ {ALERT_DAYS_BEFORE} วัน"
            ),
            "isSubtle": True,
            "wrap": True,
            "spacing": "None"
        },
        {"type": "Separator", "spacing": "Medium"}
    ]

    for t in tickets:
        days_left  = t.get("days_left", 0)
        style      = _card_style(days_left)
        days_badge = _days_badge(days_left)

        body.append({
            "type": "Container",
            "style": style,
            "spacing": "Small",
            "items": [
                {
                    "type": "ColumnSet",
                    "columns": [
                        {
                            "type": "Column",
                            "width": "stretch",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": f"🎫 **{t.get('ticket_id','-')}**  —  {t.get('subject','-')}",
                                    "weight": "Bolder",
                                    "wrap": True,
                                    "size": "Medium"
                                },
                                {
                                    "type": "FactSet",
                                    "spacing": "Small",
                                    "facts": [
                                        {
                                            "title": "📌 Status",
                                            "value": t.get("status", "-")
                                        },
                                        {
                                            "title": "🏷️ Type",
                                            "value": t.get("type", "-")
                                        },
                                        {
                                            "title": "⚡ Priority",
                                            "value": t.get("priority", "-")
                                        },
                                        {
                                            "title": "👤 Assignee",
                                            "value": t.get("assignee", "-")
                                        },
                                        {
                                            "title": "👥 Group",
                                            "value": t.get("assignment_group", "-")
                                        },
                                        {
                                            "title": "📅 Target Date",
                                            "value": t.get("target_date", "-")
                                        },
                                        {
                                            "title": "⏳ เวลาคงเหลือ",
                                            "value": days_badge
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        })

    # Footer
    body.append({
        "type": "ActionSet",
        "spacing": "Medium",
        "actions": [
            {
                "type": "Action.OpenUrl",
                "title": "🔗 เปิดระบบ Ticket",
                "url": "https://promptcare.pttdigital.com/TicketSearch/Index"
            }
        ]
    })

    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": body
                }
            }
        ]
    }


def build_no_alert_card() -> dict:
    """Card สำหรับกรณีไม่มี Ticket ใกล้ SLA"""
    today_str = date.today().strftime("%d/%m/%Y")
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": f"✅ ไม่มี Ticket ใกล้/เกิน SLA — {today_str}",
                            "size": "Medium",
                            "weight": "Bolder",
                            "color": "good"
                        },
                        {
                            "type": "TextBlock",
                            "text": f"ไม่พบ Ticket ที่ Target Date เหลือ ≤ {ALERT_DAYS_BEFORE} วัน",
                            "isSubtle": True
                        }
                    ]
                }
            }
        ]
    }


def send_teams_message(tickets: list):
    """ส่ง Adaptive Card ไป Teams Webhook"""
    payload = build_adaptive_card(tickets) if tickets else build_no_alert_card()

    resp = requests.post(
        TEAMS_WEBHOOK_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=15
    )

    if resp.status_code == 200:
        logger.info(f"✅ ส่ง Teams สำเร็จ ({len(tickets)} รายการ)")
    else:
        logger.error(f"❌ Teams ตอบ {resp.status_code}: {resp.text}")
        resp.raise_for_status()

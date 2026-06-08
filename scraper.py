# ============================================================
#  scraper.py — Login + ดึงข้อมูล Ticket เกิน/ใกล้ SLA
#  ปรับให้ตรงกับ Table จริง:
#    TICKET ID | SUBJECT | ASSIGNMENT GROUP | ASSIGNEE |
#    TYPE | PRIORITY | STATUS | TARGET DATE
#  TARGET DATE format: "22 Jun 2026 09:58"
#  มีปุ่ม "Load more" สำหรับโหลดข้อมูลเพิ่ม
# ============================================================

import logging
from datetime import date, datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from config import (
    LOGIN_URL, TICKET_URL, USERNAME, PASSWORD,
    SEARCH_PARAMS, ALERT_DAYS_BEFORE, HEADLESS
)

logger = logging.getLogger(__name__)

# ชื่อ Column จากหน้าจอจริง (ตัวพิมพ์ใหญ่)
COL_TICKET_ID        = "ticket id"
COL_SUBJECT          = "subject"
COL_ASSIGNMENT_GROUP = "assignment group"
COL_ASSIGNEE         = "assignee"
COL_TYPE             = "type"
COL_PRIORITY         = "priority"
COL_STATUS           = "status"
COL_TARGET_DATE      = "target date"


# ------------------------------------------------------------
#  Login
# ------------------------------------------------------------
def login(page):
    logger.info(f"กำลัง Login ที่ {LOGIN_URL}")
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)

    page.wait_for_selector("#username", timeout=30000)
    page.fill("#username", USERNAME)
    page.fill("#password", PASSWORD)
    page.click(".form-group-submit input[type='submit'], .form-group-submit button, input[type='submit'], button[type='submit']")

    try:
        page.wait_for_url(
            lambda url: "login" not in url.lower(),
            timeout=15000
        )
        logger.info("Login สำเร็จ")
    except PWTimeout:
        if "login" in page.url.lower():
            raise RuntimeError("Login ล้มเหลว — ตรวจสอบ USERNAME/PASSWORD ใน config.py")
        logger.info("Login สำเร็จ (ไม่มี redirect)")


# ------------------------------------------------------------
#  กรอก Search Form แล้วกด Search
# ------------------------------------------------------------
def select2_select(page, select_id: str, label: str):
    """เลือกค่าใน Select2 dropdown โดยใช้ select_option บน hidden select ตรงๆ"""
    try:
        page.select_option(select_id, label=label, timeout=8000)
        # trigger change event เพื่อให้ Select2 และ page อัปเดต
        page.evaluate(f"document.querySelector('{select_id}').dispatchEvent(new Event('change', {{bubbles: true}}))")
        logger.info(f"  Set {select_id} = {label}")
        page.wait_for_timeout(1000)
    except Exception as e:
        logger.warning(f"  ข้ามฟิลด์ '{select_id}' — {e}")


def fill_search_form(page):
    logger.info("เปิดหน้า Ticket Search")
    page.goto(TICKET_URL, wait_until="networkidle")
    page.wait_for_selector("#ddlService", timeout=15000)

    select2_select(page, "#ddlService",              SEARCH_PARAMS.get("BusinessService", ""))
    page.wait_for_timeout(1500)
    select2_select(page, "#ddlServicecategoryTier1", SEARCH_PARAMS.get("CategoryTier1", ""))
    page.wait_for_timeout(1500)
    select2_select(page, "#ddlServicecategoryTier2", SEARCH_PARAMS.get("CategoryTier2", ""))
    page.wait_for_timeout(1500)
    select2_select(page, "#ddlAssignGroup",          SEARCH_PARAMS.get("AssignmentGroup", ""))
    page.wait_for_timeout(1000)

    page.click("button:has-text('Search'), input[value='Search']")
    page.wait_for_load_state("networkidle")
    logger.info("Search เสร็จแล้ว — กำลังโหลดผลลัพธ์")


# ------------------------------------------------------------
#  กด "Load more" จนครบทุกแถว
# ------------------------------------------------------------
def load_all_rows(page):
    """กด Load more ซ้ำจนปุ่มหายไป เพื่อให้ได้ทุก Ticket"""
    click_count = 0
    while True:
        try:
            btn = page.query_selector(
                "button:has-text('Load more'), "
                "a:has-text('Load more'), "
                ".load-more, [class*='loadmore']"
            )
            if not btn or not btn.is_visible():
                break
            btn.click()
            page.wait_for_load_state("networkidle")
            click_count += 1
            logger.info(f"  กด Load more ครั้งที่ {click_count}")
        except Exception as e:
            logger.debug(f"  หยุด Load more: {e}")
            break

    logger.info(f"โหลดครบแล้ว (กด Load more {click_count} ครั้ง)")


# ------------------------------------------------------------
#  Parse วันที่ — รองรับ "22 Jun 2026 09:58" และรูปแบบอื่น
# ------------------------------------------------------------
def parse_date(date_str: str):
    """คืน date object หรือ None ถ้า parse ไม่ได้"""
    if not date_str or date_str.strip() == "-":
        return None

    s = date_str.strip()
    formats = [
        "%d %b %Y %H:%M",   # 22 Jun 2026 09:58  ← รูปแบบจากหน้าจอจริง
        "%d %b %Y",          # 22 Jun 2026
        "%d/%m/%Y %H:%M",    # 22/06/2026 09:58
        "%d/%m/%Y",          # 22/06/2026
        "%Y-%m-%d %H:%M",    # 2026-06-22 09:58
        "%Y-%m-%d",          # 2026-06-22
        "%d-%m-%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


# ------------------------------------------------------------
#  อ่าน Table ผลลัพธ์ — คืนเฉพาะ Ticket ที่ใกล้/เกิน SLA
# ------------------------------------------------------------
def parse_tickets(page):
    today     = date.today()
    tickets_alert = []

    # --- อ่าน Header ---
    header_cells = page.query_selector_all("table thead th, table thead td")
    headers = [h.inner_text().strip().lower() for h in header_cells]
    logger.info(f"Header ที่พบ: {headers}")

    def col_index(name: str):
        for i, h in enumerate(headers):
            if name in h:
                return i
        return None

    # Map column index ตามชื่อจริงในหน้าจอ
    idx = {
        "ticket_id"        : col_index(COL_TICKET_ID),
        "subject"          : col_index(COL_SUBJECT),
        "assignment_group" : col_index(COL_ASSIGNMENT_GROUP),
        "assignee"         : col_index(COL_ASSIGNEE),
        "type"             : col_index(COL_TYPE),
        "priority"         : col_index(COL_PRIORITY),
        "status"           : col_index(COL_STATUS),
        "target_date"      : col_index(COL_TARGET_DATE),
    }
    logger.info(f"Column index: {idx}")

    if idx["target_date"] is None:
        logger.error("ไม่พบ Column 'TARGET DATE' — ตรวจสอบ Header ใน Table")
        return []

    # --- อ่านทุก Row ---
    rows = page.query_selector_all("#tbodyTicket tr")
    logger.info(f"พบแถวทั้งหมด {len(rows)} แถว")

    for row in rows:
        cells = row.query_selector_all("td")
        if not cells:
            continue

        def cell(key):
            i = idx.get(key)
            if i is None or i >= len(cells):
                return "-"
            # ถ้ามี <a> tag ให้ดึง text จาก <a> ก่อน (เช่น Target Date)
            a_tag = cells[i].query_selector("a")
            if a_tag:
                return a_tag.inner_text().strip() or "-"
            # ถ้าไม่มี ดึง text node ตรงๆ ไม่รวม script/popup
            text = cells[i].evaluate(
                "el => Array.from(el.childNodes)"
                ".filter(n => n.nodeType === 3)"
                ".map(n => n.textContent)"
                ".join('').trim()"
            )
            return text or cells[i].inner_text().strip() or "-"

        target_date_str = cell("target_date")
        ticket_id       = cell("ticket_id")
        subject         = cell("subject")
        assignment_grp  = cell("assignment_group")
        assignee        = cell("assignee")
        t_type          = cell("type")
        priority        = cell("priority")
        status          = cell("status")

        # --- คำนวณวันที่เหลือ ---
        target_date = parse_date(target_date_str)
        if target_date is None:
            logger.info(f"  Parse TARGET DATE ไม่ได้: '{target_date_str}' (Ticket {ticket_id})")
            continue

        days_left = (target_date - today).days
        logger.info(f"  {ticket_id} | status={status} | target={target_date_str} | days_left={days_left}")

        # กรอง status ที่สนใจเท่านั้น
        ACTIVE_STATUSES = {"new", "assigned", "work in progress"}
        if status.lower() not in ACTIVE_STATUSES:
            continue

        if days_left <= ALERT_DAYS_BEFORE:
            tickets_alert.append({
                "ticket_id"       : ticket_id,
                "subject"         : subject,
                "assignment_group": assignment_grp,
                "assignee"        : assignee,
                "type"            : t_type,
                "priority"        : priority,
                "status"          : status,
                "target_date"     : target_date_str,
                "days_left"       : days_left,
            })
            logger.info(
                f"  ⚠️  {ticket_id} | {subject[:30]} | {status} | "
                f"Target: {target_date_str} | เหลือ {days_left} วัน"
            )

    logger.info(f"พบ Ticket ใกล้/เกิน SLA ทั้งหมด {len(tickets_alert)} รายการ")
    return tickets_alert


# ------------------------------------------------------------
#  Entry Point
# ------------------------------------------------------------
def get_sla_tickets():
    """เปิด Browser → Login → Search → Load all → Parse → คืน list"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context()
        page    = context.new_page()

        try:
            login(page)
            fill_search_form(page)
            load_all_rows(page)       # ← กด Load more จนครบ
            tickets = parse_tickets(page)
        finally:
            browser.close()

    return tickets

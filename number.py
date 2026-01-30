#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NumberPanel Telegram OTP Bot
✔ Browser-exact DataTables params
✔ HTML / session expiry detection
✔ Safe JSON parsing (no crash)
✔ ENV based secrets
✔ LAST 3 OTP ONLY
"""

import os
import time
import json
import re
import requests
from datetime import datetime

# ================= CONFIG =================
API_URL = "http://51.89.99.105/NumberPanel/client/res/data_smscdr.php"

# 🔐 ENV VALUES (REQUIRED)
PHPSESSID = os.getenv("PHPSESSID")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# sesskey hardcoded (as per your working URL)
SESSKEY = "Q05RR0FPUUpCVg=="

CHAT_ID = "-1003559187782"
CHECK_INTERVAL = 12
STATE_FILE = "state.json"

# ================= HEADERS =================
HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "http://51.89.99.105/NumberPanel/client/SMSDashboard",
    "Connection": "close",
}

# ================= HELPERS =================
def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"sent": []}

def save_state(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)

def extract_otp(text):
    if not text:
        return None
    # Telegram code 54389
    m = re.search(r"Telegram\s+code\s+(\d{4,8})", text, re.I)
    if m:
        return m.group(1)
    # fallback
    m = re.search(r"\b\d{4,8}\b", text)
    return m.group(0) if m else None

def send_telegram(msg):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": msg,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            },
            timeout=10
        )
        print("📤 Telegram:", r.status_code)
    except Exception as e:
        print("⚠️ Telegram send failed:", e)

# ================= START =================
print("🚀 NumberPanel OTP Bot Started")
print("📢 Chat ID:", CHAT_ID)

state = load_state()
sent = state["sent"]

while True:
    try:
        params = {
            # Filters (browser exact)
            "fdate1": datetime.now().strftime("%Y-%m-%d 00:00:00"),
            "fdate2": datetime.now().strftime("%Y-%m-%d 23:59:59"),
            "frange": "",
            "fnum": "",
            "fcli": "",
            "fgdate": "",
            "fgmonth": "",
            "fgrange": "",
            "fgnumber": "",
            "fgcli": "",
            "fg": 0,

            # Session
            "sesskey": SESSKEY,

            # DataTables params (CRITICAL)
            "sEcho": 1,
            "iColumns": 7,
            "sColumns": ",,,,,,",
            "iDisplayStart": 0,
            "iDisplayLength": 3,

            "mDataProp_0": 0,
            "mDataProp_1": 1,
            "mDataProp_2": 2,
            "mDataProp_3": 3,
            "mDataProp_4": 4,
            "mDataProp_5": 5,
            "mDataProp_6": 6,

            "sSearch": "",
            "bRegex": "false",
            "iSortingCols": 1,
            "iSortCol_0": 0,
            "sSortDir_0": "desc",

            "_": int(time.time() * 1000),
        }

        r = requests.get(
            API_URL,
            headers=HEADERS,
            cookies={"PHPSESSID": PHPSESSID},
            params=params,
            timeout=20
        )

        # ===== HTML / EMPTY CHECK =====
        if not r.text or not r.text.strip():
            print("⚠️ Empty response")
            time.sleep(30)
            continue

        if r.text.lstrip().startswith("<"):
            print("🔐 HTML response detected (session expired)")
            print(r.text[:120])
            time.sleep(60)
            continue

        # ===== SAFE JSON PARSE =====
        try:
            data = r.json()
        except Exception:
            print("⚠️ JSON parse failed")
            print("STATUS:", r.status_code)
            print("TYPE:", r.headers.get("content-type"))
            print("BODY:", r.text[:200])
            time.sleep(30)
            continue

        rows = data.get("aaData", [])
        if not rows:
            time.sleep(CHECK_INTERVAL)
            continue

        # Oldest → newest
        rows.reverse()

        for row in rows:
            ts, pool, number, service, message = row[:5]
            key = f"{number}_{ts}"

            if key in sent:
                continue

            otp = extract_otp(message)
            print("🧾 SMS:", message.replace("\n", " ")[:120])

            if otp:
                send_telegram(
                    f"🔐 *TELEGRAM OTP RECEIVED*\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"🕒 `{ts}`\n"
                    f"📞 `{number}`\n"
                    f"🔢 *OTP:* `{otp}`"
                )
                time.sleep(1.2)  # flood safety

            sent.append(key)

        sent = sent[-15:]
        save_state({"sent": sent})

    except Exception as e:
        print("💥 UNHANDLED ERROR:", e)

    time.sleep(CHECK_INTERVAL)

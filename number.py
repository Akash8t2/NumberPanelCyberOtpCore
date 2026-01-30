#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import re
import requests
from datetime import datetime

# ================= CONFIG =================
API_URL = "http://51.89.99.105/NumberPanel/client/res/data_smscdr.php"

# 🔐 ENV VALUES
PHPSESSID = os.getenv("PHPSESSID")
SESSKEY   = "Q05RR0FPUUpCVg=="
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID   = "-1003559187782")

CHECK_INTERVAL = 12
STATE_FILE = "state.json"

# ================= HEADERS =================
HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0",
    "Referer": "http://51.89.99.105/NumberPanel/client/SMSDashboard",
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
    m = re.search(r'Telegram\s+code\s+(\d{4,8})', text, re.I)
    if m:
        return m.group(1)
    m = re.search(r'\b\d{4,8}\b', text)
    return m.group(0) if m else None

def send_telegram(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        },
        timeout=10
    )

# ================= START =================
print("🚀 NumberPanel OTP Bot Started")
print("📢 Chat ID:", CHAT_ID)

state = load_state()
sent = state["sent"]

while True:
    try:
        r = requests.get(
            API_URL,
            headers=HEADERS,
            cookies={"PHPSESSID": PHPSESSID},
            params={
                "sesskey": SESSKEY,
                "fdate1": datetime.now().strftime("%Y-%m-%d 00:00:00"),
                "fdate2": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "iDisplayStart": 0,
                "iDisplayLength": 3,
                "_": int(time.time() * 1000),
            },
            timeout=15
        )

        data = r.json()
        rows = data.get("aaData", [])
        rows.reverse()

        for row in rows:
            ts, pool, number, service, message = row[:5]
            key = f"{number}_{ts}"

            if key in sent:
                continue

            otp = extract_otp(message)
            print("🧾 SMS:", message)

            if otp:
                send_telegram(
                    f"🔐 *TELEGRAM OTP RECEIVED*\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"🕒 `{ts}`\n"
                    f"📞 `{number}`\n"
                    f"🔢 *OTP:* `{otp}`"
                )

            sent.append(key)

        sent = sent[-10:]
        save_state({"sent": sent})

    except Exception as e:
        print("❌ ERROR:", e)

    time.sleep(CHECK_INTERVAL)

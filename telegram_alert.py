import json
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
APPROVED_JOBS_FILE = "approved_jobs.json"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    response = requests.post(url, json=payload)
    if not response.ok:
        print(f"Failed to send message: {response.text}")

def format_job_message(job):
    title = job.get("title", "No title")
    link = job.get("link", "No link")
    pay = job.get("hourly_pay", "") or job.get("budget", "No pay info")
    reason = job.get("reason", "No reason provided")

    message = f"<b>{title}</b>\n\n"
    message += f"<b>Pay:</b> {pay}\n"
    message += f"<b>Reason:</b>\n{reason}\n"
    message += f"<a href=\"{link}\">View Job</a>"

    return message

def main():
    if not os.path.exists(APPROVED_JOBS_FILE):
        print(f"File not found: {APPROVED_JOBS_FILE}")
        return

    with open(APPROVED_JOBS_FILE, "r", encoding="utf-8") as f:
        try:
            jobs = json.load(f)
        except json.JSONDecodeError:
            print("Failed to parse JSON.")
            return

    if not jobs:
        print("No jobs to send.")
        return

    for job in jobs:
        message = format_job_message(job)
        send_telegram_message(message)
        time.sleep(3)

if __name__ == "__main__":
    main()

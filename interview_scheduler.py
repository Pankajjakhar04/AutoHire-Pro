import smtplib
import sqlite3
import random
from datetime import datetime, timedelta
from email.message import EmailMessage

# Replace with your email and app password
SENDER_EMAIL = 'jakhar.pankaj0903@gmail.com'
SENDER_PASSWORD = 'pfnz adci xxgv edps'  # App Password (NOT your regular Gmail password)


# === Generate Interview Time Slot ===
def generate_time_slot():
    base_time = datetime.strptime("2025-04-13 10:00", "%Y-%m-%d %H:%M")
    minutes_offset = random.choice([0, 30, 60, 90, 120, 150, 180, 210])  # 30-min slots from 10 AM to 2 PM
    interview_time = base_time + timedelta(minutes=minutes_offset)
    return interview_time.strftime("%I:%M %p")

# === Send Email ===
def send_email(to_email, name, job_title, interview_time):
    subject = f"Shortlisted for {job_title} Role - Interview Scheduled"
    body = f"""
Hi {name},

Congratulations! 🎉

You have been shortlisted for the position of {job_title}.

📅 Interview Date: Sunday, 13th April 2025  
⏰ Time Slot: {interview_time}

The interview will be held virtually. A Google Meet link will be shared 24 hours prior to the interview.

If the time slot doesn't work for you, kindly reply to this email at the earliest.

Best of luck!

Regards,  
Talent Acquisition Team
"""

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
            print(f"✅ Email sent to {name} at {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email to {name}: {e}")

# === Fetch Shortlisted Candidates From DB ===
conn = sqlite3.connect('cv_matching.db')
cursor = conn.cursor()

cursor.execute("SELECT candidate_name, email, job_title FROM candidate_match_results WHERE match_percentage >= 70")
shortlisted = cursor.fetchall()
conn.close()

# === Send Emails ===
used_slots = set()

for name, email, job_title in shortlisted:
    slot = generate_time_slot()
    while slot in used_slots:
        slot = generate_time_slot()
    used_slots.add(slot)

    send_email(email, name, job_title, slot)

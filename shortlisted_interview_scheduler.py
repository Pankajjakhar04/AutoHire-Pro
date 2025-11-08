import os
import re
import sqlite3
import pandas as pd
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from PyPDF2 import PdfReader
import random

# === CONFIG ===
CSV_FILE = 'Matches_for_selected_jd.csv'
CV_FOLDER = 'CV1'
DB_FILE = 'cv_matching.db'
TABLE_NAME = 'candidate_match_results'
SENDER_EMAIL = 'jakhar.pankaj0903@gmail.com'
SENDER_PASSWORD = ''
INTERVIEW_DATE = "2025-04-13"
TIME_SLOTS = [0, 30, 60, 90, 120, 150, 180, 210]

# === FUNCTIONS ===

def extract_info_from_cv(file_name):
    try:
        path = os.path.join(CV_FOLDER, file_name)
        reader = PdfReader(path)
        text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())

        email = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
        phone = re.findall(r'(\+?\d{1,3})?[\s\-]?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}', text)
        name = text.split('\n')[0].strip()

        return {
            'name': name or 'Unknown',
            'email': email[0] if email else '',
            'phone': phone[0] if phone else '',
        }
    except Exception as e:
        print(f"❌ Failed to extract from {file_name}: {e}")
        return {'name': 'Unknown', 'email': '', 'phone': ''}

def generate_time_slot(used_slots):
    base_time = datetime.strptime(f"{INTERVIEW_DATE} 10:00", "%Y-%m-%d %H:%M")
    while True:
        offset = random.choice(TIME_SLOTS)
        slot = base_time + timedelta(minutes=offset)
        slot_str = slot.strftime("%I:%M %p")
        if slot_str not in used_slots:
            used_slots.add(slot_str)
            return slot_str

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

# === MAIN EXECUTION ===

# Step 1: Load CSV
df = pd.read_csv(CSV_FILE)
df.columns = [col.strip().lower() for col in df.columns]  # Normalize column names

if 'cv_file' not in df.columns:
    raise KeyError("❌ 'cv_file' column is missing in the CSV.")

# Step 2: Set up DB
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cv_id TEXT,
        candidate_name TEXT,
        email TEXT,
        phone TEXT,
        job_title TEXT,
        matched_keywords TEXT,
        match_count INTEGER,
        match_percentage REAL
    )
''')

# Step 3: Process each row
used_slots = set()
shortlisted = 0

for _, row in df.iterrows():
    cv_file = row['cv_file']
    info = extract_info_from_cv(cv_file)

    if not info['email']:
        print(f"⚠️ Skipping {cv_file} due to missing email.")
        continue

    name = info['name']
    phone = info['phone']
    email = info['email']
    job_title = 'Selected Role'
    match_keywords = ''  # not provided in this CSV
    match_count = 0      # not provided in this CSV
    score = float(row.get('score', 0))

    # Insert into DB
    cursor.execute(f'''
        INSERT INTO {TABLE_NAME} (
            cv_id, candidate_name, email, phone,
            job_title, matched_keywords, match_count, match_percentage
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        cv_file, name, email, phone,
        job_title, match_keywords, match_count, score
    ))

    # Send email
    slot = generate_time_slot(used_slots)
    send_email(email, name, job_title, slot)
    shortlisted += 1

conn.commit()
conn.close()

print(f"\n🎯 Done! {shortlisted} candidates processed and notified.")

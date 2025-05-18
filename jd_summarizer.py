import pandas as pd
import ollama
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import os
import sys

# === Command-line Flag ===
FAST_MODE = '--fast' in sys.argv
MAX_CHARS = 500 if FAST_MODE else 750

# === Config ===
CSV_PATH = "job_description.csv"
OUTPUT_PATH = "summarized_job_descriptions.csv"
JD_COLUMN = 'Job Description'
NUM_WORKERS = os.cpu_count() or 4

# === Load CSV ===
df = pd.read_csv(CSV_PATH, encoding='ISO-8859-1')
job_descriptions = df[JD_COLUMN].dropna().tolist()

# === Cleaning Function ===
def clean_jd(text, max_len=MAX_CHARS):
    return text.replace('\n', ' ').replace('\r', '').strip()[:max_len]

# === Summarize Function with model switching ===
def summarize_jd(jd_text, model_name):
    short_jd = clean_jd(jd_text)
    prompt = f"""
Summarize this job description into:
- Title
- Skills
- Experience
- Responsibilities

JD: {short_jd}
"""
    try:
        response = ollama.chat(model=model_name, messages=[
            {"role": "user", "content": prompt}
        ])
        return response['message']['content']
    except Exception as e:
        return f"Error: {e}"

# === Parallel Summary with Multiple Models ===
def summarize_multi_model(jds):
    results = []
    mid = len(jds) // 2
    phi_jds = jds[:mid]
    tiny_jds = jds[mid:]

    def task_wrapper(jd, model):
        return summarize_jd(jd, model)

    futures = []
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures += [executor.submit(task_wrapper, jd, 'phi') for jd in phi_jds]
        futures += [executor.submit(task_wrapper, jd, 'tinyllama') for jd in tiny_jds]

        for future in tqdm(as_completed(futures), total=len(futures), desc="Summarizing with phi + tinyllama", unit="JD"):
            results.append(future.result())

    return results

# === Run ===
mode = "FAST (500 chars)" if FAST_MODE else "NORMAL (750 chars)"
print(f"\n🚀 Summarizing {len(job_descriptions)} job descriptions using phi + tinyllama")
print(f"💡 Mode: {mode} | Cores: {NUM_WORKERS}\n")

summaries = summarize_multi_model(job_descriptions)

# === Save Output ===
df = df.loc[df[JD_COLUMN].notna()].copy()
df['Summarized_JD'] = summaries
df.to_csv(OUTPUT_PATH, index=False)
print(f"\n✅ Done! Output saved to {OUTPUT_PATH}")

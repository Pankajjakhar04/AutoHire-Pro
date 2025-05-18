import os
import pandas as pd
import fitz  # PyMuPDF
import ollama
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time

# === CONFIG ===
JD_CSV = "summarized_job_descriptions.csv"
PDF_FOLDER = "CV1"
OUTPUT = "Matches_for_selected_jd.csv"
JD_COL = 'Summarized_JD'
THRESHOLD = 50
MODELS = ['phi', 'tinyllama']
MAX_LEN = 300
MAX_WORKERS = os.cpu_count() * 2

# === Load JDs ===
jd_df = pd.read_csv(JD_CSV)
jds = jd_df[JD_COL].dropna().tolist()

# === Let user pick a JD ===
print("📋 Available Job Descriptions:\n")
for i, jd in enumerate(jds):
    print(f"[{i+1}] {jd[:150]}...\n")

selected_idx = int(input("\n🔍 Select JD number to match against CVs: ")) - 1
selected_jd = jds[selected_idx]

print(f"\n✅ Selected JD #{selected_idx+1}:\n{selected_jd}\n")

# === Load CVs ===
pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]
cv_texts = []

for file in tqdm(pdf_files, desc="📄 Reading CVs"):
    try:
        doc = fitz.open(os.path.join(PDF_FOLDER, file))
        text = " ".join(page.get_text() for page in doc).strip()
        if len(text) > 50:  # Only add if text is meaningful
            cv_texts.append((file, text[:MAX_LEN]))  # Limit text length early
    except Exception as e:
        print(f"⚠️ Error reading {file}: {e}")
        continue

# === Matching Function ===
def get_score(jd, cv, model):
    prompt = f"""
You are a job recruiter AI. Score how well the candidate CV matches the job description.

ONLY return a single integer from 0 to 100. Do not add any explanation.

Job Description:
{jd}

Candidate CV:
{cv}

Match Score:
"""
    try:
        res = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
        raw = res['message']['content']
        numbers = re.findall(r'\d{1,3}', raw)
        if numbers:
            score = min(int(numbers[0]), 100)
            return score
        else:
            print(f"❌ No score found in response: {raw}")
            return -1
    except Exception as e:
        print(f"❌ Error in get_score(): {e}")
        return -1

def match_worker(cv_file, cv_text, model):
    score = get_score(selected_jd[:MAX_LEN], cv_text, model)
    if score >= THRESHOLD:
        return {
            "JD_Index": selected_idx + 1,
            "JD_Summary": selected_jd[:200],
            "CV_File": cv_file,
            "Score": score,
            "Model": model
        }

# === Parallel Matching ===
def match_selected_jd():
    results = []
    futures = []
    start = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for i, (cv_file, cv_text) in enumerate(cv_texts):
            model = MODELS[i % len(MODELS)]
            futures.append(executor.submit(match_worker, cv_file, cv_text, model))

        for f in tqdm(as_completed(futures), total=len(futures), desc="⚡ Matching"):
            res = f.result()
            if res:
                results.append(res)

    print(f"\n✅ Done in {round(time.time() - start, 2)} seconds. {len(results)} candidates matched.")
    return results

# === Run Matching ===
print(f"\n🚀 Matching JD #{selected_idx+1} with {len(cv_texts)} CVs using {MAX_WORKERS} threads...\n")
matches = match_selected_jd()

# === Save Results ===
if matches:
    pd.DataFrame(matches).to_csv(OUTPUT, index=False)
    print(f"\n📄 Matches saved to {OUTPUT}")
else:
    print("\n⚠️ No matches found. CSV not created.")

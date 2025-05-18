import os
import pandas as pd
import re
from docx import Document
from PyPDF2 import PdfReader
import nltk
from nltk.corpus import stopwords
from nltk import pos_tag, word_tokenize
from nltk.stem import WordNetLemmatizer

# === CONFIG ===
CV_FOLDER = 'CV1'  # Update as needed
CV_OUTPUT_FILE = 'cv_keywords_output.csv'

JD_FILE = 'summarized_job_descriptions.csv'  # Path to JD file
JD_COLUMN = 'Summarized_JD'
JD_OUTPUT_FILE = 'jd_keywords_output.csv'

# === SETUP ===
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('stopwords')
nltk.download('wordnet')

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# === HELPER FUNCTIONS ===
def get_wordnet_pos(tag):
    if tag.startswith('J'):
        return 'a'
    elif tag.startswith('V'):
        return 'v'
    elif tag.startswith('N'):
        return 'n'
    elif tag.startswith('R'):
        return 'r'
    else:
        return 'n'

def extract_keywords(text):
    tokens = word_tokenize(text.lower())
    tagged = pos_tag(tokens)
    keywords = [
        lemmatizer.lemmatize(word, get_wordnet_pos(pos))
        for word, pos in tagged
        if word.isalpha() and word not in stop_words
    ]
    return sorted(set(keywords))

def read_txt(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def read_pdf(file_path):
    reader = PdfReader(file_path)
    return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())

def read_docx(file_path):
    doc = Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs)

def read_cv(file_path):
    if file_path.endswith('.txt'):
        return read_txt(file_path)
    elif file_path.endswith('.pdf'):
        return read_pdf(file_path)
    elif file_path.endswith('.docx'):
        return read_docx(file_path)
    else:
        return ""

# === PROCESS CVs ===
cv_data = []
for filename in os.listdir(CV_FOLDER):
    file_path = os.path.join(CV_FOLDER, filename)
    if not os.path.isfile(file_path):
        continue

    cv_text = read_cv(file_path)
    keywords = extract_keywords(cv_text)
    cv_data.append({
        'CV_ID': filename,
        'Extracted_Keywords': ", ".join(keywords)
    })

df_cv = pd.DataFrame(cv_data)
df_cv.to_csv(CV_OUTPUT_FILE, index=False)
print(f"✅ Extracted keywords from CVs saved to: {CV_OUTPUT_FILE}")

# === PROCESS JDs ===
df_jd = pd.read_csv(JD_FILE)
jd_keywords_list = []

for idx, jd_text in enumerate(df_jd[JD_COLUMN]):
    keywords = extract_keywords(str(jd_text))
    jd_keywords_list.append({
        'JD_ID': idx + 1,
        'Extracted_Keywords': ", ".join(keywords)
    })

df_jd_keywords = pd.DataFrame(jd_keywords_list)
df_jd_keywords.to_csv(JD_OUTPUT_FILE, index=False)
print(f"✅ Extracted keywords from JDs saved to: {JD_OUTPUT_FILE}")

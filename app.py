import streamlit as st
import spacy
import re
import json
from pathlib import Path

# -----------------------
# Load SpaCy model safely
# -----------------------
@st.cache_resource
def load_model():
    return spacy.load("en_core_web_sm")

nlp = load_model()

# -----------------------
# Helper functions
# -----------------------
def extract_name(doc):
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return None

def extract_email(text):
    return re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)

def extract_phone(text):
    return re.findall(r"\+?\d[\d\s\-]{8,}\d", text)

def extract_urls(text):
    return re.findall(r"(https?://\S+)", text)

def extract_education(text):
    keywords = ["B.Tech", "M.Tech", "B.Sc", "M.Sc", "PhD", "MBA"]
    found = [k for k in keywords if k.lower() in text.lower()]
    return list(set(found))

def extract_skills(text):
    skills_list = ["Python", "Java", "SQL", "C++", "TensorFlow", "Pandas",
                   "NumPy", "Machine Learning", "Deep Learning", "Django"]
    found = [s for s in skills_list if s.lower() in text.lower()]
    return list(set(found))

def parse_resume(text):
    doc = nlp(text)

    data = {
        "Name": extract_name(doc),
        "Emails": extract_email(text),
        "Phones": extract_phone(text),
        "URLs": extract_urls(text),
        "Education": extract_education(text),
        "Skills": extract_skills(text),
        "Raw Text": text[:500] + "..." if len(text) > 500 else text
    }
    return data

# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="Resume Parser", layout="wide")
st.title("📄 NLP Resume Parser")
st.write("Upload a resume (TXT only for now) and extract structured details.")

uploaded_file = st.file_uploader("Upload Resume (.txt)", type=["txt"])

if uploaded_file:
    text = uploaded_file.read().decode("utf-8", errors="ignore")
    result = parse_resume(text)

    st.subheader("Extracted Information")
    st.json(result)

    # Save JSON option
    json_file = "parsed_resume.json"
    Path(json_file).write_text(json.dumps(result, indent=2))
    with open(json_file, "rb") as f:
        st.download_button("⬇️ Download JSON", f, file_name="parsed_resume.json")

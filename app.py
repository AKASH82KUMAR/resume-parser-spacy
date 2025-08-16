import streamlit as st
import spacy
import re
import json
from pathlib import Path

# Load SpaCy model
@st.cache_resource
def load_model():
    return spacy.load("en_core_web_sm")

nlp = load_model()

# Sample skills list (extendable)
SKILLS = [
    "python", "java", "c++", "sql", "javascript", "html", "css", "machine learning",
    "deep learning", "nlp", "spacy", "tensorflow", "pytorch", "excel", "tableau"
]

def extract_entities(text):
    doc = nlp(text)

    # Extract name (first PERSON entity)
    name = None
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text
            break

    # Regex-based extractions
    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phones = re.findall(r"\+?\d[\d \-\(\)]{7,}\d", text)
    urls = re.findall(r"(https?://[^\s]+)", text)

    # Skills match (case insensitive)
    found_skills = []
    for token in doc:
        if token.text.lower() in SKILLS:
            found_skills.append(token.text)

    # Education detection
    education = re.findall(r"(B\.?Tech|M\.?Tech|B\.?Sc|M\.?Sc|MBA|Ph\.?D)", text, re.I)

    # Experience (years)
    experience = re.findall(r"(\d+)\+?\s*(?:years|yrs)", text, re.I)

    return {
        "Name": name,
        "Emails": list(set(emails)),
        "Phones": list(set(phones)),
        "Links": list(set(urls)),
        "Skills": list(set(found_skills)),
        "Education": list(set(education)),
        "Experience": list(set(experience))
    }

# ---------------- STREAMLIT UI ---------------- #

st.set_page_config(page_title="Resume Parser", page_icon="📄", layout="wide")

st.title("📄 Resume Parser with spaCy")
st.write("Upload a resume (TXT, DOCX, or PDF) and extract structured details.")

uploaded_file = st.file_uploader("Upload Resume", type=["txt", "pdf", "docx"])

if uploaded_file:
    # Read text content
    if uploaded_file.type == "text/plain":
        text = uploaded_file.read().decode("utf-8")
    else:
        text = uploaded_file.read().decode("latin-1")  # Fallback for PDF/DOCX simple text extraction

    st.subheader("📑 Extracted Resume Text")
    st.text_area("Resume Content", text, height=250)

    # Run parser
    parsed = extract_entities(text)

    st.subheader("🔍 Extracted Information")
    st.json(parsed)

    # Allow download
    st.download_button(
        "Download JSON",
        data=json.dumps(parsed, indent=2),
        file_name="parsed_resume.json",
        mime="application/json"
    )

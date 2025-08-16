import io
import json
import re
import time
from typing import Dict, Any, List

import streamlit as st

# Lazy import heavy deps to speed cold start
def lazy_imports():
    import spacy
    from spacy.cli import download as spacy_download
    import pdfminer
    from pdfminer.high_level import extract_text as pdf_extract_text
    import docx2txt
    return spacy, spacy_download, pdf_extract_text, docx2txt

st.set_page_config(page_title="Resume Parser (spaCy)", page_icon="📄", layout="wide")
st.title("📄 Resume Parser using spaCy")
st.caption("Upload a resume (PDF/DOCX/TXT) → get extracted fields (Name, Email, Phone, Skills, Education, Experience).")

with st.expander("About this app"):
    st.markdown("""
This app uses **spaCy** for NLP plus light rule-based extraction to parse resumes.
It supports **PDF**, **DOCX**, and **TXT** files. You can download parsed JSON and the cleaned text.
- **Fields**: Name, Email, Phone, Skills, Education entities, Experience (years), Links.
- **Model**: `en_core_web_sm` (auto-installs if missing).
- **Privacy**: Parsing happens within this session; nothing is uploaded elsewhere.
    """)

# ---------- Sidebar ----------
st.sidebar.header("Upload")
uploaded = st.sidebar.file_uploader("Upload resume", type=["pdf","docx","txt"])
st.sidebar.markdown("Or try a sample:")
sample_choice = st.sidebar.selectbox("Samples", ["(choose)", "Sample Resume (TXT)"])

# Skills DB (extendable)
SKILL_DB = sorted(list(set([
    # Programming
    "Python","Java","C","C++","C#","Go","Rust","JavaScript","TypeScript","SQL","R","Scala","MATLAB","Bash","Shell",
    # ML/AI
    "Machine Learning","Deep Learning","NLP","Computer Vision","CNN","RNN","Transformers","PyTorch","TensorFlow","Keras","scikit-learn","spaCy","XGBoost","LightGBM",
    # Data
    "Pandas","NumPy","Matplotlib","Seaborn","Plotly","Spark","Hadoop","Hive","Pig","Airflow","Kafka","dbt",
    # Web/Cloud/DevOps
    "Django","Flask","FastAPI","Streamlit","React","Node.js","AWS","GCP","Azure","Docker","Kubernetes","Terraform","CI/CD","Git",
    # Databases
    "MySQL","PostgreSQL","MongoDB","Redis","Elasticsearch","Neo4j",
    # Tools/Other
    "Tableau","Power BI","Excel","Figma","JIRA","Confluence","Agile","Scrum"
]))))

def extract_text_from_bytes(name: str, data: bytes) -> str:
    ext = name.lower().split(".")[-1]
    spacy, spacy_download, pdf_extract_text, docx2txt = lazy_imports()
    if ext == "pdf":
        try:
            text = pdf_extract_text(io.BytesIO(data))
            return text or ""
        except Exception as e:
            return ""
    elif ext == "docx":
        try:
            # docx2txt expects a path or file-like, but we can write to temp buffer
            # Simpler: save to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
                tf.write(data)
                tmp_path = tf.name
            out = docx2txt.process(tmp_path) or ""
            return out
        except Exception:
            return ""
    elif ext == "txt":
        return data.decode("utf-8", errors="ignore")
    else:
        return ""

def ensure_spacy_model():
    spacy, spacy_download, *_ = lazy_imports()
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        with st.spinner("Downloading spaCy model en_core_web_sm ..."):
            spacy_download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
    return nlp

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"\+?\d[\d ()-]{7,}\d")
URL_RE = re.compile(r"(https?://[^\s)]+)")

EDU_KWS = [
    "B.Tech","B.E","B.Sc","BCA","BBA","B.Com","M.Tech","M.E","M.Sc","MCA","MBA","PhD","Doctorate",
    "Bachelor","Master","Diploma","Intermediate","PUC","HSC","CBSE","ICSE"
]

TITLE_HINTS = ["Engineer","Developer","Analyst","Scientist","Consultant","Manager","Intern","Specialist","Architect"]

def normalize_whitespace(s: str) -> str:
    return re.sub(r"[ \t]+"," ", re.sub(r"\r","",s)).strip()

def parse_resume(text: str, nlp) -> Dict[str, Any]:
    clean = normalize_whitespace(text)
    doc = nlp(clean)

    # Name: first PERSON entity near top
    name = None
    for ent in doc.ents:
        if ent.label_ == "PERSON" and 0 <= ent.start_char < min(200, len(clean)):
            name = ent.text
            break

    # Emails/Phones/Links
    emails = EMAIL_RE.findall(clean)
    phones = PHONE_RE.findall(clean)
    links = URL_RE.findall(clean)

    # Skills (keyword match, case-insensitive)
    skills = sorted({s for s in SKILL_DB if re.search(rf"\\b{re.escape(s)}\\b", clean, flags=re.I)})

    # Education snippets
    edu_hits: List[str] = []
    for kw in EDU_KWS:
        for m in re.finditer(rf".{{0,40}}\\b{re.escape(kw)}\\b.{{0,40}}", clean, flags=re.I):
            edu_hits.append(m.group(0))
    edu_hits = list(dict.fromkeys(edu_hits))  # dedupe

    # Experience (years)
    exp_years = None
    m = re.search(r"(?:experience|exp)[:\\s]+(\\d{1,2})\\+?\\s*(?:years|yrs)?", clean, flags=re.I)
    if m:
        try:
            exp_years = int(m.group(1))
        except Exception:
            pass
    if exp_years is None:
        m2 = re.search(r"(\\d{1,2})\\+?\\s*(?:years|yrs)\\s+of\\s+experience", clean, flags=re.I)
        if m2:
            try:
                exp_years = int(m2.group(1))
            except Exception:
                pass

    # Titles (optional hints)
    titles = []
    for t in TITLE_HINTS:
        if re.search(rf"\\b{re.escape(t)}\\b", clean, flags=re.I):
            titles.append(t)
    titles = sorted(list(set(titles)))

    parsed = {
        "name": name,
        "emails": list(dict.fromkeys(emails)),
        "phones": list(dict.fromkeys(phones)),
        "links": list(dict.fromkeys(links)),
        "skills": skills,
        "education_snippets": edu_hits[:10],
        "experience_years": exp_years,
        "title_hints": titles,
        "summary_text_preview": clean[:600] + ("..." if len(clean) > 600 else "")
    }
    return parsed

# ---------- Main UI ----------
col_left, col_right = st.columns([1.1, 1])

raw_text = ""
file_meta = None

if uploaded is not None:
    raw_text = extract_text_from_bytes(uploaded.name, uploaded.getvalue())
    file_meta = {"filename": uploaded.name, "size": len(uploaded.getvalue())}

elif sample_choice == "Sample Resume (TXT)":
    # Load bundled sample
    with open("samples/sample_resume.txt", "r", encoding="utf-8") as f:
        raw_text = f.read()
    file_meta = {"filename": "sample_resume.txt", "size": len(raw_text.encode("utf-8"))}

if raw_text.strip():
    with st.spinner("Loading spaCy model & parsing..."):
        nlp = ensure_spacy_model()
        parsed = parse_resume(raw_text, nlp)

    with col_left:
        st.subheader("Parsed Fields")
        st.json(parsed)

        # Download JSON
        st.download_button("⬇️ Download Parsed JSON", data=json.dumps(parsed, indent=2), file_name="parsed_resume.json", mime="application/json")

        # Simple keyword filter
        st.markdown("**Quick Skill Check**")
        kw = st.text_input("Search skill keyword", "")
        if kw:
            st.write("Found:", kw if any(re.search(rf"\\b{re.escape(kw)}\\b", s, flags=re.I) for s in parsed.get("skills", [])) else "Not found")

    with col_right:
        st.subheader("Extracted Text")
        st.code(raw_text[:4000] + ("\n...\n(truncated)" if len(raw_text) > 4000 else ""), language="text")

        if file_meta:
            st.caption(f"File: {file_meta['filename']} • Size: {file_meta['size']} bytes")

else:
    st.info("👈 Upload a resume or select the sample from the sidebar to see results.")

st.markdown("---")
st.caption("Built with ❤️ using spaCy + Streamlit.")


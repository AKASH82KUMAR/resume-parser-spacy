# 📄 Resume Parser (spaCy) — Streamlit App

An NLP project that parses resumes using **spaCy** + light rules. Upload a **PDF/DOCX/TXT**, get structured data:
- Name
- Emails
- Phone numbers
- Skills (from a curated list)
- Education snippets (B.Tech, M.Sc, PhD, etc.)
- Experience (years)
- Links (URLs)

## 🚀 Quickstart (Local)
```bash
# 1) Create venv (recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install deps
pip install -r requirements.txt

# 3) Run app
streamlit run app.py
```

> First run will auto-download the spaCy model `en_core_web_sm` if missing.

## 🌐 Deploy — Streamlit Cloud (free)
1. Push these files to a new GitHub repo (e.g., `resume-parser-spacy`).
2. Go to **share.streamlit.io** (Streamlit Community Cloud) and sign in.
3. **New app** → pick your repo → `main` branch → `app.py` as entrypoint.
4. Click **Deploy**. Done! You’ll get a public URL like:
   `https://<your-app-name>.streamlit.app`

## 🤗 Alternative Deploy — Hugging Face Spaces
1. Create a new **Space** → choose **Streamlit** template.
2. Upload `app.py`, `requirements.txt`, `samples/` to the Space.
3. The Space will build and give you a public URL.

## 📁 Project Structure
```
.
├─ app.py
├─ requirements.txt
├─ samples/
│  └─ sample_resume.txt
└─ README.md
```

## 🧠 Notes
- This is a **baseline** parser. Accuracy can be improved by training a **custom spaCy NER** for entities like `EDUCATION`, `ORG`, `TITLE`, and using better skills ontologies.
- Add PDF layout-awareness (e.g., pdfplumber) and section-based parsing for further gains.
- Keep the `SKILL_DB` in `app.py` growing with domain-specific terms.

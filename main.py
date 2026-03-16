import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import psycopg2
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
from docx import Document
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


st.set_page_config("AI Resume Analyzer", "📊", layout="wide")

st.markdown("""<meta name="google-site-verification" content="Ur5oXAnC1cNCwVqD3_z7ASYo7oKQYKDV8KNH_xiXElg" />""",unsafe_allow_html=True)
# =====================
# DATABASE CONFIG
# =====================
import os
DATABASE_URL = os.getenv("DATABASE_URL")
def connect_db():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return none

DB_CONFIG = {
    "host": "dpg-d6rarl7afjfc73f3uhi0-a",
    "database": "resume_analyzer",
    "user": "postgres",
    "password": "U92ocib5VdbcGj7qEp94x2EOlDT947gC",
    "port": "5432"
}
def connect_db():
    return psycopg2.connect(**DB_CONFIG)
    
# =====================
# NLTK SETUP
# =====================
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")

# =====================
# DATABASE FUNCTIONS
# =====================
def init_db():
    try:
        conn = connect_db()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id SERIAL PRIMARY KEY,
            resume_name VARCHAR(255),
            match_score FLOAT,
            job_description TEXT,
            analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_resume TEXT
        )
        """)

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        st.error(f"Database error: {e}")

def save_to_db(names, scores, job_desc, processed_texts):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        for n, s, t in zip(names, scores, processed_texts):
            cursor.execute("""
                INSERT INTO analysis_results
                (resume_name, match_score, job_description, analysis_date,processed_resume)
                VALUES (%s, %s, %s, %s,%s)
            """, (n, s, job_desc[:1000], datetime.now(),t[:1000]))

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        st.error(f"Database save error: {e}")

def get_db_stats():
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT resume_name, match_score, analysis_date
            FROM analysis_results
            ORDER BY analysis_date DESC
        """)

        data = cursor.fetchall()

        cursor.close()
        conn.close()

        return pd.DataFrame(data, columns=["Resume", "Score", "Date"])

    except Exception as e:
        st.error(f"Database read error: {e}")
        return pd.DataFrame()
# -----------------------------------
#========== HEADER-------------------
# -------------------------------
st.header("""**Smart Resume Screening Powered By Artificial Intelligence**""")
st.markdown("""Upload resume (pdf/docx) and paste the job description to see how well they match !
            This tool can analyze more than one resume at a time.
            It reducing manual screening time.
            """)
with st.sidebar:
    st.header("About")
    st.info("""
    *Features:*
    - Measures how your resume matches a job description
    - Upload 10+ resumes at once
    - Color-coded match score(🔴Low 🟡Medium 🟢High )
    - Side-by-side comparison table
    - Individual suggetions
    - Store the data in database
            """)
    st.header("How It works")
    st.write("""
    1. Upload your resume (PDF/DOCX)
    2. Paste the job description
    3. Click **Analyze Match**
    4. Review score & suggetion
    """)
# =====================
# TEXT PROCESSING
# =====================
def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        return " ".join([p.extract_text() or "" for p in reader.pages])
    except:
        return ""
    
def extract_text_from_docx(uploaded_file):
    doc = Document(uploaded_file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + " "
    return text.strip()

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def remove_stopwords(text):
    stop_words = set(stopwords.words("english"))
    words = word_tokenize(text)
    return " ".join([w for w in words if w not in stop_words and len(w) > 2])

def preprocess(text):
    return remove_stopwords(clean_text(text))

# =====================
# ANALYSIS FUNCTION
# =====================
def analyze_resumes(resumes, jd):
    jd_clean = preprocess(jd)
    resumes_clean = [preprocess(r) for r in resumes]

    corpus = resumes_clean + [jd_clean]
    vectorizer = TfidfVectorizer(max_features=1000)
    tfidf = vectorizer.fit_transform(corpus)

    scores = cosine_similarity(tfidf[:-1], tfidf[-1]).flatten() * 100

    jd_terms = set(jd_clean.split())
    gaps = []
    for r in resumes_clean:
        r_terms = set(r.split())
        gaps.append(list(jd_terms - r_terms)[:10])

    return [round(float(s), 2) for s in scores], gaps, resumes_clean

# =====================
# STREAMLIT APP
# =====================
def main():
    init_db()



    st.markdown("""
<style>
*{
font-family:bold ;
color:beige;
}
:root{
primaryColor="#54acbf";
}
.stApp {
background: linear-gradient(
to left,
#a7ebf2,#54acbf,#26658c,#023859,#011c40
);
}
                /* Transparent Text Area */
textarea {
background-color: rgba(255,255,255,0.1) !important;
color: white !important;
border-radius: 10px !important;
border: 1px solid rgba(255,255,255,0.3) !important;
backdrop-filter: blur(10px);
}

/* Upload box transparency */
[data-testid="stFileUploader"] {
background: rgba(255,255,255,0.1);
border-radius: 10px;
padding: 10px;
}

/* Input text color */
input {
background-color: rgba(255,255,255,0.1) !important;
color: white !important;
}


</style>
""", unsafe_allow_html=True)

    st.title("🤖 AI-Based Resume Analyzer")

    tab1, tab2 = st.tabs(["📊 ANALYZE", "⌛ HISTORY"])

    # =====================
    # TAB 1 — ANALYZE
    # =====================
    with tab1:
        uploaded_files = st.file_uploader(
            "📁 Upload multiple resumes (PDF/DOCX)",
            type=["pdf","docx"],
            accept_multiple_files=True
        )

        job_description = st.text_area(
            "📝 Paste job description",
            height=200
        )

        if st.button("🚀 Analyze All", type="primary"):
            if not uploaded_files or not job_description.strip():
                st.warning("Please upload resumes and paste job description")
                return

            texts, names = [], []
            for f in uploaded_files:
                if f.name.endswith(".pdf"):
                    t = extract_text_from_pdf(f)
                elif f.name.endswith(".docx"):
                    t = extract_text_from_docx(f)
                else:
                    t = None
                if t:
                    texts.append(t)
                    names.append(f.name)

            scores, gaps, processed = analyze_resumes(texts, job_description)

            df = pd.DataFrame({
                "Resume": names,
                "Match Score (%)": scores,
                "Missing Skills": [", ".join(g) if g else "None" for g in gaps]
            }).sort_values("Match Score (%)", ascending=False)

            st.session_state["df"] = df
            save_to_db(names, scores, job_description, processed)

            st.subheader("📊 Results")
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.download_button(
                "⬇️ Download Results (CSV)",
                df.to_csv(index=False),
                "resume_analysis.csv",
                "text/csv"
            )

            # Graph
            fig, ax = plt.subplots(figsize=(10, len(df)*0.6 + 1))
            colors = [
                "#ff4b4b" if s < 40 else "#ffa726" if s < 70 else "#0f9d58"
                for s in df["Match Score (%)"]
            ]
            bars = ax.barh(df["Resume"], df["Match Score (%)"], color=colors)
            ax.set_xlim(0, 100)
            ax.set_xlabel("Match Score (%)")
            ax.set_title("Resume vs Job Match")

            for bar, score in zip(bars, df["Match Score (%)"]):
                ax.text(
                    score + 1,
                    bar.get_y() + bar.get_height()/2,
                    f"{score}%",
                    va="center",
                    fontweight="bold"
                )

            st.pyplot(fig)

            # Suggestions
            st.subheader("💡 Suggestions")
            for _, r in df.iterrows():
                if r["Match Score (%)"] < 40:
                    st.error(f"🔴 {r['Resume']} – Needs major improvement")
                elif r["Match Score (%)"] < 70:
                    st.warning(f"🟡 {r['Resume']} – Moderate match")
                else:
                    st.success(f"🟢 {r['Resume']} – Excellent match")

    # =====================
    # TAB 2 — HISTORY ONLY
    # =====================
    with tab2:
        st.subheader("⌛ Previous Analysis")
        st.dataframe(get_db_stats(), use_container_width=True)


# ... all existing analysis and chart code above ...

# --- SIDEBAR CREDITS ---
st.sidebar.markdown("---") # This adds a nice separator line
st.sidebar.caption("Project Information") # Smaller heading style
st.sidebar.write("🚀 **Developed & Deployed by:**")
st.sidebar.info("Subhadra Biswal") 

# =====================
# RUN APP
# =====================
if __name__ == "__main__":
   main()

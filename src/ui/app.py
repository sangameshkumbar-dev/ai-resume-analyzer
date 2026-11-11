"""
Streamlit Web Application for AI Resume Analyzer and Job Matcher.
Combines traditional NLP, dense semantic similarity, and local LLM recommendations.
Zero external APIs. Corporate-friendly, transparent, and explainable.
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import json

from src.stage1_ingestion.extractor import PDFResumeExtractor
from src.stage1_ingestion.validator import ResumeValidator
from src.stage2_extraction.resume_parser import ResumeParser, CandidateProfile
from src.stage3_matching.jd_parser import JobDescriptionParser
from src.stage3_matching.scoring_engine import ScoringEngine
from src.stage4_recommendations.local_llm import LocalLLMClient
from src.stage4_recommendations.recommender import ResumeRecommender
from src.stage4_recommendations.report_generator import ReportGenerator
from src.ui.components import render_match_gauge, render_radar_breakdown, render_score_bar_breakdown
from src.config import SAMPLE_RESUMES_DIR, SAMPLE_JOBS_DIR

# Set page config
st.set_page_config(
    page_title="AI Resume Analyzer & Job Matcher",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished modern design (Dark & Light theme adaptive)
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
        opacity: 0.85;
    }
    .metric-card {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
        line-height: 1.6;
        font-size: 0.98rem;
    }
    @media (prefers-color-scheme: light) {
        .metric-card {
            background-color: #F8FAFC;
            border-color: #E2E8F0;
            color: #1E293B;
        }
    }
    .skill-pill {
        display: inline-block;
        padding: 4px 10px;
        margin: 3px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .skill-matched {
        background-color: rgba(34, 197, 94, 0.15);
        color: #4ADE80;
        border: 1px solid rgba(34, 197, 94, 0.35);
    }
    .skill-missing {
        background-color: rgba(239, 68, 68, 0.15);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.35);
    }
    .skill-preferred {
        background-color: rgba(245, 158, 11, 0.15);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.35);
    }
    .skill-extra {
        background-color: rgba(99, 102, 241, 0.15);
        color: #A5B4FC;
        border: 1px solid rgba(99, 102, 241, 0.35);
    }
    .rewrite-card {
        background-color: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-left: 4px solid #3B82F6;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 14px;
        line-height: 1.6;
    }
    @media (prefers-color-scheme: light) {
        .rewrite-card {
            background-color: #F8FAFC;
            border-color: #E2E8F0;
            border-left-color: #3B82F6;
            color: #1E293B;
        }
    }
    .rewrite-card .orig-label {
        opacity: 0.7;
        font-size: 0.92rem;
        margin-bottom: 6px;
    }
    .rewrite-card .enh-text {
        color: #38BDF8;
        font-weight: 600;
        font-size: 0.98rem;
    }
    @media (prefers-color-scheme: light) {
        .rewrite-card .enh-text {
            color: #0369A1;
        }
    }
    .rewrite-card .critique-note {
        opacity: 0.65;
        font-size: 0.82rem;
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "extracted_doc" not in st.session_state:
    st.session_state.extracted_doc = None
if "candidate_profile" not in st.session_state:
    st.session_state.candidate_profile = None
if "jd_text" not in st.session_state:
    st.session_state.jd_text = ""
if "match_results" not in st.session_state:
    st.session_state.match_results = None
if "recommendations" not in st.session_state:
    st.session_state.recommendations = None
if "active_resume_id" not in st.session_state:
    st.session_state.active_resume_id = None

# Initialize Singletons
@st.cache_resource
def get_extractor():
    return PDFResumeExtractor()

@st.cache_resource
def get_parser():
    return ResumeParser()

@st.cache_resource
def get_scoring_engine():
    return ScoringEngine()

@st.cache_resource
def get_jd_parser():
    return JobDescriptionParser()


# --- SIDEBAR CONFIGURATION ---
st.sidebar.title("⚙️ Engine Controls")

st.sidebar.markdown("### Local AI Configuration")
llm_provider = st.sidebar.selectbox(
    "LLM Provider Mode",
    options=["auto", "ollama", "huggingface", "fallback"],
    index=0,
    help="Select local engine. Auto checks for running Ollama instance, falling back to local heuristic/HF."
)

ollama_model = st.sidebar.text_input(
    "Ollama Model Name",
    value="llama3.2:3b",
    help="Local Ollama model tag (e.g., llama3.2:3b, mistral, phi3, qwen2.5)"
)

# Ollama Connectivity Health Check
llm_client = LocalLLMClient(provider=llm_provider, ollama_model=ollama_model)
ollama_status = llm_client.check_ollama_status()

if ollama_status["running"]:
    st.sidebar.success(f"🟢 Ollama Daemon Online\nModels: {', '.join(ollama_status['models']) or 'None'}")
else:
    st.sidebar.info("🟡 Ollama Offline (Using Smart Heuristic/HuggingFace Fallback)")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🧪 Quick Load Sample Data")
col_s1, col_s2 = st.sidebar.columns(2)

if col_s1.button("Full Stack Sample"):
    fs_pdf = SAMPLE_RESUMES_DIR / "resume_senior_fullstack.pdf"
    fs_jd = SAMPLE_JOBS_DIR / "senior_fullstack_engineer.txt"
    if fs_pdf.exists() and fs_jd.exists():
        with open(fs_pdf, "rb") as f:
            pdf_bytes = f.read()
        with open(fs_jd, "r", encoding="utf-8") as f:
            st.session_state.jd_text = f.read()
        extractor = get_extractor()
        doc = extractor.extract_from_bytes(pdf_bytes, filename=fs_pdf.name)
        st.session_state.extracted_doc = doc
        st.session_state.active_resume_id = f"sample_{fs_pdf.name}"
        st.session_state.candidate_profile = get_parser().parse(doc)
        st.session_state.match_results = None
        st.session_state.recommendations = None
        st.rerun()

if col_s2.button("ML Engineer Sample"):
    ml_pdf = SAMPLE_RESUMES_DIR / "resume_data_scientist.pdf"
    ml_jd = SAMPLE_JOBS_DIR / "machine_learning_engineer.txt"
    if ml_pdf.exists() and ml_jd.exists():
        with open(ml_pdf, "rb") as f:
            pdf_bytes = f.read()
        with open(ml_jd, "r", encoding="utf-8") as f:
            st.session_state.jd_text = f.read()
        extractor = get_extractor()
        doc = extractor.extract_from_bytes(pdf_bytes, filename=ml_pdf.name)
        st.session_state.extracted_doc = doc
        st.session_state.active_resume_id = f"sample_{ml_pdf.name}"
        st.session_state.candidate_profile = get_parser().parse(doc)
        st.session_state.match_results = None
        st.session_state.recommendations = None
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<small><b>3-Stage Architecture:</b><br/>"
    "• <b>Stage 1:</b> Resume Upload, Text Extraction & Validation<br/>"
    "• <b>Stage 2:</b> Resume Information Extraction (Skills, Edu, Exp, Projects, Certs, Years)<br/>"
    "• <b>Stage 3:</b> Resume–Job Matching Engine (Skills, Semantic Sim, Overall Score, LLM Recs)<br/>"
    "<i>Local Ollama & Hugging Face Transformers. No LangChain. 100% Corporate-safe.</i></small>",
    unsafe_allow_html=True
)

# --- MAIN DASHBOARD HEADER ---
st.markdown('<div class="main-title">🎯 AI Resume Analyzer & Job Matcher</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">3-Stage Evaluation Engine combining <b>Traditional NLP</b>, '
    '<b>Dense Semantic Embeddings</b>, and <b>Local LLM Recommendations</b>.</div>',
    unsafe_allow_html=True
)

# 3 STAGES TABS
tab1, tab2, tab3 = st.tabs([
    "📥 Stage 1: Resume Upload & Text Extraction",
    "🧠 Stage 2: Resume Information Extraction",
    "⚖️ Stage 3: Resume–Job Matching Engine"
])


# ==========================================
# STAGE 1: RESUME UPLOAD & TEXT EXTRACTION
# ==========================================
with tab1:
    st.subheader("Stage 1: Resume Upload & Text Extraction")
    st.caption("Upload your resume in PDF format. Validates file type, size, and usable text extraction before user verification.")

    uploaded_file = st.file_uploader(
        "Choose a PDF Resume",
        type=["pdf"],
        help="Upload a standard PDF resume (up to 10MB)"
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        file_id = f"upload_{uploaded_file.name}_{len(file_bytes)}"
        # Check if a new or different resume has been uploaded
        if st.session_state.get("active_resume_id") != file_id:
            extractor = get_extractor()
            extracted_doc = extractor.extract_from_bytes(file_bytes, filename=uploaded_file.name)
            st.session_state.extracted_doc = extracted_doc
            st.session_state.active_resume_id = file_id
            if extracted_doc.validation and extracted_doc.validation.is_valid:
                st.session_state.candidate_profile = get_parser().parse(extracted_doc)
            else:
                st.session_state.candidate_profile = None
            # Invalidate downstream match results from the previous resume
            st.session_state.match_results = None
            st.session_state.recommendations = None
    elif (st.session_state.get("active_resume_id") or "").startswith("upload_"):
        # User cleared the uploaded file (clicked the 'x' in the uploader)
        st.session_state.extracted_doc = None
        st.session_state.candidate_profile = None
        st.session_state.active_resume_id = None
        st.session_state.match_results = None
        st.session_state.recommendations = None

    doc = st.session_state.extracted_doc

    if doc and doc.validation:
        val = doc.validation
        # Validation Metrics Bar
        m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
        m_col1.metric("File Name", val.filename[:18] + ("..." if len(val.filename) > 18 else ""))
        m_col2.metric("File Size", f"{val.file_size_kb} KB")
        m_col3.metric("Page Count", f"{val.page_count} pages")
        m_col4.metric("Word Count", f"{val.word_count} words")
        m_col5.metric("Extract Quality", val.quality_badge)

        # Show any errors or warnings
        if val.errors:
            for err in val.errors:
                st.error(f"❌ {err}")
        if val.warnings:
            for warn in val.warnings:
                st.warning(f"⚠️ {warn}")

        if val.is_valid:
            st.markdown("### 📝 Verified Extracted Text")
            st.info("Review the extracted text below. You can edit or refine any section before running NLP extraction.")
            
            # Interactive editable text verification with dynamic key based on active resume ID
            # This ensures that uploading a new resume replaces the text area contents immediately
            current_id = st.session_state.get("active_resume_id") or "default"
            text_area_key = f"verified_resume_text_{current_id}"

            verified_text = st.text_area(
                "Extracted Text (Editable for Verification)",
                value=doc.normalized_text,
                height=320,
                key=text_area_key
            )

            if st.button("✅ Confirm & Parse Resume (Proceed to Stage 2)", type="primary"):
                doc.normalized_text = verified_text
                st.session_state.candidate_profile = get_parser().parse(doc)
                st.session_state.match_results = None
                st.session_state.recommendations = None
                st.success("Resume text confirmed! Navigate to 'Stage 2: Information Extraction' tab to view extracted candidate profile.")
    else:
        st.info("👆 Please upload a PDF resume or click one of the 'Quick Load Sample Data' buttons in the left sidebar to begin.")


# ==========================================
# STAGE 2: RESUME INFORMATION EXTRACTION
# ==========================================
with tab2:
    st.subheader("Stage 2: Resume Information Extraction")
    st.caption("Extracts important candidate details: Skills & technical tools, education & qualifications, work experience & project experience, certifications, and verified years of experience.")

    profile: CandidateProfile = st.session_state.candidate_profile

    if profile is None:
        if st.session_state.extracted_doc and st.session_state.extracted_doc.validation.is_valid:
            profile = get_parser().parse(st.session_state.extracted_doc)
            st.session_state.candidate_profile = profile
        else:
            st.warning("⚠️ No parsed resume available. Please upload a resume in Stage 1 first.")

    if profile is not None:
        # Candidate Header Card
        st.markdown(f"### 👤 {profile.name}")
        contact_items = []
        if profile.contact_info.get("email"):
            contact_items.append(f"📧 `{profile.contact_info['email']}`")
        if profile.contact_info.get("phone"):
            contact_items.append(f"📱 `{profile.contact_info['phone']}`")
        if profile.contact_info.get("linkedin"):
            contact_items.append(f"💼 [{profile.contact_info['linkedin']}]({profile.contact_info['linkedin']})")
        if profile.contact_info.get("github"):
            contact_items.append(f"🐙 [{profile.contact_info['github']}]({profile.contact_info['github']})")

        st.markdown(" • ".join(contact_items) if contact_items else "*No contact links detected*")
        st.markdown("---")

        # Overview Metrics Bar
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Verified Experience", f"{profile.total_years_exp} Yrs", help=profile.timeline.get("confidence", "Calculated"))
        m2.metric("Highest Degree", profile.highest_degree)
        m3.metric("Technical Skills", f"{len(profile.all_skills_list)} Skills")
        m4.metric("Roles & Projects", f"{len(profile.work_experience) + len(profile.projects)}")
        st.markdown("---")

        # Education Details
        with st.expander("🎓 View Full Education Details", expanded=False):
            for edu in profile.education:
                st.markdown(f"**{edu['degree']}** in *{edu['major']}*")
                st.caption(f"🏛️ {edu.get('institution') or 'University'} | 🗓️ {edu.get('graduation_year') or 'Year not specified'} | GPA: {edu.get('gpa') or 'N/A'}")

        # Skills Taxonomy Breakdown
        st.markdown(f"#### 🛠️ Skills & Technical Tools ({len(profile.all_skills_list)} Identified)")
        cat_skills = profile.skills.get("categorized", {})
        if cat_skills:
            for category, skills in cat_skills.items():
                st.markdown(f"**{category}:**")
                pills = " ".join([f'<span class="skill-pill skill-matched">{s}</span>' for s in skills])
                st.markdown(pills, unsafe_allow_html=True)
        else:
            st.write("No catalogued technical skills identified.")

        st.markdown("---")

        # Work Experience & Projects
        exp_col, proj_col = st.columns(2)
        with exp_col:
            st.markdown(f"#### 💼 Work & Internship Experience ({len(profile.work_experience)})")
            if profile.work_experience:
                for work in profile.work_experience:
                    with st.container():
                        # Role title
                        title = work.get("title", "")
                        if title and title != "Software Professional / Intern":
                            st.markdown(f"**{title}**")
                        else:
                            st.markdown(f"**Software Professional / Intern**")
                        # Company — only show when actually extracted from the resume
                        comp = work.get("company", "")
                        if comp and comp not in ("Company / Organization", "Organization / Company", ""):
                            st.markdown(f"🏢 **{comp}**")
                        # Dates
                        if work.get("dates") and work["dates"] != "Dates Not Specified":
                            st.caption(f"🗓️ {work['dates']}")
                        # Bullet points
                        for b in work.get("bullets", []):
                            st.markdown(f"- <small>{b}</small>", unsafe_allow_html=True)
                        st.markdown("")
            else:
                st.write("No structured work experience or internships detected.")

        with proj_col:
            st.markdown(f"#### 🚀 Project Experience ({len(profile.projects)} Projects)")
            if profile.projects:
                for proj in profile.projects:
                    with st.container():
                        # Project name only — extracted directly from resume
                        pname = proj.get("name", "")
                        if pname:
                            st.markdown(f"**🔹 {pname}**")
                        if proj.get("tech_stack"):
                            st.caption(f"🛠️ {proj['tech_stack']}")
                        for b in proj.get("bullets", []):
                            st.markdown(f"- <small>{b}</small>", unsafe_allow_html=True)
                        st.markdown("")
            else:
                st.write("No distinct project blocks detected.")

        # Certifications
        if profile.certifications:
            st.markdown("---")
            st.markdown(f"#### 📜 Verified Certifications ({len(profile.certifications)})")
            for cert in profile.certifications:
                st.markdown(f"• **{cert['name']}** — *{cert['issuer']}*")


# ==========================================
# STAGE 3: RESUME-JOB MATCHING ENGINE
# ==========================================
with tab3:
    st.subheader("Stage 3: Resume–Job Matching Engine")
    st.caption("Compares candidate profile against target job description: matches skills, identifies gaps, computes dense semantic similarity, generates an explainable overall score, and provides actionable LLM recommendations.")

    jd_input_col, action_col = st.columns([3, 1])
    with jd_input_col:
        st.session_state.jd_text = st.text_area(
            "Target Job Description (JD)",
            value=st.session_state.jd_text,
            height=200,
            placeholder="Paste complete Job Description here (Role, Responsibilities, Required Skills, Qualifications)..."
        )

    with action_col:
        st.markdown("#### Job Matching Actions")
        match_clicked = st.button("⚡ Run Matching Analysis", type="primary", use_container_width=True)

    if match_clicked:
        if not st.session_state.candidate_profile:
            st.warning("⚠️ Please upload and verify a resume in Stage 1 before running the matching engine.")
        elif not st.session_state.jd_text.strip():
            st.warning("⚠️ Please paste a Job Description before running the matching engine.")
        else:
            with st.spinner("Analyzing skill matrices, computing semantic similarity embeddings, and generating local LLM recommendations..."):
                jd_reqs = get_jd_parser().parse(st.session_state.jd_text)
                scoring_engine = get_scoring_engine()
                score_res = scoring_engine.evaluate_match(st.session_state.candidate_profile, jd_reqs)
                st.session_state.match_results = (jd_reqs, score_res)

                # Generate Stage 3 Personalized Recommendations (Local Ollama / HF Transformers)
                recommender = ResumeRecommender(llm_client)
                recs = recommender.generate_recommendations(
                    st.session_state.candidate_profile,
                    jd_reqs,
                    score_res
                )
                st.session_state.recommendations = recs

    if st.session_state.match_results:
        jd_reqs, score_res = st.session_state.match_results

        st.markdown("---")
        st.markdown(f"### 🎯 Evaluation for: **{jd_reqs.title}**")

        # Top Score Display (Gauge + Radar + Score Breakdown)
        g_col, r_col, b_col = st.columns([1.1, 1.2, 1.2])

        with g_col:
            gauge_fig = render_match_gauge(score_res.overall_score, title=score_res.tier)
            st.plotly_chart(gauge_fig, use_container_width=True)

        with r_col:
            radar_fig = render_radar_breakdown(
                score_res.skills_score,
                score_res.semantic_score,
                score_res.experience_score,
                score_res.education_score
            )
            st.plotly_chart(radar_fig, use_container_width=True)

        with b_col:
            bar_fig = render_score_bar_breakdown(score_res.weighted_contributions)
            st.plotly_chart(bar_fig, use_container_width=True)

        st.markdown("---")

        # Semantic Similarity Analysis
        st.markdown("#### 🧠 Semantic Similarity Analysis (Dense Neural Embeddings)")
        sem = score_res.semantic_report
        sim_score = sem.get("percentage", score_res.semantic_score)
        sim_engine = sem.get("engine", "Dense Embeddings")
        sim_conf = sem.get("confidence", "High")

        sem_col1, sem_col2 = st.columns([1, 2])
        with sem_col1:
            st.metric("Contextual Semantic Match", f"{sim_score}%", help="Calculated using local SentenceTransformers cosine similarity between full resume profile and job requirements.")
            st.caption(f"**Engine:** `{sim_engine}`")
            st.caption(f"**Confidence:** `{sim_conf}`")
        with sem_col2:
            st.info(
                f"**Semantic Alignment Interpretation:**\n\n"
                f"The candidate's project descriptions, responsibilities, and professional trajectory share a "
                f"**{sim_score}% contextual similarity** with the target role. "
                f"This captures nuanced phrasing and conceptual overlap beyond simple exact keyword matches."
            )

        st.markdown("---")

        # Detailed Skill Alignment Matrix
        st.markdown("#### 🔍 Skill Alignment & Gap Analysis")
        rep = score_res.skill_report

        s_col1, s_col2 = st.columns(2)
        with s_col1:
            st.markdown(f"**🟢 Matched Required Skills ({len(rep.matched_required_skills)})**")
            if rep.matched_required_skills:
                pills = " ".join([f'<span class="skill-pill skill-matched">✓ {s}</span>' for s in rep.matched_required_skills])
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.write("*None*")

            st.markdown(f"**🟡 Matched Preferred Skills ({len(rep.matched_preferred_skills)})**")
            if rep.matched_preferred_skills:
                pills = " ".join([f'<span class="skill-pill skill-preferred">✓ {s}</span>' for s in rep.matched_preferred_skills])
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.write("*None*")

        with s_col2:
            st.markdown(f"**🔴 Missing Required Skills ({len(rep.missing_required_skills)})**")
            if rep.missing_required_skills:
                pills = " ".join([f'<span class="skill-pill skill-missing">✗ {s}</span>' for s in rep.missing_required_skills])
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.success("🎉 All mandatory skills detected in resume!")

            st.markdown(f"**⚪ Missing / Unverified Preferred Skills ({len(rep.missing_preferred_skills)})**")
            if rep.missing_preferred_skills:
                pills = " ".join([f'<span class="skill-pill skill-missing">✗ {s}</span>' for s in rep.missing_preferred_skills])
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.write("*None*")

        if rep.candidate_additional_skills:
            st.markdown(f"**🔵 Candidate Additional Proficiencies ({len(rep.candidate_additional_skills)})**")
            pills = " ".join([f'<span class="skill-pill skill-extra">{s}</span>' for s in rep.candidate_additional_skills[:12]])
            st.markdown(pills, unsafe_allow_html=True)

        st.markdown("---")

        # Explainable Score Audit
        st.markdown("#### 📋 Explainable Score Breakdown & Audit")
        for exp in score_res.explanations:
            st.markdown(f"• {exp}")

        # Personalized Recommendations (Local LLM)
        if st.session_state.recommendations:
            recs = st.session_state.recommendations
            profile = st.session_state.candidate_profile

            st.markdown("---")
            st.markdown("### 🚀 Personalized AI Recommendations to Improve Resume")
            st.caption("Actionable recommendations powered by local LLM (Ollama / Hugging Face Transformers) to close skill gaps, elevate bullet impact, and improve ATS compliance.")

            # 1. Tailored Summary
            st.markdown("#### ✍️ Tailored Executive Pitch (Customized for Target JD)")
            st.markdown(f'<div class="metric-card"><i>"{recs["tailored_summary"]}"</i></div>', unsafe_allow_html=True)

            # 2. Bullet Point Rewrites
            st.markdown("#### 🌟 Google XYZ / STAR Bullet Point Rewrites")
            st.caption("Transform passive job descriptions into measurable, outcome-focused achievements: Accomplished [X], measured by [Y], by doing [Z].")

            for idx, b in enumerate(recs.get("bullet_enhancements", [])):
                with st.container():
                    st.markdown(f'<div class="rewrite-card">'
                                f'<div class="orig-label"><b>Original Bullet:</b> <i>"{b["original"]}"</i></div>'
                                f'<div class="enh-text">⭐ {b["improved"]}</div>'
                                f'<div class="critique-note"><b>Rationale:</b> {b["critique"]}</div>'
                                f'</div>', unsafe_allow_html=True)

            # 3. Missing Skills Strategy
            st.markdown("#### 🔑 Missing Skills Integration Strategy")
            st.caption("Actionable guidance on how to integrate crucial missing keywords legitimately into your experience.")

            for s_rec in recs.get("missing_skills_strategy", [])[:4]:
                with st.expander(f"Skill: {s_rec['skill']} — {s_rec['importance']}"):
                    st.markdown(f"**Strategy:** {s_rec['actionable_advice']}")
                    st.markdown(f"**Recommended Bullet Pattern:** `{s_rec['example_bullet']}`")

            # 4. ATS & Readability Audit
            st.markdown("#### 🤖 ATS & Formatting Health Check")
            ats = recs.get("ats_audit", {})
            a1, a2, a3, a4 = st.columns(4)
            a1.metric("ATS Health Score", f"{ats.get('ats_compatibility_score', 0)}/100")
            a2.metric("Total Word Count", ats.get("word_count", 0))
            a3.metric("Action Verbs Detected", ats.get("action_verb_count", 0))
            a4.metric("Quantifiable Metrics", ats.get("metrics_detected_count", 0))

            st.markdown("**Checklist Findings:**")
            for chk in ats.get("checks", []):
                st.markdown(f"• {chk}")

            # 5. Export Report
            st.markdown("#### 📥 Export Audit Report")
            pdf_bytes = ReportGenerator.generate_pdf_report(profile, jd_reqs, score_res, recs)

            st.download_button(
                label="📄 Download Comprehensive Audit Report (.pdf)",
                data=pdf_bytes,
                file_name=f"resume_match_report_{profile.name.replace(' ', '_').lower()}.pdf",
                mime="application/pdf"
            )

    elif not st.session_state.candidate_profile:
        st.info("Please upload a resume in Stage 1 before running the matching engine.")
    else:
        st.info("Paste a Job Description above and click 'Run Matching Analysis' to see match scores, semantic similarity, skill alignments, and personalized recommendations.")


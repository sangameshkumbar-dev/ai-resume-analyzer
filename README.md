# 🎯 AI Resume Analyzer & Job Matcher

> **Enterprise-grade, privacy-first Resume Intelligence & Job Matching Platform.**  
> Combines **Traditional NLP**, **Local Dense Semantic Similarity**, and **Local LLMs (Ollama / Hugging Face Transformers)**.  
> **100% Local Inference — Zero External LLM APIs — Corporate Safe — No LangChain.**

---

## 🏛️ System Architecture & 4-Stage Pipeline

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │                           Uploaded PDF Resume                          │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
  ▼ STAGE 1: Ingestion & Validation   │
  ┌───────────────────────────────────┴────────────────────────────────────┐
  │ • Magic Bytes & MIME Check (%PDF-)  • Size & Page Limits (100B - 10MB) │
  │ • Encryption Detection              • OCR / Scanned Text Verification  │
  │ • pdfplumber + pypdf Dual Engine    • Normalization & Verification UI  │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │ Verified Clean Text
  ▼ STAGE 2: Information Extraction   │
  ┌───────────────────────────────────┴────────────────────────────────────┐
  │ • Categorized Skills & Tools Taxonomy (Languages, Cloud, DBs, DevOps)  │
  │ • Education & Degree Level Detection (B.Tech, MS, Ph.D., GPA)          │
  │ • Work Experience & Projects Segmentation (Roles, Companies, Bullets)  │
  │ • Industry Certifications Catalog (AWS, Azure, GCP, CKA, PMP)          │
  │ • Algorithmic Date Interval Merging (Resolves Concurrent Overlaps)     │
  └─────────────────┬──────────────────────────────────────────────────────┘
                    │ Candidate Profile Data
  ▼ STAGE 3: Matching & Similarity    │ ◄── Job Description (Parsed)
  ┌───────────────────────────────────┴────────────────────────────────────┐
  │ • Exact & Canonical Skill Matching (Matched vs Missing vs Bonus)       │
  │ • Contextual Embeddings via HuggingFace `all-MiniLM-L6-v2` / TF-IDF    │
  │ • Explainable Scoring: Hard Skills (40%) + Semantic Fit (30%) +       │
  │   Experience Alignment (20%) + Education Credentials (10%)             │
  └─────────────────┬──────────────────────────────────────────────────────┘
                    │ Auditable Match Breakdown
  ▼ STAGE 4: Local LLM Recommendations│
  ┌───────────────────────────────────┴────────────────────────────────────┐
  │ • Local LLM: Ollama (REST API) / Hugging Face Transformers Local Model │
  │ • Google XYZ / STAR Bullet Point Rewriter                              │
  │ • High-Priority Missing Skill Integration Advice                       │
  │ • ATS Compatibility & Readability Audit (Action Verbs, Metrics)        │
  │ • Tailored Executive Summary & Downloadable Audit Report (.md)         │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Features

| Capability | Implementation | Why It Matters |
|---|---|---|
| **Privacy & Security** | Runs locally with Ollama / Hugging Face Transformers | No candidate PII or proprietary JD leaves the corporate network |
| **No Black-Box Scores** | Explainable multi-factor scoring formula | HR recruiters know exactly why points were awarded or deducted |
| **True Timeline Algebra** | Merges overlapping employment intervals | Prevents double-counting concurrent freelance or overlap jobs |
| **Layout-Aware PDF Extraction** | Dual engine (`pdfplumber` + `pypdf`) | Accurately parses multi-column and tabular resumes |
| **Semantic Matching** | SentenceTransformers (`all-MiniLM-L6-v2`) | Understands context beyond superficial keyword repetition |
| **Interactive Verification** | Real-time text verification area | Allows candidates to correct OCR or parsing flaws before scoring |

---

## 📁 Project Structure

```
ai-resume-analyzer/
├── .vscode/
│   ├── settings.json              # VS Code Python environment & test configuration
│   └── launch.json                # F5 debug launcher for Streamlit, Pytest & CLI
├── data/
│   ├── sample_resumes/            # Sample pre-built PDF resumes
│   │   ├── resume_senior_fullstack.pdf
│   │   └── resume_data_scientist.pdf
│   └── sample_jobs/               # Sample job descriptions
│       ├── senior_fullstack_engineer.txt
│       ├── machine_learning_engineer.txt
│       └── devops_platform_engineer.txt
├── src/
│   ├── config.py                  # Thresholds, scoring weights & endpoints
│   ├── stage1_ingestion/          # STAGE 1: PDF extraction, validation, verification
│   │   ├── validator.py           # File size, magic bytes, extractability
│   │   ├── extractor.py           # Dual-engine layout-aware text parser
│   │   └── models.py              # ValidationResult & ExtractedDocument schemas
│   ├── stage2_extraction/         # STAGE 2: Information extraction (NLP + Taxonomy)
│   │   ├── taxonomy.py            # Comprehensive tech skills & certs dictionary
│   │   ├── skill_extractor.py     # Regex boundary & n-gram matcher
│   │   ├── education_extractor.py # Degree, major, institution, graduation year
│   │   ├── experience_extractor.py# Roles, companies, dates, bullet items
│   │   ├── certification_extractor.py # Recognized industry credentials
│   │   ├── timeline_analyzer.py   # Overlap-resolving experience calculator
│   │   └── resume_parser.py       # Orchestrator producing CandidateProfile
│   ├── stage3_matching/           # STAGE 3: Resume-Job Matching & Semantic Engine
│   │   ├── jd_parser.py           # Requirements, skills, experience extraction
│   │   ├── skill_matcher.py       # Matched, missing, and bonus skills
│   │   ├── semantic_engine.py     # Local SentenceTransformers & TF-IDF
│   │   └── scoring_engine.py      # Transparent multi-factor scoring formula
│   ├── stage4_recommendations/    # STAGE 4: Local LLM Recommendations
│   │   ├── local_llm.py           # Ollama & Hugging Face client (NO LangChain)
│   │   ├── recommender.py         # Google XYZ rewrites, missing skill guide, ATS
│   │   └── report_generator.py    # Markdown report exporter
│   ├── ui/                        # Interactive Streamlit Web Dashboard
│   │   ├── app.py                 # 4-stage tabbed web application
│   │   └── components.py          # Plotly gauge, radar, and breakdown charts
│   └── utils/
│       ├── text_helpers.py        # Unicode cleaning, CID normalizer, regex
│       └── generate_sample_pdfs.py# Sample PDF builder
├── tests/                         # Pytest automated test suite (100% pass)
│   ├── test_stage1_validator.py
│   ├── test_stage2_extraction.py
│   ├── test_stage3_matching.py
│   └── test_stage4_llm.py
├── run_app.py                     # One-command runner (Streamlit or CLI)
├── requirements.txt
└── README.md
```

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.12)
- *(Optional for Stage 4)* **[Ollama](https://ollama.com/)** running locally (e.g., `ollama run llama3.2`)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🖥️ Running the Project

### Option A: Interactive Streamlit Web UI (Recommended)
Launch the interactive web application with one command:
```bash
python run_app.py
```
*Or directly via Streamlit:*
```bash
streamlit run src/ui/app.py
```
Open **`http://localhost:8501`** in your browser.

#### In the Web UI:
1. **Stage 1 Tab:** Upload any PDF resume or click **"Quick Load Sample Data"** in the sidebar. Verify the extracted text.
2. **Stage 2 Tab:** Review the candidate profile: skills categorized by domain, education, work experience, projects, and algorithmically calculated total experience.
3. **Stage 3 Tab:** Paste any target Job Description and click **"Run Matching Analysis"**. View the match gauge, radar chart, points breakdown, and matched vs missing skills.
4. **Stage 4 Tab:** Review Google XYZ/STAR bullet point rewrites, missing skill integration advice, ATS compatibility score, and click **"Download Comprehensive Audit Report"**.

---

### Option B: Command Line (CLI) Mode
Run an automated end-to-end evaluation in the terminal:
```bash
python run_app.py --cli
```

---

### Option C: VS Code Native Integration
1. Open the project folder in VS Code:
   `C:\Users\Sangamesh\.gemini\antigravity\scratch\ai-resume-analyzer`
2. Press **`F5`** or open the **Run & Debug** pane:
   - Select **"Launch AI Resume Analyzer (Streamlit)"** to debug the UI.
   - Select **"Run All Tests (Pytest)"** to run the test suite.
   - Select **"Run CLI Demo"** to run terminal mode.

---

## 🧪 Running Automated Tests

Run the full pytest suite:
```bash
python -m pytest tests/ -v
```

All 13 tests cover:
- Stage 1 PDF header validation, file size bounds, corruption checks.
- Stage 2 skill alias normalization, degree extraction, and date interval overlap merging.
- Stage 3 JD parsing, gap identification, dense embedding similarity, and scoring bounds.
- Stage 4 Local LLM fallback, Google XYZ bullet rewriting, and Markdown report generation.

---

## 🦙 Local LLM Options (Corporate Privacy)

The system is configured to prioritize local privacy:

1. **Ollama (Recommended for fast local generation):**
   - Install Ollama from [ollama.com](https://ollama.com/)
   - Pull a model: `ollama run llama3.2:3b` (or `mistral`, `phi3`, `qwen2.5`)
   - The analyzer automatically detects the local Ollama daemon at `http://127.0.0.1:11434`.

2. **Hugging Face Transformers (Direct in-memory Python inference):**
   - Select `huggingface` in the UI sidebar.
   - Uses local open models like `Qwen/Qwen2.5-0.5B-Instruct` or `TinyLlama-1.1B-Chat-v1.0`.

3. **Intelligent Offline Heuristic Fallback:**
   - If no local LLM is loaded or memory is limited on CPU, the system automatically falls back to an expert rule-based recommendation engine (STAR method rewriter, missing keyword integration templates, ATS optimization guidelines).
   - **Zero crashes, guaranteed operational stability.**

---

## 📊 Transparent Scoring Methodology

The overall match score (0 - 100%) is calculated transparently:

$$\text{Overall Score} = (0.40 \times S_{\text{skills}}) + (0.30 \times S_{\text{semantic}}) + (0.20 \times S_{\text{exp}}) + (0.10 \times S_{\text{edu}})$$

- **$S_{\text{skills}}$ (40% Weight):** Hard skills match ratio (Required skills carry 80% weight, Preferred skills carry 20%).
- **$S_{\text{semantic}}$ (30% Weight):** Dense neural embedding cosine similarity between resume experience & JD responsibilities.
- **$S_{\text{exp}}$ (20% Weight):** Ratio of verified total experience (overlapping employment merged) vs required years.
- **$S_{\text{edu}}$ (10% Weight):** Degree level alignment (Bachelors, Masters, Ph.D.).


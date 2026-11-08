"""
Configuration module for the AI Resume Analyzer & Job Matcher.
Centralizes constants, thresholds, weighting parameters, and local LLM endpoints.
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_RESUMES_DIR = DATA_DIR / "sample_resumes"
SAMPLE_JOBS_DIR = DATA_DIR / "sample_jobs"

# Ingestion / Validation Constraints
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB max resume size
MIN_FILE_SIZE_BYTES = 100               # 100 bytes min
ALLOWED_EXTENSIONS = {".pdf"}
MIN_EXTRACTED_CHAR_COUNT = 80          # Below this, flagged as potentially scanned/empty

# Scoring Weights (Must sum to 1.0)
# Combines transparent NLP extraction + semantic embeddings
WEIGHTS = {
    "skill_match": 0.40,       # 40% weight on hard technical & domain skill match
    "semantic_similarity": 0.30, # 30% weight on deep embedding similarity of profile vs JD
    "experience_alignment": 0.20, # 20% weight on years of verified experience vs required
    "education_alignment": 0.10,  # 10% weight on degree level match
}

# Semantic Similarity Settings
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast, highly performant HuggingFace local model (~80MB)
FALLBACK_TFIDF_NGRAMS = (1, 2)

# Local LLM Settings (Strictly Ollama or local HuggingFace Transformers, corporate-friendly, NO LangChain)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
DEFAULT_HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-0.5B-Instruct") # Lightweight CPU-friendly HF model
LLM_TIMEOUT_SECONDS = 45


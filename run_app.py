"""
Launcher script for AI Resume Analyzer & Job Matcher.
Supports interactive Streamlit UI or headless CLI execution.
Usage:
    python run_app.py            # Starts Streamlit UI
    python run_app.py --cli      # Runs automated demo on sample data
"""
import sys
import argparse
from pathlib import Path

# Fix Windows console UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run_cli_demo():
    from src.stage1_ingestion.extractor import PDFResumeExtractor
    from src.stage2_extraction.resume_parser import ResumeParser
    from src.stage3_matching.jd_parser import JobDescriptionParser
    from src.stage3_matching.scoring_engine import ScoringEngine
    from src.stage4_recommendations.local_llm import LocalLLMClient
    from src.stage4_recommendations.recommender import ResumeRecommender
    from src.stage4_recommendations.report_generator import ReportGenerator
    from src.config import SAMPLE_RESUMES_DIR, SAMPLE_JOBS_DIR

    print("\n" + "="*70)
    print("🚀 RUNNING AI RESUME ANALYZER & JOB MATCHER (CLI MODE)")
    print("="*70)

    # 1. Ingestion
    sample_pdf = SAMPLE_RESUMES_DIR / "resume_senior_fullstack.pdf"
    print(f"\n[Stage 1] Ingesting & Validating PDF: {sample_pdf.name}")
    extractor = PDFResumeExtractor()
    doc = extractor.extract_from_path(sample_pdf)
    print(f"  ✓ Validation: {doc.validation.quality_badge}")
    print(f"  ✓ Pages: {doc.validation.page_count} | Size: {doc.validation.file_size_kb} KB | Words: {doc.validation.word_count}")

    # 2. Information Extraction
    print("\n[Stage 2] Extracting Candidate Profile (Traditional NLP & Taxonomy)...")
    parser = ResumeParser()
    profile = parser.parse(doc)
    print(f"  ✓ Candidate Name: {profile.name}")
    print(f"  ✓ Verified Experience: {profile.total_years_exp} Years ({profile.timeline.get('confidence')})")
    print(f"  ✓ Highest Degree: {profile.highest_degree}")
    print(f"  ✓ Extracted Skills ({len(profile.all_skills_list)}): {', '.join(profile.all_skills_list[:8])}...")

    # 3. Matching Engine
    sample_jd_path = SAMPLE_JOBS_DIR / "senior_fullstack_engineer.txt"
    print(f"\n[Stage 3] Comparing Against Job Description: {sample_jd_path.name}...")
    with open(sample_jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read()

    jd_parser = JobDescriptionParser()
    jd_reqs = jd_parser.parse(jd_text)
    scoring_engine = ScoringEngine()
    score_res = scoring_engine.evaluate_match(profile, jd_reqs)

    print(f"\n  🎯 OVERALL MATCH SCORE: {score_res.overall_score}% ({score_res.tier})")
    print(f"     - Technical Skills: {score_res.skills_score}% (Weight: 40% -> +{score_res.weighted_contributions['skills']} pts)")
    print(f"     - Semantic Similarity: {score_res.semantic_score}% (Weight: 30% -> +{score_res.weighted_contributions['semantic']} pts)")
    print(f"     - Experience Alignment: {score_res.experience_score}% (Weight: 20% -> +{score_res.weighted_contributions['experience']} pts)")
    print(f"     - Education Alignment: {score_res.education_score}% (Weight: 10% -> +{score_res.weighted_contributions['education']} pts)")

    print(f"\n  🔍 Matched Skills ({len(score_res.skill_report.all_matched)}): {', '.join(score_res.skill_report.all_matched)}")
    print(f"  ❌ Missing Required Skills: {', '.join(score_res.skill_report.missing_required_skills) or 'None'}")

    # 4. Recommendations
    print("\n[Stage 4] Generating Local AI Recommendations & Enhancements...")
    llm_client = LocalLLMClient(provider="auto")
    recommender = ResumeRecommender(llm_client)
    recs = recommender.generate_recommendations(profile, jd_reqs, score_res)

    print(f"\n  ✍️ Tailored Summary:\n     \"{recs['tailored_summary']}\"")
    print(f"\n  ⭐ Sample Enhanced Bullet (Google XYZ Format):")
    if recs["bullet_enhancements"]:
        enh = recs["bullet_enhancements"][0]
        print(f"     Original: {enh['original']}")
        print(f"     Improved: {enh['improved']}")

    print("\n" + "="*70)
    print("✅ ANALYSIS COMPLETE! Launch with 'python run_app.py' to explore interactive UI.")
    print("="*70 + "\n")


def run_streamlit():
    import subprocess
    app_path = PROJECT_ROOT / "src" / "ui" / "app.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    subprocess.run(cmd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Resume Analyzer & Job Matcher")
    parser.add_argument("--cli", action="store_true", help="Run in terminal CLI mode without browser UI")
    args = parser.parse_args()

    if args.cli:
        run_cli_demo()
    else:
        run_streamlit()

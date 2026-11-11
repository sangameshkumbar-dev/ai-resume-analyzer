"""
Unit tests for Stage 4: Local LLM Recommendations and Reports.
"""
from src.stage4_recommendations.local_llm import LocalLLMClient
from src.stage4_recommendations.recommender import ResumeRecommender
from src.stage4_recommendations.report_generator import ReportGenerator
from src.stage2_extraction.resume_parser import CandidateProfile
from src.stage3_matching.jd_parser import JobDescriptionParser
from src.stage3_matching.scoring_engine import ScoringEngine


def test_local_llm_fallback_operational():
    # Force fallback mode to verify zero dependency on external daemon
    client = LocalLLMClient(provider="fallback")
    resp = client.generate("Rewrite this bullet point: worked on python backend")
    assert resp is not None
    assert len(resp) > 20
    assert any(term in resp for term in ["STAR", "Redesigned", "Spearheaded", "Engineered", "backend"])


def test_recommender_generates_suite():
    client = LocalLLMClient(provider="fallback")
    recommender = ResumeRecommender(client)
    jd_parser = JobDescriptionParser()
    scoring_engine = ScoringEngine()

    jd_reqs = jd_parser.parse("Software Engineer. Requirements: Python, React, Docker, AWS, PostgreSQL. 3+ years exp.")
    profile = CandidateProfile(
        name="Sam Sample",
        contact_info={"email": "sam@example.com"},
        skills={"all_skills": ["Python", "React"]},
        education=[{"degree": "Bachelor's Degree", "major": "Computer Science", "level": 3}],
        work_experience=[{
            "title": "Software Developer",
            "company": "Tech Corp",
            "dates": "Jan 2021 - Present",
            "bullets": ["Maintained backend services and wrote SQL queries for team."]
        }],
        projects=[],
        certifications=[],
        timeline={"total_years": 3.2},
        raw_text="Maintained backend services and wrote SQL queries for team. Python, React."
    )

    score_res = scoring_engine.evaluate_match(profile, jd_reqs)
    recs = recommender.generate_recommendations(profile, jd_reqs, score_res)

    assert "missing_skills_strategy" in recs
    assert "bullet_enhancements" in recs
    assert "ats_audit" in recs
    assert "tailored_summary" in recs

    # Test report generator (Markdown & PDF)
    report_md = ReportGenerator.generate_markdown_report(profile, jd_reqs, score_res, recs)
    assert "# 🎯 AI Resume & Job Match Audit Report" in report_md
    assert "Sam Sample" in report_md

    report_pdf = ReportGenerator.generate_pdf_report(profile, jd_reqs, score_res, recs)
    assert isinstance(report_pdf, bytes)
    assert len(report_pdf) > 1000
    assert report_pdf.startswith(b"%PDF")


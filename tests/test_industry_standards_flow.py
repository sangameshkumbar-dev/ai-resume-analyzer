"""
Comprehensive Industry Standards & End-to-End Flow Verification Suite.
Validates all 4 pipeline stages, boundary conditions, edge cases, error resilience,
and UI visualization components against corporate enterprise standards.
"""
import io
import pytest
from datetime import datetime
from pathlib import Path

# Stage 1
from src.stage1_ingestion.validator import ResumeValidator
from src.stage1_ingestion.extractor import PDFResumeExtractor
from src.stage1_ingestion.models import ValidationResult, ExtractedDocument
from src.utils.text_helpers import normalize_text, extract_contact_info, clean_bullet_points

# Stage 2
from src.stage2_extraction.taxonomy import SKILL_TAXONOMY, SKILL_ALIASES, RECOGNIZED_CERTIFICATIONS
from src.stage2_extraction.skill_extractor import SkillExtractor
from src.stage2_extraction.education_extractor import EducationExtractor
from src.stage2_extraction.experience_extractor import ExperienceExtractor
from src.stage2_extraction.certification_extractor import CertificationExtractor
from src.stage2_extraction.timeline_analyzer import TimelineAnalyzer
from src.stage2_extraction.resume_parser import ResumeParser, CandidateProfile

# Stage 3
from src.stage3_matching.jd_parser import JobDescriptionParser, JobRequirements
from src.stage3_matching.skill_matcher import SkillMatcher, SkillMatchReport
from src.stage3_matching.semantic_engine import SemanticSimilarityEngine
from src.stage3_matching.scoring_engine import ScoringEngine, MatchScoreBreakdown

# Stage 4
from src.stage4_recommendations.local_llm import LocalLLMClient
from src.stage4_recommendations.recommender import ResumeRecommender
from src.stage4_recommendations.report_generator import ReportGenerator

# UI
from src.ui.components import render_match_gauge, render_radar_breakdown, render_score_bar_breakdown

from src.config import SAMPLE_RESUMES_DIR, SAMPLE_JOBS_DIR


# ==============================================================================
# 1. FULL END-TO-END FLOW TESTS ON REAL DATASETS
# ==============================================================================
def test_e2e_fullstack_pipeline():
    """Verify complete end-to-end execution on Senior Fullstack sample."""
    sample_pdf = SAMPLE_RESUMES_DIR / "resume_senior_fullstack.pdf"
    sample_jd = SAMPLE_JOBS_DIR / "senior_fullstack_engineer.txt"
    assert sample_pdf.exists() and sample_jd.exists()

    # Stage 1: Ingestion
    extractor = PDFResumeExtractor()
    doc = extractor.extract_from_path(sample_pdf)
    assert doc.validation.is_valid
    assert doc.validation.word_count > 150
    assert "Alex Mercer" in doc.normalized_text

    # Stage 2: Information Extraction
    parser = ResumeParser()
    profile = parser.parse(doc)
    assert profile.name == "Alex Mercer"
    assert profile.total_years_exp >= 7.0
    assert "Bachelor" in profile.highest_degree
    assert len(profile.all_skills_list) >= 15
    assert "Python" in profile.all_skills_list
    assert "FastAPI" in profile.all_skills_list

    # Stage 3: Matching & Scoring
    jd_parser = JobDescriptionParser()
    with open(sample_jd, "r", encoding="utf-8") as f:
        jd_text = f.read()
    jd_reqs = jd_parser.parse(jd_text)
    scoring = ScoringEngine()
    score_breakdown = scoring.evaluate_match(profile, jd_reqs)

    assert 0.0 <= score_breakdown.overall_score <= 100.0
    assert score_breakdown.overall_score >= 70.0  # High match
    assert len(score_breakdown.skill_report.matched_required_skills) >= 5
    assert len(score_breakdown.explanations) == 4

    # Stage 4: Recommendations & Audit Report
    recommender = ResumeRecommender(LocalLLMClient(provider="fallback"))
    recs = recommender.generate_recommendations(profile, jd_reqs, score_breakdown)
    assert len(recs["missing_skills_strategy"]) >= 1
    assert len(recs["bullet_enhancements"]) >= 1
    assert recs["ats_audit"]["ats_compatibility_score"] >= 60

    report_md = ReportGenerator.generate_markdown_report(profile, jd_reqs, score_breakdown, recs)
    assert f"# 🎯 AI Resume & Job Match Audit Report" in report_md
    assert "Alex Mercer" in report_md
    assert f"{score_breakdown.overall_score}%" in report_md


def test_e2e_data_scientist_pipeline():
    """Verify complete end-to-end execution on Data Scientist / ML sample."""
    sample_pdf = SAMPLE_RESUMES_DIR / "resume_data_scientist.pdf"
    sample_jd = SAMPLE_JOBS_DIR / "machine_learning_engineer.txt"
    assert sample_pdf.exists() and sample_jd.exists()

    extractor = PDFResumeExtractor()
    doc = extractor.extract_from_path(sample_pdf)
    assert doc.validation.is_valid

    parser = ResumeParser()
    profile = parser.parse(doc)
    assert "Elena" in profile.name or "Rostova" in profile.name
    assert "Master" in profile.highest_degree
    assert any(s in profile.all_skills_list for s in ["PyTorch", "TensorFlow", "Machine Learning"])

    jd_parser = JobDescriptionParser()
    with open(sample_jd, "r", encoding="utf-8") as f:
        jd_reqs = jd_parser.parse(f.read())
    scoring = ScoringEngine()
    score = scoring.evaluate_match(profile, jd_reqs)

    assert score.overall_score >= 65.0
    assert score.education_score == 100.0  # Master's satisfies Master's/Bachelor's


# ==============================================================================
# 2. STAGE 1: INGESTION, VALIDATION & TEXT HELPER ROBUSTNESS
# ==============================================================================
def test_validator_file_size_and_type_guards():
    # 1. Non-PDF extension
    res = ResumeValidator.validate_bytes(b"%PDF-1.4 Fake", "document.docx")
    assert not res.is_valid
    assert any("Only PDF files are supported" in e for e in res.errors)

    # 2. Too small
    res = ResumeValidator.validate_bytes(b"%PDF-1.4", "short.pdf")
    assert not res.is_valid
    assert any("too small" in e for e in res.errors)

    # 3. Missing magic byte
    res = ResumeValidator.validate_bytes(b"INVALID_HEADER" + b" " * 150, "fake.pdf")
    assert not res.is_valid
    assert any("missing %PDF-" in e for e in res.errors)

    # 4. Non-existent file path
    res = ResumeValidator.validate_file_path("non_existent_resume_file_xyz.pdf")
    assert not res.is_valid
    assert any("does not exist" in e for e in res.errors)


def test_text_normalization_and_contact_extraction():
    # Ligatures, special bullets, dashes, non-breaking spaces
    raw_text = (
        "John Doe\n"
        "Email: john.doe@enterprise.com | Phone: +1 (555) 234-5678\n"
        "LinkedIn: linkedin.com/in/johndoe-tech | GitHub: github.com/johndoe\n"
        "\ufb01rst \ufb02oat (cid:127) Architected microservices \u2013 high performance\n"
        "“Quotes” and ‘single’ with\u00A0non-breaking\r\nspaces."
    )
    normalized = normalize_text(raw_text)
    assert "first float" in normalized
    assert "• Architected microservices" in normalized
    assert '"Quotes"' in normalized
    assert "'single'" in normalized
    assert "\u00A0" not in normalized

    contact = extract_contact_info(raw_text)
    assert contact["email"] == "john.doe@enterprise.com"
    assert "555" in contact["phone"]
    assert contact["linkedin"] == "https://linkedin.com/in/johndoe-tech"
    assert contact["github"] == "https://github.com/johndoe"


def test_clean_bullet_points():
    raw_bullets = [
        "• Developed high-throughput REST APIs using FastAPI and PostgreSQL.",
        "- Short",  # Under 15 chars, must be pruned
        "   ",     # Empty, must be pruned
        "> Automated deployment pipeline using GitHub Actions and Docker containers."
    ]
    cleaned = clean_bullet_points(raw_bullets)
    assert len(cleaned) == 2
    assert cleaned[0].startswith("Developed")
    assert cleaned[1].startswith("Automated")


# ==============================================================================
# 3. STAGE 2: TAXONOMY, EDUCATION & TIMELINE ALGEBRA
# ==============================================================================
def test_skill_extractor_normalization_and_boundaries():
    extractor = SkillExtractor()
    # Punctuation/symbol skills: C++, C#, .NET, Node.js, k8s alias
    text = "We use C++, C#, k8s, nodejs, postgres, and Docker. Not Cloud or Good."
    res = extractor.extract_skills(text)
    skills = res["all_skills"]

    assert "C++" in skills
    assert "C#" in skills
    assert "Kubernetes" in skills   # Normalized from k8s
    assert "Node.js" in skills      # Normalized from nodejs
    assert "PostgreSQL" in skills   # Normalized from postgres
    assert "Docker" in skills
    # Ensure "C" is not falsely matched inside "Cloud"
    assert "C" not in skills


def test_timeline_analyzer_advanced_interval_merging():
    """Test overlapping concurrent roles, comma date formats, and present dates."""
    analyzer = TimelineAnalyzer(reference_year=2026)
    
    # 3 overlapping jobs:
    # Job 1: Jan 2020 - Dec 2022 (36 mos)
    # Job 2 (concurrent freelance): Jun 2021 - Jun 2022 (12 mos, totally inside Job 1)
    # Job 3: Jan, 2023 - Present (Jan 2023 - Jan 2026 = 36 mos)
    # Total merged: 36 mos + 36 mos = 72 months = 6.0 years (not 84 mos / 7.0 yrs!)
    sample_text = (
        "Role 1: Jan 2020 - Dec 2022\n"
        "Role 2: Jun 2021 - Jun 2022\n"
        "Role 3: Jan, 2023 - Present\n"
    )
    res = analyzer.calculate_total_experience(sample_text)
    assert res["detected_intervals_count"] == 3
    assert res["merged_intervals_count"] == 2
    assert 5.8 <= res["total_years"] <= 6.2
    assert res["confidence"] == "Calculated (Timeline Intervals)"


def test_education_extractor_degrees_and_majors():
    extractor = EducationExtractor()
    sample_text = (
        "EDUCATION\n"
        "Doctor of Philosophy in Artificial Intelligence, MIT, 2024\n"
        "Master of Science in Cybersecurity, Stanford University, 2020\n"
        "Bachelor of Technology in Electronics Engineering, IIT, 2018\n"
    )
    entries = extractor.extract_education(sample_text)
    assert len(entries) == 3
    assert entries[0]["degree"] == "Ph.D."
    assert entries[0]["level"] == 5
    assert entries[1]["degree"] == "Master's Degree"
    assert entries[1]["level"] == 4
    assert entries[2]["degree"] == "Bachelor's Degree"
    assert entries[2]["level"] == 3


def test_experience_and_project_separation():
    extractor = ExperienceExtractor()
    sample_text = (
        "PROFESSIONAL EXPERIENCE\n"
        "Senior Software Engineer\n"
        "Acme Corp | Jan 2021 - Present\n"
        "• Architected distributed backend services processing 1M events daily.\n"
        "• Mentored junior engineers and improved test coverage to 92%.\n\n"
        "PROJECTS\n"
        "1. AI Resume Scanner (Python, PyTorch)\n"
        "• Built automated document parsing engine reducing review time by 60%.\n"
        "2. Cloud Infrastructure Monitor | Terraform, AWS\n"
        "• Deployed serverless monitoring stack with Prometheus alerts.\n"
    )
    data = extractor.extract_experience(sample_text)
    work = data["work_experience"]
    projs = data["projects"]

    assert len(work) >= 1
    assert "Senior Software Engineer" in work[0]["title"]
    assert len(work[0]["bullets"]) >= 2

    assert len(projs) >= 2
    proj_names = [p["name"] for p in projs]
    assert any("AI Resume Scanner" in name for name in proj_names)
    assert any("Cloud Infrastructure Monitor" in name for name in proj_names)


# ==============================================================================
# 4. STAGE 3: MATCHING, SCORING & MATHEMATICAL INVARIANTS
# ==============================================================================
def test_skill_matcher_comprehensive():
    matcher = SkillMatcher()
    jd = JobRequirements(
        title="DevOps Engineer",
        required_skills=["Docker", "Kubernetes", "AWS", "Terraform"],
        preferred_skills=["Prometheus", "Grafana", "Python"],
        min_years_experience=4.0,
        required_degree_level=3,
        required_degree_name="Bachelor's Degree"
    )
    # Candidate has all required, 1 preferred, plus 2 extra
    profile = CandidateProfile(
        name="Candidate A",
        contact_info={},
        skills={"all_skills": ["Docker", "Kubernetes", "AWS", "Terraform", "Python", "Go", "Redis"]},
        education=[],
        work_experience=[],
        projects=[],
        certifications=[],
        timeline={"total_years": 5.0},
        raw_text=""
    )
    report = matcher.match(profile, jd)
    assert len(report.matched_required_skills) == 4
    assert len(report.missing_required_skills) == 0
    assert "Python" in report.matched_preferred_skills
    assert "Prometheus" in report.missing_preferred_skills
    assert "Grafana" in report.missing_preferred_skills
    assert "Go" in report.candidate_additional_skills
    assert "Redis" in report.candidate_additional_skills
    # 100% of required (80 pts) + 1/3 of preferred (33.3% * 20 = 6.7 pts) = ~86.7%
    assert 85.0 <= report.match_percentage <= 88.0


def test_scoring_engine_mathematical_bounds():
    """Verify that score contributions accurately sum to overall score and bounds hold."""
    scoring = ScoringEngine()

    # Case A: Minimal candidate (0 matching skills, 0 exp)
    min_profile = CandidateProfile(
        name="Beginner",
        contact_info={},
        skills={"all_skills": []},
        education=[],
        work_experience=[],
        projects=[],
        certifications=[],
        timeline={"total_years": 0.0},
        raw_text="Hello world minimal text"
    )
    strict_jd = JobRequirements(
        title="Principal Architect",
        required_skills=["C++", "Rust", "System Design", "Microservices"],
        preferred_skills=["Kubernetes", "Distributed Systems"],
        min_years_experience=10.0,
        required_degree_level=4,
        required_degree_name="Master's Degree",
        raw_text="Principal Architect with 10+ years experience in C++, Rust, and Distributed Systems."
    )
    res_min = scoring.evaluate_match(min_profile, strict_jd)
    assert 0.0 <= res_min.overall_score <= 100.0
    assert res_min.overall_score < 40.0
    assert "Low Alignment" in res_min.tier

    # Verify score equation: sum of weighted contributions equals overall score
    contributions_sum = round(sum(res_min.weighted_contributions.values()), 1)
    assert abs(contributions_sum - res_min.overall_score) <= 0.2

    # Case B: Zero required skills in JD (Graceful fallback)
    empty_jd = JobRequirements(
        title="General Role",
        required_skills=[],
        preferred_skills=[],
        min_years_experience=0.0,
        required_degree_level=1,
        required_degree_name="High School",
        raw_text="General role description."
    )
    res_empty = scoring.evaluate_match(min_profile, empty_jd)
    assert 0.0 <= res_empty.overall_score <= 100.0


# ==============================================================================
# 5. STAGE 4: LOCAL LLM, ATS AUDIT & REPORT GENERATION
# ==============================================================================
def test_recommender_and_ats_audit_flow():
    client = LocalLLMClient(provider="fallback")
    recommender = ResumeRecommender(client)
    scoring = ScoringEngine()

    jd = JobRequirements(
        title="Senior Full Stack Engineer",
        required_skills=["Python", "React", "PostgreSQL", "Docker", "AWS"],
        preferred_skills=["Redis", "CI/CD"],
        min_years_experience=5.0,
        required_degree_level=3,
        required_degree_name="Bachelor's Degree",
        raw_text="Full stack engineer role."
    )
    profile = CandidateProfile(
        name="Morgan Lee",
        contact_info={"email": "morgan@example.com"},
        skills={"all_skills": ["Python", "PostgreSQL"]},
        education=[{"degree": "Bachelor's Degree", "major": "Computer Science", "level": 3}],
        work_experience=[{
            "title": "Full Stack Developer",
            "company": "Apex Solutions",
            "dates": "Jan 2021 - Dec 2023",
            "bullets": [
                "Responsible for writing Python scripts and updating database records.",
                "Worked with the product team on bug fixes and website improvements."
            ]
        }],
        projects=[],
        certifications=[],
        timeline={"total_years": 3.0},
        raw_text="Responsible for writing Python scripts and updating database records. Worked with the team. Achieved 25% increase."
    )
    score_breakdown = scoring.evaluate_match(profile, jd)
    recs = recommender.generate_recommendations(profile, jd, score_breakdown)

    # Missing skills strategy must include missing required skills: React, Docker, AWS
    missing_skills_advised = [r["skill"] for r in recs["missing_skills_strategy"]]
    assert any(s in missing_skills_advised for s in ["React", "Docker", "AWS"])

    # Bullet enhancements
    assert len(recs["bullet_enhancements"]) >= 1
    for enh in recs["bullet_enhancements"]:
        assert "original" in enh and "improved" in enh
        assert enh["improved"].startswith("•")

    # ATS audit
    ats = recs["ats_audit"]
    assert 0 <= ats["ats_compatibility_score"] <= 100
    assert ats["word_count"] > 0
    assert "checks" in ats

    # Markdown Report Generation
    report = ReportGenerator.generate_markdown_report(profile, jd, score_breakdown, recs)
    assert "Morgan Lee" in report
    assert "Senior Full Stack Engineer" in report
    assert "Match Score Breakdown" in report
    assert "Skill Alignment & Gap Analysis" in report


# ==============================================================================
# 6. UI PLOTLY COMPONENTS VERIFICATION
# ==============================================================================
def test_ui_components_generate_valid_figures():
    # 1. Gauge indicator
    fig_gauge = render_match_gauge(85.5, title="Exceptional Match")
    assert fig_gauge is not None
    assert fig_gauge.data[0].type == "indicator"
    assert fig_gauge.data[0].value == 85.5

    # 2. Radar breakdown
    fig_radar = render_radar_breakdown(90.0, 75.0, 80.0, 100.0)
    assert fig_radar is not None
    assert fig_radar.data[0].type == "scatterpolar"
    # Closed polygon (5 points for 4 categories)
    assert len(fig_radar.data[0].r) == 5

    # 3. Bar breakdown
    contributions = {"skills": 32.0, "semantic": 24.0, "experience": 20.0, "education": 10.0}
    fig_bar = render_score_bar_breakdown(contributions)
    assert fig_bar is not None
    assert len(fig_bar.data) == 2  # Earned vs Unearned bars


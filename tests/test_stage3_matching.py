"""
Unit tests for Stage 3: Resume-Job Matching & Semantic Similarity.
"""
from src.stage3_matching.jd_parser import JobDescriptionParser
from src.stage3_matching.skill_matcher import SkillMatcher
from src.stage3_matching.semantic_engine import SemanticSimilarityEngine
from src.stage3_matching.scoring_engine import ScoringEngine
from src.stage2_extraction.resume_parser import CandidateProfile


def test_jd_parser_extracts_requirements():
    parser = JobDescriptionParser()
    sample_jd = (
        "Senior Backend Engineer\n"
        "Requirements:\n"
        "• Minimum 5+ years of experience in software development\n"
        "• Hands-on proficiency in Python, FastAPI, and PostgreSQL\n"
        "• Docker and AWS cloud experience\n"
        "Preferred Qualifications:\n"
        "• Familiarity with Kubernetes and Redis\n"
        "Education: Bachelor's degree in Computer Science\n"
    )
    reqs = parser.parse(sample_jd)

    assert "Senior" in reqs.title or "Backend" in reqs.title
    assert reqs.min_years_experience == 5.0
    assert "Python" in reqs.required_skills
    assert "FastAPI" in reqs.required_skills
    assert "PostgreSQL" in reqs.required_skills


def test_skill_matcher_and_gap_identification():
    matcher = SkillMatcher()
    jd_parser = JobDescriptionParser()
    sample_jd = (
        "Role: Full Stack Engineer\n"
        "Required: Python, React, PostgreSQL, Docker\n"
        "Preferred: Kubernetes, Redis"
    )
    jd_reqs = jd_parser.parse(sample_jd)

    profile = CandidateProfile(
        name="Test Dev",
        contact_info={},
        skills={"all_skills": ["Python", "React", "MongoDB"]},  # Missing PostgreSQL, Docker, Kubernetes, Redis
        education=[],
        work_experience=[],
        projects=[],
        certifications=[],
        timeline={"total_years": 4.0},
        raw_text=""
    )

    report = matcher.match(profile, jd_reqs)
    assert "Python" in report.matched_required_skills
    assert "React" in report.matched_required_skills
    assert "PostgreSQL" in report.missing_required_skills
    assert "Docker" in report.missing_required_skills
    assert report.match_percentage < 100.0


def test_semantic_similarity_engine():
    engine = SemanticSimilarityEngine()
    text_a = "Senior Software Engineer building scalable microservices in Python and cloud APIs."
    text_b = "Backend developer role responsible for Python microservices and cloud systems."
    res = engine.compute_similarity(text_a, text_b)

    assert res["percentage"] > 40.0
    assert res["similarity_score"] > 0.4


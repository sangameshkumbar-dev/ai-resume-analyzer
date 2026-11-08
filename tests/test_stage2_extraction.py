"""
Unit tests for Stage 2: Resume Information Extraction Pipeline.
"""
from datetime import datetime
from src.stage2_extraction.skill_extractor import SkillExtractor
from src.stage2_extraction.education_extractor import EducationExtractor
from src.stage2_extraction.timeline_analyzer import TimelineAnalyzer
from src.stage2_extraction.certification_extractor import CertificationExtractor
from src.stage2_extraction.resume_parser import ResumeParser
from src.stage1_ingestion.models import ExtractedDocument, ValidationResult


def test_skill_extractor_handles_aliases_and_symbols():
    extractor = SkillExtractor()
    sample_text = (
        "Experienced in Python, C++, React.js, and k8s. "
        "Also used postgres and AWS Lambda for microservices."
    )
    res = extractor.extract_skills(sample_text)
    skills = res["all_skills"]

    assert "Python" in skills
    assert "C++" in skills
    assert "React" in skills          # Normalized from React.js
    assert "Kubernetes" in skills     # Normalized from k8s
    assert "PostgreSQL" in skills     # Normalized from postgres
    assert "AWS Lambda" in skills


def test_education_extractor():
    extractor = EducationExtractor()
    sample_text = (
        "EDUCATION\n"
        "Master of Science in Data Science and Artificial Intelligence\n"
        "Columbia University, 2020. GPA: 3.9/4.0\n"
        "Bachelor of Science in Computer Science, 2018\n"
    )
    entries = extractor.extract_education(sample_text)
    assert len(entries) >= 2
    assert entries[0]["degree"] == "Master's Degree"
    assert "Data Science" in entries[0]["major"]
    assert entries[0]["graduation_year"] == "2020"


def test_timeline_analyzer_merges_overlapping_intervals():
    analyzer = TimelineAnalyzer(reference_year=2024)
    # Job 1: Jan 2020 to Jan 2022 (24 mos)
    # Job 2: Jul 2021 to Jun 2022 (12 mos - overlaps Job 1)
    # Merged span: Jan 2020 to Jun 2022 = 30 months = ~2.5 years (not 36 mos / 3.0 yrs!)
    sample_text = "Job A: Jan 2020 - Jan 2022\nJob B: Jul 2021 - Jun 2022"
    res = analyzer.calculate_total_experience(sample_text)

    assert res["detected_intervals_count"] == 2
    assert res["merged_intervals_count"] == 1  # Overlap collapsed
    assert 2.3 <= res["total_years"] <= 2.6


def test_certification_extractor():
    extractor = CertificationExtractor()
    text = "Certifications: AWS Certified Solutions Architect, CKA, and CompTIA Security+"
    certs = extractor.extract_certifications(text)
    names = [c["name"] for c in certs]

    assert any("AWS Certified Solutions Architect" in n for n in names)
    assert any("CKA" in n for n in names)


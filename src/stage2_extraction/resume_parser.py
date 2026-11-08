"""
Unified Resume Information Extraction Pipeline.
Orchestrates Skill, Education, Experience, Certification, and Timeline extractors
into a structured CandidateProfile.
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from src.stage1_ingestion.models import ExtractedDocument
from src.stage2_extraction.skill_extractor import SkillExtractor
from src.stage2_extraction.education_extractor import EducationExtractor
from src.stage2_extraction.experience_extractor import ExperienceExtractor
from src.stage2_extraction.certification_extractor import CertificationExtractor
from src.stage2_extraction.timeline_analyzer import TimelineAnalyzer
from src.utils.text_helpers import extract_contact_info


@dataclass
class CandidateProfile:
    """Structured representation of extracted candidate resume data."""
    name: str
    contact_info: Dict[str, Optional[str]]
    skills: Dict[str, Any]
    education: List[Dict[str, Any]]
    work_experience: List[Dict[str, Any]]
    projects: List[Dict[str, Any]]
    certifications: List[Dict[str, Any]]
    timeline: Dict[str, Any]
    raw_text: str
    summary: str = ""

    @property
    def total_years_exp(self) -> float:
        return self.timeline.get("total_years", 0.0)

    @property
    def highest_degree(self) -> str:
        if self.education:
            return self.education[0].get("degree", "Not Specified")
        return "Not Specified"

    @property
    def all_skills_list(self) -> List[str]:
        return self.skills.get("all_skills", [])


class ResumeParser:
    """End-to-end information extraction pipeline combining NLP rules, regex, and taxonomies."""

    def __init__(self):
        self.skill_extractor = SkillExtractor()
        self.education_extractor = EducationExtractor()
        self.experience_extractor = ExperienceExtractor()
        self.certification_extractor = CertificationExtractor()
        self.timeline_analyzer = TimelineAnalyzer()

    def parse(self, document: ExtractedDocument) -> CandidateProfile:
        """Parse ExtractedDocument into CandidateProfile."""
        text = document.normalized_text

        # 1. Candidate Name Detection (Top lines heuristic)
        name = self._extract_candidate_name(text)

        # 2. Contact Information
        contact = extract_contact_info(text)

        # 3. Skills & Technical Tools
        skills = self.skill_extractor.extract_skills(text)

        # 4. Education & Qualifications
        education = self.education_extractor.extract_education(text)

        # 5. Work & Project Experience
        exp_data = self.experience_extractor.extract_experience(text)

        # 6. Certifications
        certifications = self.certification_extractor.extract_certifications(text)

        # 7. Algorithmic Experience Calculation (using full text & experience sections)
        timeline = self.timeline_analyzer.calculate_total_experience(
            exp_data.get("raw_experience_text") or text
        )

        # 8. Executive Summary / Objective snippet
        summary = self._extract_summary(text)

        return CandidateProfile(
            name=name,
            contact_info=contact,
            skills=skills,
            education=education,
            work_experience=exp_data.get("work_experience", []),
            projects=exp_data.get("projects", []),
            certifications=certifications,
            timeline=timeline,
            raw_text=text,
            summary=summary
        )

    def _extract_candidate_name(self, text: str) -> str:
        """Extract candidate name from first few lines of resume."""
        lines = [line.strip() for line in text.splitlines()[:8] if line.strip()]
        for line in lines:
            # Check for name-like pattern (2-4 words, capitalized, no punctuation/numbers/email)
            if re.match(r'^[A-Z][a-zA-Z\.\'\-]+(?:\s+[A-Z][a-zA-Z\.\'\-]+){1,3}$', line):
                # Filter out obvious false positives like "RESUME", "CURRICULUM VITAE", "SUMMARY"
                if not any(k in line.upper() for k in ["RESUME", "CV", "PROFILE", "SUMMARY", "EXPERIENCE", "ENGINEER", "DEVELOPER"]):
                    return line
        return "Candidate"

    def _extract_summary(self, text: str) -> str:
        """Extract professional summary or objective statement if present."""
        match = re.search(
            r'^(?:SUMMARY|PROFESSIONAL SUMMARY|EXECUTIVE SUMMARY|OBJECTIVE|ABOUT ME)\b(.*?)(?=\n[A-Z\s]{4,}|\Z)',
            text, re.IGNORECASE | re.MULTILINE | re.DOTALL
        )
        if match:
            raw_summary = match.group(1).strip()
            # Return first 300 chars
            return " ".join(raw_summary.split()[:50])
        return ""


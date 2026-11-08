"""
Job Description (JD) Parsing Engine.
Extracts required skills, preferred qualifications, experience expectations, and education prerequisites.
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from src.stage2_extraction.skill_extractor import SkillExtractor
from src.stage2_extraction.education_extractor import DEGREE_PATTERNS
from src.utils.text_helpers import normalize_text


@dataclass
class JobRequirements:
    """Structured representation of parsed job description."""
    title: str
    required_skills: List[str]
    preferred_skills: List[str]
    min_years_experience: float
    required_degree_level: int  # 1 to 5 scale matching DEGREE_PATTERNS
    required_degree_name: str
    key_responsibilities: List[str] = field(default_factory=list)
    raw_text: str = ""

    @property
    def all_target_skills(self) -> List[str]:
        # Deduplicated combination of required and preferred
        seen = set(self.required_skills)
        res = list(self.required_skills)
        for s in self.preferred_skills:
            if s not in seen:
                seen.add(s)
                res.append(s)
        return res


class JobDescriptionParser:
    """Extracts requirements, skills, and expectations from raw JD text."""

    def __init__(self):
        self.skill_extractor = SkillExtractor()

    def parse(self, jd_text: str) -> JobRequirements:
        """Parse raw job description text."""
        clean_jd = normalize_text(jd_text)

        # 1. Job Title Heuristic
        title = self._extract_job_title(clean_jd)

        # 2. Extract Skills (split into Required vs Preferred if sections present)
        req_skills, pref_skills = self._extract_categorized_skills(clean_jd)

        # 3. Minimum Years of Experience
        min_years = self._extract_experience_requirement(clean_jd)

        # 4. Education / Degree Requirement
        deg_level, deg_name = self._extract_education_requirement(clean_jd)

        # 5. Key Responsibilities
        responsibilities = self._extract_responsibilities(clean_jd)

        return JobRequirements(
            title=title,
            required_skills=req_skills,
            preferred_skills=pref_skills,
            min_years_experience=min_years,
            required_degree_level=deg_level,
            required_degree_name=deg_name,
            key_responsibilities=responsibilities,
            raw_text=clean_jd
        )

    def _extract_job_title(self, text: str) -> str:
        """Extract job title from header line or common title patterns."""
        lines = [line.strip() for line in text.splitlines()[:6] if line.strip()]
        for line in lines:
            if any(term in line.lower() for term in ["engineer", "developer", "architect", "scientist", "manager", "lead", "analyst"]):
                if len(line) <= 60 and not line.lower().startswith(("about", "company", "description")):
                    return line
        return "Target Position"

    def _extract_categorized_skills(self, text: str) -> tuple[List[str], List[str]]:
        """Identify required skills vs nice-to-have / preferred skills."""
        # Check for Preferred / Bonus sections
        pref_pat = re.compile(
            r'(?:preferred qualifications|nice to have|bonus points|preferred skills|plus if you have|preferred:?)\b(.*?)(?=\n[A-Z\s]{4,}|\Z)',
            re.IGNORECASE | re.DOTALL
        )
        pref_match = pref_pat.search(text)
        pref_text = pref_match.group(1) if pref_match else ""

        # Check for explicit Required section
        req_pat = re.compile(
            r'(?:required qualifications|requirements|required skills|must have|required:?)\b(.*?)(?=(?:preferred qualifications|nice to have|bonus|preferred:?|\n[A-Z\s]{4,}|\Z))',
            re.IGNORECASE | re.DOTALL
        )
        req_match = req_pat.search(text)
        req_text = req_match.group(1) if req_match else ""

        all_extracted = self.skill_extractor.extract_skills(text)
        all_skills = all_extracted["all_skills"]

        pref_extracted = self.skill_extractor.extract_skills(pref_text)
        pref_skills = pref_extracted["all_skills"]

        if req_text:
            req_extracted = self.skill_extractor.extract_skills(req_text)
            req_skills = req_extracted["all_skills"]
            # Deduplicate against preferred
            pref_set = set(pref_skills)
            req_skills = [s for s in req_skills if s not in pref_set]
            return req_skills, pref_skills

        # Required skills are all detected skills excluding pure preferred ones
        pref_set = set(pref_skills)
        req_skills = [s for s in all_skills if s not in pref_set]

        # If no explicit preferred section was found, treat top 70% as required, 30% as preferred
        if not pref_skills and len(all_skills) > 4:
            split_idx = int(len(all_skills) * 0.75)
            req_skills = all_skills[:split_idx]
            pref_skills = all_skills[split_idx:]

        return req_skills, pref_skills

    def _extract_experience_requirement(self, text: str) -> float:
        """Extract required years of experience (e.g., '5+ years', '3-5 years', 'minimum 4 years')."""
        patterns = [
            r'(?:minimum|at least)?\s*(\d{1,2})\+?\s*(?:-\s*\d{1,2})?\s*(?:years|yrs)\s+(?:of\s+)?(?:experience|exp)',
            r'(\d{1,2})\+?\s*(?:years|yrs)\s+(?:of\s+)?(?:hands-on|industry|relevant)?\s*experience',
            r'(?:experience|background):\s*(\d{1,2})\+?\s*years'
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                return float(match.group(1))

        # Check for seniority indicators
        if re.search(r'\b(?:Principal|Staff|Lead)\b', text, re.I):
            return 7.0
        elif re.search(r'\bSenior\b', text, re.I):
            return 5.0
        elif re.search(r'\b(?:Mid-level|Intermediate)\b', text, re.I):
            return 3.0
        elif re.search(r'\b(?:Junior|Entry-level|Associate)\b', text, re.I):
            return 1.0

        return 2.0  # Default general assumption

    def _extract_education_requirement(self, text: str) -> tuple[int, str]:
        """Detect minimum required education level."""
        for pat, deg_name, lvl in DEGREE_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                return lvl, deg_name
        return 3, "Bachelor's Degree (Standard)"

    def _extract_responsibilities(self, text: str) -> List[str]:
        """Extract bullet points or responsibility statements."""
        resp_pat = re.compile(
            r'(?:responsibilities|what you\'ll do|duties|the role)\b(.*?)(?=\n[A-Z\s]{4,}|\Z)',
            re.IGNORECASE | re.DOTALL
        )
        match = resp_pat.search(text)
        if match:
            lines = match.group(1).splitlines()
            bullets = [l.strip(" •-*>\t") for l in lines if len(l.strip()) >= 20]
            return bullets[:8]
        return []

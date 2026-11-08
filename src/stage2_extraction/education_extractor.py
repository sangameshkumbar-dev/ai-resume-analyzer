"""
Education and Qualifications Extraction Engine.
Extracts degrees, majors, institutions, graduation years, and GPAs using pattern matching.
"""
import re
from typing import List, Dict, Any, Optional

DEGREE_PATTERNS = [
    # Ph.D / Doctorate
    (r'\b(Ph\.?D\.?|Doctor of Philosophy|Doctorate)\b', "Ph.D.", 5),
    # Master's
    (r'\b(M\.?S\.?|M\.?Sc\.?|Master of Science|M\.?Tech\.?|Master of Technology|M\.?Eng\.?|M\.?B\.?A\.?|Master of Business Administration|Masters?)\b', "Master's Degree", 4),
    # Bachelor's
    (r'\b(B\.?S\.?|B\.?Sc\.?|Bachelor of Science|B\.?Tech\.?|Bachelor of Technology|B\.?E\.?|Bachelor of Engineering|B\.?A\.?|Bachelor of Arts|Bachelors?)\b', "Bachelor's Degree", 3),
    # Associate's
    (r'\b(Associate(?:\'s)?\s*(?:Degree|of Science|of Arts)?|A\.?S\.?|A\.?A\.?)\b', "Associate Degree", 2),
    # High School / Diploma
    (r'\b(High School Diploma|Secondary School|GED|Diploma)\b', "Diploma / High School", 1),
]

MAJOR_PATTERNS = [
    r'Computer Science(?: and Engineering)?',
    r'Software Engineering',
    r'Data Science(?: and Analytics)?',
    r'Artificial Intelligence',
    r'Machine Learning',
    r'Information Technology',
    r'Information Systems',
    r'Electrical Engineering',
    r'Computer Engineering',
    r'Mathematics(?: and Statistics)?',
    r'Statistics',
    r'Physics',
    r'Mechanical Engineering',
    r'Business Administration',
    r'Finance',
    r'Cybersecurity'
]

INSTITUTION_KEYWORDS = [
    r'[A-Z][A-Za-z\s,\.]+(?:University|College|Institute of Technology|Polytechnic|Academy|School of [A-Za-z]+)'
]


class EducationExtractor:
    """Parses education details from resume text."""

    def extract_education(self, text: str) -> List[Dict[str, Any]]:
        """Extract structured education entries."""
        if not text:
            return []

        # Find education section if present, or scan whole text
        edu_section = self._isolate_education_section(text)
        target_text = edu_section if len(edu_section) > 50 else text

        entries: List[Dict[str, Any]] = []
        lines = [line.strip() for line in target_text.splitlines() if line.strip()]

        # Scan line by line and in 2-3 line sliding windows
        for i, line in enumerate(lines):
            # Check for degree mention
            matched_degree = None
            degree_level = 0
            for pat, deg_name, lvl in DEGREE_PATTERNS:
                if re.search(pat, line, re.IGNORECASE):
                    matched_degree = deg_name
                    degree_level = lvl
                    break

            if matched_degree:
                # First check current line for major, then fallback to context block
                context_block = " ".join(lines[max(0, i - 1): min(len(lines), i + 2)])

                # Extract Major
                major = None
                for m_pat in MAJOR_PATTERNS:
                    m_match = re.search(rf'\b({m_pat})\b', line, re.IGNORECASE)
                    if m_match:
                        major = m_match.group(1).title()
                        break
                if not major:
                    for m_pat in MAJOR_PATTERNS:
                        m_match = re.search(rf'\b({m_pat})\b', context_block, re.IGNORECASE)
                        if m_match:
                            major = m_match.group(1).title()
                            break

                # Extract Year
                year_match = re.search(r'\b(19\d{2}|20\d{2})\b', context_block)
                grad_year = year_match.group(1) if year_match else None

                # Extract GPA / CGPA
                gpa_match = re.search(r'\b(?:GPA|CGPA)[:\s]+([0-9]\.[0-9]{1,2}(?:\s*/\s*[0-9]\.?[0-9]*)?)\b', context_block, re.IGNORECASE)
                gpa = gpa_match.group(1) if gpa_match else None

                # Extract Institution
                institution = self._find_institution(context_block)

                entry = {
                    "degree": matched_degree,
                    "level": degree_level,
                    "major": major or "Computer Science / General STEM",
                    "institution": institution,
                    "graduation_year": grad_year,
                    "gpa": gpa,
                    "raw_context": line
                }

                # Avoid duplicate degrees from same block
                if not any(e["degree"] == matched_degree and e.get("graduation_year") == grad_year for e in entries):
                    entries.append(entry)

        # Sort entries by degree level descending
        entries.sort(key=lambda x: x["level"], reverse=True)
        return entries

    def _isolate_education_section(self, text: str) -> str:
        """Heuristically isolate the EDUCATION section from the resume."""
        header_pat = re.compile(
            r'^(?:EDUCATION|ACADEMIC BACKGROUND|ACADEMICS|EDUCATIONAL QUALIFICATIONS)',
            re.IGNORECASE | re.MULTILINE
        )
        match = header_pat.search(text)
        if not match:
            return ""

        start = match.start()
        # Look for the next major section header
        next_header_pat = re.compile(
            r'^(?:EXPERIENCE|WORK EXPERIENCE|PROFESSIONAL EXPERIENCE|SKILLS|PROJECTS|CERTIFICATIONS|PUBLICATIONS)\b',
            re.IGNORECASE | re.MULTILINE
        )
        next_match = next_header_pat.search(text[match.end():])
        if next_match:
            end = match.end() + next_match.start()
            return text[start:end]
        return text[start:start + 1200]

    def _find_institution(self, block: str) -> Optional[str]:
        for inst_pat in INSTITUTION_KEYWORDS:
            m = re.search(inst_pat, block)
            if m:
                inst_str = m.group(0).strip(" ,.-")
                # Filter out absurdly long fragments
                if len(inst_str) <= 80:
                    return inst_str
        return None

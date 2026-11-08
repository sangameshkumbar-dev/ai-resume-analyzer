"""
Text processing helpers, regex patterns, and string normalization utilities.
"""
import re
import unicodedata
from typing import List, Optional, Tuple

# Regex Patterns for contact info
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
PHONE_REGEX = re.compile(
    r'(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?|(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}'
)
LINKEDIN_REGEX = re.compile(r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/([A-Za-z0-9_-]+)', re.IGNORECASE)
GITHUB_REGEX = re.compile(r'(?:https?:\/\/)?(?:www\.)?github\.com\/([A-Za-z0-9_-]+)', re.IGNORECASE)


def normalize_text(text: str) -> str:
    """Normalize unicode characters, remove weird ligatures, standardize bullets and spacing."""
    if not text:
        return ""
    # Normalize unicode (NFKD decomposes ligatures like \ufb01 -> fi)
    text = unicodedata.normalize("NFKD", text)
    # Remove PDF CID font mapping artifacts (e.g., (cid:127) -> bullet)
    text = re.sub(r'\(cid:\d+\)', '•', text)
    # Standardize bullet points
    text = re.sub(r'[\u2022\u2023\u25E6\u2043\u2219\u25AA\u25CF\u25BA\u27A2\uF0B7]', '\n• ', text)
    # Normalize dash variants
    text = re.sub(r'[\u2012\u2013\u2014\u2015]', '-', text)
    # Normalize quotes
    text = re.sub(r'[\u2018\u2019]', "'", text)
    text = re.sub(r'[\u201C\u201D]', '"', text)
    # Replace non-breaking spaces with normal spaces
    text = text.replace('\u00A0', ' ')
    # Replace carriage returns
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Collapse multiple consecutive empty lines to maximum 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Collapse multiple inline spaces
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()


def extract_contact_info(text: str) -> dict:
    """Extract email, phone, LinkedIn, and GitHub links from resume text."""
    emails = EMAIL_REGEX.findall(text)
    primary_email = emails[0] if emails else None

    # LinkedIn
    linkedin_match = LINKEDIN_REGEX.search(text)
    linkedin_url = f"https://linkedin.com/in/{linkedin_match.group(1)}" if linkedin_match else None

    # GitHub
    github_match = GITHUB_REGEX.search(text)
    github_url = f"https://github.com/{github_match.group(1)}" if github_match else None

    # Phone
    phone = None
    # Look for phone patterns, filter out pure year ranges or fake numbers
    for line in text.splitlines()[:20]:  # Usually in first 20 lines
        matches = re.finditer(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', line)
        for m in matches:
            candidate = m.group(0).strip()
            # Must have at least 10 digits
            digits = re.sub(r'\D', '', candidate)
            if 10 <= len(digits) <= 15:
                phone = candidate
                break
        if phone:
            break

    return {
        "email": primary_email,
        "phone": phone,
        "linkedin": linkedin_url,
        "github": github_url
    }


def clean_bullet_points(bullets: List[str]) -> List[str]:
    """Clean and filter meaningful bullet points from raw extracted list."""
    cleaned = []
    for b in bullets:
        b_clean = b.strip()
        # Remove leading bullet symbols
        b_clean = re.sub(r'^[•\-\*\>]\s*', '', b_clean)
        # Filter out trivial fragments (less than 15 chars)
        if len(b_clean) >= 15:
            cleaned.append(b_clean)
    return cleaned

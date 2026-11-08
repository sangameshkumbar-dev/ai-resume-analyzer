"""
Certification and Credential Extraction Engine.
Matches against recognized industry credentials and parses dedicated certification sections.
"""
import re
from typing import List, Dict, Any, Set
from src.stage2_extraction.taxonomy import RECOGNIZED_CERTIFICATIONS


class CertificationExtractor:
    """Extracts industry certifications and credentials from resumes."""

    def __init__(self):
        self.cert_catalog = RECOGNIZED_CERTIFICATIONS
        # Precompile regex for fast lookup
        self.compiled_certs = [
            (cert, re.compile(rf'(?<![a-zA-Z0-9_]){re.escape(cert)}(?![a-zA-Z0-9_])', re.IGNORECASE))
            for cert in self.cert_catalog
        ]

    def extract_certifications(self, text: str) -> List[Dict[str, Any]]:
        """Extract all verified certifications."""
        if not text:
            return []

        found_certs: List[Dict[str, Any]] = []
        seen_names: Set[str] = set()

        # 1. Match against known catalog
        for cert_name, pattern in self.compiled_certs:
            if pattern.search(text):
                # Canonical name mapping
                canon_name = cert_name
                # Avoid duplicates for acronyms (e.g., CKA vs Certified Kubernetes Administrator)
                if "Kubernetes Administrator" in canon_name or canon_name == "CKA":
                    canon_name = "CKA (Certified Kubernetes Administrator)"
                elif "Solutions Architect" in canon_name:
                    canon_name = "AWS Certified Solutions Architect"
                elif "Azure Fundamentals" in canon_name:
                    canon_name = "Microsoft Certified: Azure Fundamentals"

                if canon_name not in seen_names:
                    seen_names.add(canon_name)
                    found_certs.append({
                        "name": canon_name,
                        "type": "Industry Recognized Credential",
                        "issuer": self._guess_issuer(canon_name)
                    })

        # 2. Parse dedicated CERTIFICATIONS section for any custom or proprietary credentials
        custom_certs = self._parse_custom_cert_section(text, seen_names)
        found_certs.extend(custom_certs)

        return found_certs

    def _guess_issuer(self, name: str) -> str:
        name_l = name.lower()
        if "aws" in name_l or "amazon" in name_l:
            return "Amazon Web Services"
        elif "azure" in name_l or "microsoft" in name_l:
            return "Microsoft"
        elif "google" in name_l or "gcp" in name_l:
            return "Google Cloud"
        elif "kubernetes" in name_l or "cka" in name_l or "ckad" in name_l:
            return "Cloud Native Computing Foundation (CNCF)"
        elif "pmp" in name_l or "project management" in name_l:
            return "Project Management Institute (PMI)"
        elif "comptia" in name_l:
            return "CompTIA"
        elif "hashicorp" in name_l or "terraform" in name_l:
            return "HashiCorp"
        return "Professional Organization"

    def _parse_custom_cert_section(self, text: str, seen: Set[str]) -> List[Dict[str, Any]]:
        """Find lines in a dedicated CERTIFICATIONS section that might be other credentials."""
        section_pat = re.compile(
            r'^(?:CERTIFICATIONS|LICENSES & CERTIFICATIONS|CREDENTIALS|CERTIFICATES)\b',
            re.IGNORECASE | re.MULTILINE
        )
        match = section_pat.search(text)
        if not match:
            return []

        start = match.end()
        end_pat = re.compile(
            r'^(?:EXPERIENCE|EDUCATION|SKILLS|PROJECTS|PUBLICATIONS|AWARDS)\b',
            re.IGNORECASE | re.MULTILINE
        )
        next_m = end_pat.search(text[start:])
        end = start + next_m.start() if next_m else start + 800

        custom_entries = []
        for line in text[start:end].splitlines():
            line_s = line.strip(" •-*>\t")
            if 10 <= len(line_s) <= 80 and not line_s.endswith(":"):
                # Avoid headers or already detected certs
                if not any(s.lower() in line_s.lower() for s in seen):
                    seen.add(line_s)
                    custom_entries.append({
                        "name": line_s,
                        "type": "General Certificate",
                        "issuer": "Verified Institution"
                    })
        return custom_entries


"""
Skill and Technical Tool Extraction Engine using N-gram matching, regex boundary guards,
and canonical taxonomy normalization.
"""
import re
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict

from src.stage2_extraction.taxonomy import SKILL_TAXONOMY, SKILL_ALIASES


class SkillExtractor:
    """Extracts, normalizes, and categorizes technical skills and tools from unstructured text."""

    def __init__(self):
        # Build lookup table: lowercase term -> (Canonical Name, Category)
        self.term_to_canonical: Dict[str, Tuple[str, str]] = {}
        self.all_patterns = []

        for category, skills in SKILL_TAXONOMY.items():
            for skill in skills:
                canon = skill
                self.term_to_canonical[skill.lower()] = (canon, category)

        # Include Aliases
        for alias, canon in SKILL_ALIASES.items():
            # Find category of canonical skill
            category = "Other Tools"
            for cat, skills in SKILL_TAXONOMY.items():
                if canon in skills:
                    category = cat
                    break
            self.term_to_canonical[alias.lower()] = (canon, category)

        # Precompile regex for multi-character and special symbol skills
        # Sort by length descending to match longest phrase first (e.g., "AWS Lambda" before "AWS")
        sorted_terms = sorted(self.term_to_canonical.keys(), key=lambda x: len(x), reverse=True)
        self.compiled_rules = []
        for term in sorted_terms:
            # Safe boundary check supporting punctuation like C++, C#, .NET, Node.js
            escaped = re.escape(term)
            pattern = re.compile(rf'(?<![a-zA-Z0-9_]){escaped}(?![a-zA-Z0-9_])', re.IGNORECASE)
            self.compiled_rules.append((pattern, term))

    def extract_skills(self, text: str) -> Dict[str, Any]:
        """Extract skills from text, deduplicate, and group by category."""
        if not text:
            return {"categorized": {}, "all_skills": [], "skill_counts": {}}

        found_canonical: Set[str] = set()
        skill_counts: Dict[str, int] = defaultdict(int)
        categorized: Dict[str, List[str]] = defaultdict(list)

        for pattern, term in self.compiled_rules:
            matches = pattern.findall(text)
            if matches:
                canon_name, category = self.term_to_canonical[term]
                if canon_name not in found_canonical:
                    found_canonical.add(canon_name)
                    categorized[category].append(canon_name)
                skill_counts[canon_name] += len(matches)

        # Sort skills in each category
        for cat in categorized:
            categorized[cat] = sorted(categorized[cat])

        return {
            "categorized": dict(categorized),
            "all_skills": sorted(list(found_canonical)),
            "skill_counts": dict(skill_counts),
            "total_count": len(found_canonical)
        }

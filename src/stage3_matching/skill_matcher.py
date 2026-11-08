"""
Skill Matching Engine.
Compares candidate skills against job description requirements,
identifying matched, partially matched, and missing/unverified skills.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Set, Any
from src.stage2_extraction.resume_parser import CandidateProfile
from src.stage3_matching.jd_parser import JobRequirements


@dataclass
class SkillMatchReport:
    """Detailed report on skill alignment between Candidate and Job."""
    matched_required_skills: List[str]
    matched_preferred_skills: List[str]
    missing_required_skills: List[str]
    missing_preferred_skills: List[str]
    candidate_additional_skills: List[str]
    match_percentage: float
    total_target_skills_count: int
    matched_count: int

    @property
    def all_matched(self) -> List[str]:
        return self.matched_required_skills + self.matched_preferred_skills

    @property
    def all_missing(self) -> List[str]:
        return self.missing_required_skills + self.missing_preferred_skills


class SkillMatcher:
    """Performs set and fuzzy matching between candidate profile and JD."""

    def match(self, profile: CandidateProfile, jd: JobRequirements) -> SkillMatchReport:
        candidate_skills = set(s.lower() for s in profile.all_skills_list)
        # Create map from lowercase to original casing for display
        cand_map = {s.lower(): s for s in profile.all_skills_list}

        # Match Required Skills
        matched_req = []
        missing_req = []
        for s in jd.required_skills:
            if s.lower() in candidate_skills:
                matched_req.append(cand_map.get(s.lower(), s))
            else:
                missing_req.append(s)

        # Match Preferred Skills
        matched_pref = []
        missing_pref = []
        for s in jd.preferred_skills:
            if s.lower() in candidate_skills:
                matched_pref.append(cand_map.get(s.lower(), s))
            else:
                missing_pref.append(s)

        # Candidate Extra Skills (skills candidate has that weren't in JD)
        jd_all_lower = set(s.lower() for s in jd.all_target_skills)
        candidate_extras = [
            cand_map[s_low] for s_low in candidate_skills if s_low not in jd_all_lower
        ]

        # Calculate Weighted Match Score
        # Required skills carry 80% weight, Preferred skills carry 20%
        req_total = len(jd.required_skills)
        pref_total = len(jd.preferred_skills)

        req_score = (len(matched_req) / req_total) if req_total > 0 else 1.0
        pref_score = (len(matched_pref) / pref_total) if pref_total > 0 else 1.0

        if req_total > 0 and pref_total > 0:
            weighted_pct = (req_score * 0.80 + pref_score * 0.20) * 100.0
        elif req_total > 0:
            weighted_pct = req_score * 100.0
        elif pref_total > 0:
            weighted_pct = pref_score * 100.0
        else:
            weighted_pct = 70.0  # Default neutral

        return SkillMatchReport(
            matched_required_skills=sorted(matched_req),
            matched_preferred_skills=sorted(matched_pref),
            missing_required_skills=sorted(missing_req),
            missing_preferred_skills=sorted(missing_pref),
            candidate_additional_skills=sorted(candidate_extras),
            match_percentage=round(weighted_pct, 1),
            total_target_skills_count=req_total + pref_total,
            matched_count=len(matched_req) + len(matched_pref)
        )


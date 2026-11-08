"""
Explainable Multi-Factor Scoring Engine.
Combines traditional NLP skill extraction, neural semantic similarity,
experience timeline verification, and education credentials into a transparent match score.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any
from src.config import WEIGHTS
from src.stage2_extraction.resume_parser import CandidateProfile
from src.stage3_matching.jd_parser import JobRequirements
from src.stage3_matching.skill_matcher import SkillMatcher, SkillMatchReport
from src.stage3_matching.semantic_engine import SemanticSimilarityEngine


@dataclass
class MatchScoreBreakdown:
    """Detailed score breakdown with explainable components."""
    overall_score: float
    tier: str
    skills_score: float
    semantic_score: float
    experience_score: float
    education_score: float
    weights: Dict[str, float]
    weighted_contributions: Dict[str, float]
    explanations: List[str]
    skill_report: SkillMatchReport
    semantic_report: Dict[str, Any]


class ScoringEngine:
    """Computes an auditable, deterministic match score between candidate and JD."""

    def __init__(self, weights: Dict[str, float] = WEIGHTS):
        self.weights = weights
        self.skill_matcher = SkillMatcher()
        self.semantic_engine = SemanticSimilarityEngine()

    def evaluate_match(
        self,
        profile: CandidateProfile,
        jd: JobRequirements
    ) -> MatchScoreBreakdown:
        """Run complete matching pipeline and return explainable score breakdown."""
        # 1. Skill Matching
        skill_report = self.skill_matcher.match(profile, jd)
        s_skills = skill_report.match_percentage

        # 2. Semantic Similarity
        # Compare candidate work experience + projects vs JD responsibilities + text
        cand_rich_text = f"{profile.summary}\n{' '.join(profile.all_skills_list)}\n{profile.raw_text}"
        semantic_report = self.semantic_engine.compute_similarity(cand_rich_text, jd.raw_text)
        s_semantic = semantic_report["percentage"]

        # 3. Experience Alignment
        cand_years = profile.total_years_exp
        req_years = jd.min_years_experience
        if req_years <= 0:
            s_exp = 100.0
        elif cand_years >= req_years:
            s_exp = 100.0
        else:
            s_exp = max(20.0, round((cand_years / req_years) * 100.0, 1))

        # 4. Education Alignment
        highest_level = 0
        if profile.education:
            highest_level = profile.education[0].get("level", 0)

        req_level = jd.required_degree_level
        if highest_level >= req_level:
            s_edu = 100.0
        elif highest_level == req_level - 1:
            s_edu = 75.0
        elif highest_level > 0:
            s_edu = 50.0
        else:
            s_edu = 35.0

        # 5. Composite Weighted Score
        w_skills = self.weights["skill_match"]
        w_semantic = self.weights["semantic_similarity"]
        w_exp = self.weights["experience_alignment"]
        w_edu = self.weights["education_alignment"]

        c_skills = round(s_skills * w_skills, 2)
        c_semantic = round(s_semantic * w_semantic, 2)
        c_exp = round(s_exp * w_exp, 2)
        c_edu = round(s_edu * w_edu, 2)

        overall = round(c_skills + c_semantic + c_exp + c_edu, 1)

        # 6. Determine Tier
        if overall >= 85.0:
            tier = "Exceptional Match (Top-Tier Fit)"
        elif overall >= 72.0:
            tier = "Strong Competitive Match"
        elif overall >= 55.0:
            tier = "Moderate Match (Gaps to Address)"
        else:
            tier = "Low Alignment (Significant Gaps)"

        # 7. Generate Plain-English Explanations
        explanations = []
        # Skills explanation
        explanations.append(
            f"Skills Match ({c_skills}/{round(w_skills*100, 1)} pts): Candidate matched "
            f"{len(skill_report.matched_required_skills)} of {len(jd.required_skills)} required technical skills. "
            f"Missing required skills: {', '.join(skill_report.missing_required_skills[:4]) or 'None'}."
        )
        # Semantic explanation
        explanations.append(
            f"Semantic Context ({c_semantic}/{round(w_semantic*100, 1)} pts): Embeddings measured {s_semantic}% "
            f"conceptual alignment between resume project/work descriptions and the job requirements using {semantic_report['engine']}."
        )
        # Experience explanation
        if cand_years >= req_years:
            explanations.append(
                f"Experience ({c_exp}/{round(w_exp*100, 1)} pts): Candidate verified experience of {cand_years} years "
                f"meets/exceeds the required {req_years} years."
            )
        else:
            explanations.append(
                f"Experience ({c_exp}/{round(w_exp*100, 1)} pts): Candidate has {cand_years} verified years, "
                f"which is below the target requirement of {req_years} years."
            )
        # Education explanation
        cand_deg_name = profile.highest_degree
        if highest_level >= req_level:
            explanations.append(
                f"Education ({c_edu}/{round(w_edu*100, 1)} pts): Candidate holds {cand_deg_name}, "
                f"satisfying the required {jd.required_degree_name}."
            )
        else:
            explanations.append(
                f"Education ({c_edu}/{round(w_edu*100, 1)} pts): Candidate holds {cand_deg_name}, "
                f"while the target role requests {jd.required_degree_name}."
            )

        return MatchScoreBreakdown(
            overall_score=overall,
            tier=tier,
            skills_score=round(s_skills, 1),
            semantic_score=round(s_semantic, 1),
            experience_score=round(s_exp, 1),
            education_score=round(s_edu, 1),
            weights=self.weights,
            weighted_contributions={
                "skills": c_skills,
                "semantic": c_semantic,
                "experience": c_exp,
                "education": c_edu
            },
            explanations=explanations,
            skill_report=skill_report,
            semantic_report=semantic_report
        )


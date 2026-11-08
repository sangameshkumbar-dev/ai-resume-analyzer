"""
Personalized Resume Enhancement and Actionable Recommendation Engine.
Produces tailored recommendations, Google XYZ/STAR bullet point rewrites,
missing keyword integration strategies, and ATS optimization advice.
"""
import re
from typing import List, Dict, Any, Optional

from src.stage2_extraction.resume_parser import CandidateProfile
from src.stage3_matching.jd_parser import JobRequirements
from src.stage3_matching.scoring_engine import MatchScoreBreakdown
from src.stage4_recommendations.local_llm import LocalLLMClient

POWER_ACTION_VERBS = {
    "architected", "engineered", "spearheaded", "orchestrated", "developed",
    "implemented", "designed", "optimized", "streamlined", "automated",
    "scaled", "mentored", "delivered", "deployed", "transformed", "reduced",
    "accelerated", "integrated", "refactored", "migrated"
}


class ResumeRecommender:
    """Generates personalized, high-impact improvements for the resume."""

    def __init__(self, llm_client: Optional[LocalLLMClient] = None):
        self.llm = llm_client or LocalLLMClient()

    def generate_recommendations(
        self,
        profile: CandidateProfile,
        jd: JobRequirements,
        score_breakdown: MatchScoreBreakdown
    ) -> Dict[str, Any]:
        """Generate comprehensive improvement suite tailored to candidate and target role."""
        # 1. Missing Skill / Keyword Integration Strategy
        skill_recs = self._recommend_skill_integrations(score_breakdown.skill_report, jd)

        # 2. Bullet Point Rewrites (STAR / Google XYZ Framework)
        bullet_recs = self._rewrite_experience_bullets(profile, jd)

        # 3. ATS Optimization & Structural Audit
        ats_audit = self._audit_ats_readability(profile)

        # 4. Tailored Executive Pitch / Profile Summary
        tailored_summary = self._generate_tailored_summary(profile, jd, score_breakdown)

        return {
            "missing_skills_strategy": skill_recs,
            "bullet_enhancements": bullet_recs,
            "ats_audit": ats_audit,
            "tailored_summary": tailored_summary,
            "llm_provider_used": self.llm.provider
        }

    def _recommend_skill_integrations(self, skill_report, jd: JobRequirements) -> List[Dict[str, str]]:
        """Advise candidate how to incorporate missing skills naturally."""
        recs = []
        missing = skill_report.missing_required_skills[:6]

        for skill in missing:
            recs.append({
                "skill": skill,
                "importance": "High (Mandatory Requirement in JD)",
                "actionable_advice": (
                    f"If you have hands-on experience or coursework with {skill}, explicitly mention it in your "
                    f"Projects or Work Experience section with a specific metric or deliverable rather than just listing it in a skills grid."
                ),
                "example_bullet": (
                    f"• Leveraged {skill} to streamline system workflows, enhancing overall project execution and reliability."
                )
            })

        missing_pref = skill_report.missing_preferred_skills[:3]
        for skill in missing_pref:
            recs.append({
                "skill": skill,
                "importance": "Medium (Preferred / Bonus Skill)",
                "actionable_advice": (
                    f"Adding a project or certification related to {skill} will give you an edge over competing applicants."
                ),
                "example_bullet": (
                    f"• Explored and implemented {skill} in proof-of-concept architectures to evaluate scalability."
                )
            })

        return recs

    def _rewrite_experience_bullets(self, profile: CandidateProfile, jd: JobRequirements) -> List[Dict[str, str]]:
        """Identify weak or passive resume bullets and provide high-impact STAR rewrites."""
        rewrites = []
        all_bullets = []
        for work in profile.work_experience:
            for b in work.get("bullets", []):
                all_bullets.append(b)
        for proj in profile.projects:
            for b in proj.get("bullets", []):
                all_bullets.append(b)

        if not all_bullets:
            all_bullets = [
                "Responsible for writing backend code and maintaining database queries.",
                "Worked with the team to fix bugs and build new features for users."
            ]

        # Select up to 3 bullets that could be strengthened
        target_bullets = all_bullets[:3]

        for orig in target_bullets:
            prompt = (
                f"You are an executive resume coach. Rewrite this resume bullet point using Google's XYZ formula: "
                f"'Accomplished [X], as measured by [Y], by doing [Z]'.\n"
                f"Target Position: {jd.title}\n"
                f"Original Bullet: \"{orig}\"\n"
                f"Output ONLY the improved bullet point with strong action verbs and realistic quantifiable metrics."
            )
            enhanced = self.llm.generate(
                prompt=prompt,
                system_prompt="You are a professional corporate tech recruiter and resume specialist.",
                max_tokens=120,
                temperature=0.3
            )

            # Clean output
            clean_enhanced = enhanced.strip(" \"\n•-")
            if not clean_enhanced or len(clean_enhanced) < 20:
                clean_enhanced = (
                    f"Spearheaded implementation and architectural optimization of core systems, "
                    f"boosting efficiency by 25% and reducing operational friction across the engineering cycle."
                )

            rewrites.append({
                "original": orig,
                "improved": f"• {clean_enhanced}",
                "framework": "XYZ Formula (Accomplished [X] measured by [Y] by doing [Z])",
                "critique": "Transformed passive duty description into an outcome-oriented, measurable business achievement."
            })

        return rewrites

    def _audit_ats_readability(self, profile: CandidateProfile) -> Dict[str, Any]:
        """Perform structural ATS compliance and readability checks."""
        text = profile.raw_text
        words = text.split()
        word_count = len(words)

        # Check action verbs
        text_lower = text.lower()
        found_verbs = [v for v in POWER_ACTION_VERBS if v in text_lower]

        # Flags & Recommendations
        recommendations = []
        if word_count < 250:
            recommendations.append("Resume content is sparse (< 250 words). Expand on accomplishments, metrics, and technical contributions.")
        elif word_count > 1100:
            recommendations.append("Resume is lengthy (> 1100 words). Condense to 1-2 focused pages to improve recruiter scannability.")

        if len(found_verbs) < 5:
            recommendations.append(
                f"Only {len(found_verbs)} strong action verbs detected. Incorporate more verbs like "
                f"'{', '.join(list(POWER_ACTION_VERBS)[:4])}' to convey proactive leadership."
            )

        # Metric presence check (% or numbers)
        metric_matches = re.findall(r'\b(?:\d+%(?:\s+increase|\s+reduction)?|\$\d+[\d,]*|\d+x|\d+\+?\s*(?:users|clients|requests|ms|sec))\b', text, re.I)
        if len(metric_matches) < 3:
            recommendations.append("Low density of quantifiable metrics. Add numbers (% improvement, dollar savings, user scale, latency cuts).")

        return {
            "word_count": word_count,
            "action_verb_count": len(found_verbs),
            "action_verbs_found": found_verbs,
            "metrics_detected_count": len(metric_matches),
            "ats_compatibility_score": min(100, 60 + len(found_verbs) * 5 + len(metric_matches) * 5),
            "checks": recommendations or ["Resume formatting, metric density, and action verbs meet top corporate standards."]
        }

    def _generate_tailored_summary(
        self,
        profile: CandidateProfile,
        jd: JobRequirements,
        score_breakdown: MatchScoreBreakdown
    ) -> str:
        """Create a targeted 3-4 sentence professional summary aligned to the JD."""
        prompt = (
            f"Draft a compelling 3-sentence professional summary for a candidate applying to '{jd.title}'.\n"
            f"Candidate verified experience: {profile.total_years_exp} years.\n"
            f"Top matched skills: {', '.join(score_breakdown.skill_report.matched_required_skills[:5])}.\n"
            f"Target Key Tech: {', '.join(jd.required_skills[:4])}.\n"
            f"Make it professional, concise, and focused on value delivery. Do not invent fake company names."
        )
        summary = self.llm.generate(
            prompt=prompt,
            system_prompt="You are an expert talent acquisition advisor.",
            max_tokens=150,
            temperature=0.3
        )
        summary_clean = summary.strip(" \"\n")
        if len(summary_clean) < 40:
            summary_clean = (
                f"Dynamic software professional with {profile.total_years_exp} years of proven expertise in "
                f"{', '.join(score_breakdown.skill_report.matched_required_skills[:3]) or 'software development'}. "
                f"Demonstrated ability to architect reliable solutions and collaborate across cross-functional teams. "
                f"Eager to leverage core technical competencies to drive measurable impact as a {jd.title}."
            )
        return summary_clean


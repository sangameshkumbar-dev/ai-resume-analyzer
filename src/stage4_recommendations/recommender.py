"""
Personalized Resume Enhancement and Actionable Recommendation Engine.
Produces tailored recommendations, Google XYZ/STAR bullet point rewrites,
missing keyword integration strategies, and ATS optimization advice.
"""
import re
from typing import List, Dict, Any, Optional

from src.stage2_extraction.resume_parser import CandidateProfile
from src.stage2_extraction.taxonomy import SKILL_TAXONOMY, SKILL_ALIASES
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

    @staticmethod
    def _get_skill_category(skill_name: str) -> str:
        for cat, skills in SKILL_TAXONOMY.items():
            if skill_name.lower() in [s.lower() for s in skills]:
                return cat
        for alias, canon in SKILL_ALIASES.items():
            if alias.lower() == skill_name.lower():
                for cat, skills in SKILL_TAXONOMY.items():
                    if canon.lower() in [s.lower() for s in skills]:
                        return cat
        return "Software Engineering & Tools"

    @classmethod
    def _get_category_bullet_and_advice(cls, skill: str, category: str, is_required: bool) -> tuple[str, str]:
        if category == "Cloud & DevOps":
            advice = f"Detail how you configure, provision, or orchestrate deployments using {skill} with measurable turnaround or uptime metrics."
            bullet = f"• Automated infrastructure provisioning and containerized workflows with {skill}, reducing environment drift and deployment cycle times by 40%."
        elif category == "Databases & Storage":
            advice = f"Highlight database schema design, indexing, or caching strategies leveraging {skill} with dataset sizes or query latency reductions."
            bullet = f"• Architected scalable data storage and query optimization strategies using {skill}, decreasing peak read latencies by 35%."
        elif category == "Frameworks & Libraries":
            advice = f"Incorporate {skill} into your project deliverables, linking component architecture and modular design to measurable system responsiveness."
            bullet = f"• Engineered modular, production-ready application services leveraging {skill}, elevating system throughput and reducing render latencies by 30%."
        elif category == "Data Engineering & AI/ML":
            advice = f"Reference pipelines, model training, fine-tuning, or inference workflows implemented with {skill}, citing benchmark accuracy or data throughput."
            bullet = f"• Built and evaluated high-throughput data processing and model pipelines using {skill}, sustaining sub-80ms response times at scale."
        elif category == "Programming Languages":
            advice = f"Showcase production services or algorithmic components engineered in {skill}, emphasizing performance, concurrency, or type safety."
            bullet = f"• Implemented robust core services in {skill}, boosting concurrent transaction processing while maintaining rigorous type safety."
        else:
            advice = f"Incorporate practical deliverables with {skill} into your work bullets or project achievements to demonstrate verified competence to ATS parsers."
            bullet = f"• Integrated {skill} into engineering workflows, elevating software reliability and accelerating team delivery velocity by 25%."
        return advice, bullet

    def _recommend_skill_integrations(self, skill_report, jd: JobRequirements) -> List[Dict[str, str]]:
        """Advise candidate how to incorporate missing skills naturally without repeated templates."""
        recs = []
        missing = skill_report.missing_required_skills[:6]

        for skill in missing:
            cat = self._get_skill_category(skill)
            advice, example_b = self._get_category_bullet_and_advice(skill, cat, is_required=True)
            recs.append({
                "skill": skill,
                "importance": "High (Mandatory Requirement in JD)",
                "actionable_advice": advice,
                "example_bullet": example_b
            })

        missing_pref = skill_report.missing_preferred_skills[:3]
        for skill in missing_pref:
            cat = self._get_skill_category(skill)
            advice, example_b = self._get_category_bullet_and_advice(skill, cat, is_required=False)
            recs.append({
                "skill": skill,
                "importance": "Medium (Preferred / Bonus Skill)",
                "actionable_advice": advice,
                "example_bullet": example_b
            })

        return recs

    def _rewrite_experience_bullets(self, profile: CandidateProfile, jd: JobRequirements) -> List[Dict[str, str]]:
        """Identify weak or passive resume bullets and provide high-impact STAR rewrites tailored to each bullet."""
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

        # Select up to 3 distinct bullets that could be strengthened
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
            # If the response is generic, fallback canned text, or empty, use the candidate-grounded enhancer
            if (
                not clean_enhanced
                or len(clean_enhanced) < 20
                or "Actionable Enhancement" in clean_enhanced
                or "Redesigned and refactored" in clean_enhanced
            ):
                clean_enhanced = LocalLLMClient._enhance_single_bullet(orig)

            rewrites.append({
                "original": orig,
                "improved": f"• {clean_enhanced}",
                "framework": "XYZ Formula (Accomplished [X] measured by [Y] by doing [Z])",
                "critique": "Elevated passive duty description into an outcome-oriented, measurable business achievement grounded in your actual work."
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
            f"Candidate Name: {profile.name}.\n"
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

        matched = score_breakdown.skill_report.matched_required_skills
        top_skills = ", ".join(matched[:4]) if matched else ", ".join(profile.all_skills_list[:4])
        years = profile.total_years_exp
        years_txt = f"{years} years of verified experience" if years > 0 else "proven practical expertise"
        deg_txt = f"Holds a {profile.highest_degree}" if profile.highest_degree != "Not Specified" else ""

        if (
            len(summary_clean) < 40
            or "Results-driven software engineering professional with proven expertise in building high-concurrency systems" in summary_clean
        ):
            deg_clause = f"{deg_txt}, and eager" if deg_txt else "Eager"
            summary_clean = (
                f"Results-oriented software professional with {years_txt} specializing in "
                f"{top_skills or 'scalable software engineering'}. Demonstrated track record of building reliable, "
                f"high-performance systems and collaborating across cross-functional engineering teams. "
                f"{deg_clause} to leverage core technical proficiencies to drive high-impact results as a {jd.title}."
            )
        return summary_clean


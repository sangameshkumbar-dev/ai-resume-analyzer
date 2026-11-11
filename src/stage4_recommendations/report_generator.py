"""
Audit Report Generator.
Formats analysis results, score breakdowns, and recommendations into clean PDF and Markdown reports.
"""
import io
import html
from typing import Dict, Any
from src.stage2_extraction.resume_parser import CandidateProfile
from src.stage3_matching.jd_parser import JobRequirements
from src.stage3_matching.scoring_engine import MatchScoreBreakdown


class ReportGenerator:
    """Generates comprehensive PDF and Markdown reports for candidate export."""

    @staticmethod
    def generate_pdf_report(
        profile: CandidateProfile,
        jd: JobRequirements,
        score: MatchScoreBreakdown,
        recommendations: Dict[str, Any]
    ) -> bytes:
        """
        Generate a professional, downloadable PDF audit report.
        Uses reportlab flowables, styled tables, and formatted recommendations.
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )

        def esc(text: Any) -> str:
            return html.escape(str(text or ""))

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=4
        )
        sub_style = ParagraphStyle(
            'DocSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor('#475569'),
            spaceAfter=8
        )
        h2_style = ParagraphStyle(
            'DocH2',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=10,
            spaceAfter=6
        )
        h3_style = ParagraphStyle(
            'DocH3',
            parent=styles['Heading3'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#334155'),
            spaceBefore=6,
            spaceAfter=3
        )
        body_style = ParagraphStyle(
            'DocBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155')
        )
        bold_body = ParagraphStyle(
            'DocBold',
            parent=body_style,
            fontName='Helvetica-Bold'
        )
        callout_style = ParagraphStyle(
            'DocCallout',
            parent=body_style,
            fontName='Helvetica-Oblique',
            textColor=colors.HexColor('#0F766E')
        )

        story = []

        # Header Title & Metadata
        story.append(Paragraph("AI Resume &amp; Job Match Audit Report", title_style))
        story.append(Paragraph(
            f"<b>Target Position:</b> {esc(jd.title)} &nbsp;|&nbsp; "
            f"<b>Candidate:</b> {esc(profile.name)} &nbsp;|&nbsp; "
            f"<b>Overall Match Score:</b> <font color='#0F766E'><b>{score.overall_score}%</b></font> ({esc(score.tier)})",
            sub_style
        ))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=8))

        # 1. Match Score Breakdown Table
        story.append(Paragraph("1. Match Score Breakdown", h2_style))
        table_data = [
            [Paragraph("<b>Evaluation Dimension</b>", bold_body),
             Paragraph("<b>Score</b>", bold_body),
             Paragraph("<b>Weight</b>", bold_body),
             Paragraph("<b>Contribution</b>", bold_body)],
            [Paragraph("Technical Skills Match", body_style),
             Paragraph(f"{score.skills_score}%", body_style),
             Paragraph(f"{int(score.weights['skill_match']*100)}%", body_style),
             Paragraph(f"+{score.weighted_contributions['skills']} pts", body_style)],
            [Paragraph("Semantic / Domain Similarity", body_style),
             Paragraph(f"{score.semantic_score}%", body_style),
             Paragraph(f"{int(score.weights['semantic_similarity']*100)}%", body_style),
             Paragraph(f"+{score.weighted_contributions['semantic']} pts", body_style)],
            [Paragraph("Experience Alignment", body_style),
             Paragraph(f"{score.experience_score}%", body_style),
             Paragraph(f"{int(score.weights['experience_alignment']*100)}%", body_style),
             Paragraph(f"+{score.weighted_contributions['experience']} pts", body_style)],
            [Paragraph("Education Alignment", body_style),
             Paragraph(f"{score.education_score}%", body_style),
             Paragraph(f"{int(score.weights['education_alignment']*100)}%", body_style),
             Paragraph(f"+{score.weighted_contributions['education']} pts", body_style)],
            [Paragraph("<b>TOTAL MATCH SCORE</b>", bold_body),
             Paragraph(f"<b>{score.overall_score}%</b>", bold_body),
             Paragraph("<b>100%</b>", bold_body),
             Paragraph(f"<b>{score.overall_score} pts</b>", bold_body)],
        ]
        t = Table(table_data, colWidths=[200, 100, 100, 130])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#94A3B8')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F8FAFC')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 6))

        for exp in score.explanations:
            story.append(Paragraph(f"• {esc(exp)}", body_style))
        story.append(Spacer(1, 8))

        # 2. Skill Alignment & Gap Analysis
        story.append(Paragraph("2. Skill Alignment &amp; Gap Analysis", h2_style))
        matched_str = ", ".join(score.skill_report.all_matched) if score.skill_report.all_matched else "None identified"
        story.append(Paragraph(f"<b>Matched Skills ({len(score.skill_report.all_matched)}):</b> {esc(matched_str)}", body_style))
        story.append(Spacer(1, 4))

        missing_req = ", ".join(score.skill_report.missing_required_skills) if score.skill_report.missing_required_skills else "None! All required skills matched."
        story.append(Paragraph(f"<b>Missing Required Skills:</b> <font color='#DC2626'>{esc(missing_req)}</font>", body_style))
        story.append(Spacer(1, 4))

        if score.skill_report.missing_preferred_skills:
            missing_pref = ", ".join(score.skill_report.missing_preferred_skills)
            story.append(Paragraph(f"<b>Missing Preferred Skills:</b> <font color='#D97706'>{esc(missing_pref)}</font>", body_style))
            story.append(Spacer(1, 6))

        # 3. Personalized AI Recommendations
        story.append(Paragraph("3. Personalized AI Recommendations", h2_style))

        # A. Tailored Executive Pitch
        if recommendations.get("tailored_summary"):
            story.append(Paragraph("<b>A. Tailored Executive Pitch:</b>", h3_style))
            story.append(Paragraph(f"<i>\"{esc(recommendations['tailored_summary'])}\"</i>", callout_style))
            story.append(Spacer(1, 6))

        # B. Google XYZ / STAR Bullet Point Enhancements
        enh_bullets = recommendations.get("bullet_enhancements", [])
        if enh_bullets:
            story.append(Paragraph("<b>B. Google XYZ / STAR Bullet Point Rewrites:</b>", h3_style))
            for b in enh_bullets[:4]:
                story.append(Paragraph(f"• <b>Original:</b> <i>\"{esc(b.get('original', ''))}\"</i>", body_style))
                story.append(Paragraph(f"&nbsp;&nbsp;<b>Enhanced:</b> <font color='#0F766E'><b>{esc(b.get('improved', ''))}</b></font>", body_style))
                story.append(Paragraph(f"&nbsp;&nbsp;<font color='#64748B'>Rationale: {esc(b.get('critique', ''))}</font>", body_style))
                story.append(Spacer(1, 4))

        # C. Missing Skills Strategy
        strat = recommendations.get("missing_skills_strategy", [])
        if strat:
            story.append(Paragraph("<b>C. Missing Skills Integration Strategy:</b>", h3_style))
            for s in strat[:3]:
                story.append(Paragraph(f"• <b>{esc(s.get('skill', ''))}</b> ({esc(s.get('importance', ''))}): {esc(s.get('actionable_advice', ''))}", body_style))
                story.append(Paragraph(f"&nbsp;&nbsp;<i>Sample Pattern:</i> <code>{esc(s.get('example_bullet', ''))}</code>", body_style))
                story.append(Spacer(1, 3))

        # 4. ATS & Readability Audit
        ats = recommendations.get("ats_audit", {})
        story.append(Paragraph("4. ATS &amp; Formatting Health Check", h2_style))
        ats_line = (
            f"<b>ATS Compatibility Score:</b> {ats.get('ats_compatibility_score', 0)}/100 &nbsp;|&nbsp; "
            f"<b>Word Count:</b> {ats.get('word_count', 0)} &nbsp;|&nbsp; "
            f"<b>Action Verbs:</b> {ats.get('action_verb_count', 0)} &nbsp;|&nbsp; "
            f"<b>Quantifiable Metrics:</b> {ats.get('metrics_detected_count', 0)}"
        )
        story.append(Paragraph(ats_line, body_style))
        story.append(Spacer(1, 4))
        for check in ats.get("checks", []):
            story.append(Paragraph(f"• {esc(check)}", body_style))

        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=6))
        story.append(Paragraph("<font color='#94A3B8'><i>Generated by AI Resume Analyzer &amp; Job Matcher (100% Local NLP &amp; Dense Embeddings)</i></font>", body_style))

        doc.build(story)
        pdf_bytes = buf.getvalue()
        buf.close()
        return pdf_bytes

    @staticmethod
    def generate_markdown_report(
        profile: CandidateProfile,
        jd: JobRequirements,
        score: MatchScoreBreakdown,
        recommendations: Dict[str, Any]
    ) -> str:
        """Generate complete exportable markdown report."""
        report = []
        report.append(f"# 🎯 AI Resume & Job Match Audit Report")
        report.append(f"**Target Position:** {jd.title}")
        report.append(f"**Candidate:** {profile.name}")
        report.append(f"**Overall Match Score:** **{score.overall_score}%** — *{score.tier}*\n")
        report.append("---")

        # 1. Executive Summary
        report.append("## 📌 1. Match Score Breakdown")
        report.append("| Dimension | Score | Weight | Contribution |")
        report.append("|---|---|---|---|")
        report.append(f"| **Technical Skills Match** | {score.skills_score}% | {int(score.weights['skill_match']*100)}% | +{score.weighted_contributions['skills']} pts |")
        report.append(f"| **Semantic / Domain Similarity** | {score.semantic_score}% | {int(score.weights['semantic_similarity']*100)}% | +{score.weighted_contributions['semantic']} pts |")
        report.append(f"| **Experience Alignment** | {score.experience_score}% | {int(score.weights['experience_alignment']*100)}% | +{score.weighted_contributions['experience']} pts |")
        report.append(f"| **Education Alignment** | {score.education_score}% | {int(score.weights['education_alignment']*100)}% | +{score.weighted_contributions['education']} pts |")
        report.append(f"| **TOTAL SCORE** | **{score.overall_score}%** | 100% | **{score.overall_score} pts** |\n")

        report.append("### Score Explanation:")
        for exp in score.explanations:
            report.append(f"- {exp}")
        report.append("\n---")

        # 2. Skill Gap Analysis
        report.append("## 🔍 2. Skill Alignment & Gap Analysis")
        report.append(f"**Matched Skills ({len(score.skill_report.all_matched)}):**")
        if score.skill_report.all_matched:
            report.append(", ".join([f"`{s}`" for s in score.skill_report.all_matched]))
        else:
            report.append("None identified")

        report.append(f"\n**Missing Required Skills ({len(score.skill_report.missing_required_skills)}):**")
        if score.skill_report.missing_required_skills:
            report.append(", ".join([f"`{s}`" for s in score.skill_report.missing_required_skills]))
        else:
            report.append("None! All required skills matched.")

        if score.skill_report.missing_preferred_skills:
            report.append(f"\n**Missing Preferred Skills ({len(score.skill_report.missing_preferred_skills)}):**")
            report.append(", ".join([f"`{s}`" for s in score.skill_report.missing_preferred_skills]))

        report.append("\n---")

        # 3. Actionable Recommendations
        report.append("## 💡 3. Personalized Improvement Recommendations")
        report.append("### A. High-Priority Missing Skill Integration")
        for rec in recommendations.get("missing_skills_strategy", []):
            report.append(f"**{rec['skill']}** ({rec['importance']})")
            report.append(f"- *Advice:* {rec['actionable_advice']}")
            report.append(f"- *Sample Bullet:* `{rec['example_bullet']}`\n")

        report.append("### B. Google XYZ / STAR Bullet Point Enhancements")
        for b in recommendations.get("bullet_enhancements", []):
            report.append(f"**Original:** *\"{b['original']}\"*")
            report.append(f"**Enhanced:** **{b['improved']}**")
            report.append(f"*Why:* {b['critique']}\n")

        # 4. Tailored Summary
        report.append("### C. Tailored Executive Pitch")
        report.append(f"> \"{recommendations.get('tailored_summary', '')}\"\n")

        # 5. ATS Compliance
        ats = recommendations.get("ats_audit", {})
        report.append("## 📋 4. ATS & Readability Audit")
        report.append(f"- **Estimated Word Count:** {ats.get('word_count', 0)}")
        report.append(f"- **Strong Action Verbs Found:** {ats.get('action_verb_count', 0)}")
        report.append(f"- **Quantifiable Metrics Found:** {ats.get('metrics_detected_count', 0)}")
        report.append(f"- **ATS Health Score:** {ats.get('ats_compatibility_score', 0)}/100")
        report.append("### Checks & Advice:")
        for check in ats.get("checks", []):
            report.append(f"- {check}")

        report.append("\n---")
        report.append("*Generated by AI Resume Analyzer & Job Matcher (Hybrid NLP, Local Embeddings & LLM)*")

        return "\n".join(report)


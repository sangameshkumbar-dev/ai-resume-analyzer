"""
Utility script to generate realistic sample PDF resumes for testing and demonstrations.
"""
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SAMPLE_DIR = BASE_DIR / "data" / "sample_resumes"


def create_pdf(filename: str, content_data: dict):
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = SAMPLE_DIR / filename
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=4
    )
    contact_style = ParagraphStyle(
        'DocContact',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#475569'),
        spaceAfter=12
    )
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0F766E'),
        spaceBefore=8,
        spaceAfter=4,
        bold=True
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=4
    )
    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155'),
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )

    story = []

    # Name & Contact
    story.append(Paragraph(content_data["name"], title_style))
    contact_str = f"{content_data['email']} | {content_data['phone']} | {content_data['linkedin']} | {content_data['github']}"
    story.append(Paragraph(contact_str, contact_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=8))

    # Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", h2_style))
    story.append(Paragraph(content_data["summary"], body_style))
    story.append(Spacer(1, 6))

    # Skills
    story.append(Paragraph("TECHNICAL SKILLS", h2_style))
    for cat, sks in content_data["skills"].items():
        sk_line = f"<b>{cat}:</b> {', '.join(sks)}"
        story.append(Paragraph(sk_line, body_style))
    story.append(Spacer(1, 6))

    # Work Experience
    story.append(Paragraph("PROFESSIONAL EXPERIENCE", h2_style))
    for job in content_data["experience"]:
        job_header = f"<b>{job['title']}</b> | {job['company']} &nbsp;&nbsp;&nbsp;&nbsp; <i>{job['dates']}</i>"
        story.append(Paragraph(job_header, body_style))
        for bullet in job["bullets"]:
            story.append(Paragraph(f"• {bullet}", bullet_style))
        story.append(Spacer(1, 4))

    # Projects
    if "projects" in content_data and content_data["projects"]:
        story.append(Paragraph("PROJECTS", h2_style))
        for proj in content_data["projects"]:
            p_header = f"<b>{proj['name']}</b> | <i>{proj['tech']}</i>"
            story.append(Paragraph(p_header, body_style))
            for bullet in proj["bullets"]:
                story.append(Paragraph(f"• {bullet}", bullet_style))
            story.append(Spacer(1, 4))

    # Education
    story.append(Paragraph("EDUCATION", h2_style))
    for edu in content_data["education"]:
        edu_line = f"<b>{edu['degree']}</b> in {edu['major']} &nbsp;&nbsp; <i>{edu['year']}</i><br/>{edu['institution']} — GPA: {edu.get('gpa', 'N/A')}"
        story.append(Paragraph(edu_line, body_style))
        story.append(Spacer(1, 4))

    # Certifications
    if "certifications" in content_data and content_data["certifications"]:
        story.append(Paragraph("CERTIFICATIONS", h2_style))
        for cert in content_data["certifications"]:
            story.append(Paragraph(f"• {cert}", bullet_style))

    doc.build(story)
    print(f"Generated: {pdf_path}")


def generate_all_samples():
    # 1. Full Stack Engineer
    fullstack_data = {
        "name": "Alex Mercer",
        "email": "alex.mercer.dev@example.com",
        "phone": "+1 (555) 234-5678",
        "linkedin": "https://linkedin.com/in/alexmercer-dev",
        "github": "https://github.com/alexmercer",
        "summary": "Full Stack Software Engineer with 6+ years of verified experience building high-throughput microservices, responsive web apps, and automated cloud infrastructure using Python, React, and AWS.",
        "skills": {
            "Languages": ["Python", "TypeScript", "JavaScript", "SQL", "HTML5", "CSS3"],
            "Frameworks": ["FastAPI", "Django", "React", "Next.js", "Redux", "Tailwind CSS"],
            "Databases & Cloud": ["PostgreSQL", "Redis", "AWS", "Docker", "GitHub Actions", "CI/CD"],
            "Practices": ["Microservices", "REST APIs", "Unit Testing", "PyTest", "Agile"]
        },
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "CloudScale Technologies",
                "dates": "Jan 2021 - Present",
                "bullets": [
                    "Architected and deployed 12+ RESTful microservices in Python using FastAPI and PostgreSQL, serving 500k+ daily requests.",
                    "Designed and led migration of core customer portal to React and Next.js, cutting page load times by 42%.",
                    "Integrated Redis caching layer, decreasing database query latency by 65% during peak traffic bursts.",
                    "Mentored 4 junior software engineers on clean architecture, PyTest unit testing, and Git workflows."
                ]
            },
            {
                "title": "Full Stack Developer",
                "company": "Apex Digital Labs",
                "dates": "Jun 2018 - Dec 2020",
                "bullets": [
                    "Developed full-stack web applications using Python, Django, and React.",
                    "Created automated CI/CD pipelines with GitHub Actions and Docker, reducing release cycle time from 2 weeks to 2 days.",
                    "Optimized complex PostgreSQL queries and indexing, saving over $15,000 annually in AWS RDS compute costs."
                ]
            }
        ],
        "projects": [
            {
                "name": "Enterprise Document Search Engine",
                "tech": "Python, FastAPI, React, PostgreSQL, Docker",
                "bullets": [
                    "Built full-text indexing engine searching across 2M+ PDF legal documents in under 120ms.",
                    "Created responsive UI with React and Tailwind CSS featuring faceted filters and instant search."
                ]
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Technology",
                "major": "Computer Science and Engineering",
                "institution": "University of Washington",
                "year": "2018",
                "gpa": "3.8/4.0"
            }
        ],
        "certifications": [
            "AWS Certified Developer - Associate",
            "HashiCorp Certified: Terraform Associate"
        ]
    }

    # 2. Machine Learning Engineer
    ml_data = {
        "name": "Dr. Elena Rostova",
        "email": "elena.rostova.ai@example.com",
        "phone": "+1 (555) 876-5432",
        "linkedin": "https://linkedin.com/in/elena-rostova-ai",
        "github": "https://github.com/erostova-ml",
        "summary": "Machine Learning Engineer with 4+ years of specialized experience designing, fine-tuning, and deploying Deep Learning and NLP transformer pipelines, RAG systems, and scalable AI inference APIs.",
        "skills": {
            "Languages": ["Python", "SQL", "C++", "Bash"],
            "ML & AI Frameworks": ["PyTorch", "Hugging Face", "Transformers", "Scikit-Learn", "Pandas", "NumPy"],
            "GenAI & RAG": ["Large Language Models", "NLP", "ChromaDB", "Pinecone", "RAG", "BERT"],
            "Deployment & Cloud": ["FastAPI", "Docker", "AWS", "MLflow", "Linux"]
        },
        "experience": [
            {
                "title": "Machine Learning Engineer",
                "company": "NeuralEdge Solutions",
                "dates": "Aug 2021 - Present",
                "bullets": [
                    "Engineered multi-modal Retrieval-Augmented Generation (RAG) system utilizing Hugging Face Transformers and ChromaDB, increasing factual answer accuracy by 28%.",
                    "Fine-tuned domain-specific open-source LLMs on proprietary corpora using PyTorch and LoRA techniques.",
                    "Packaged and served low-latency inference pipelines via FastAPI and Docker on AWS ECS, handling 1.2M API calls weekly with sub-80ms response time.",
                    "Implemented automated model evaluation and data drift monitoring using MLflow and Prometheus."
                ]
            },
            {
                "title": "Data Scientist",
                "company": "Cognitive Insights Corp",
                "dates": "Jan 2020 - Jul 2021",
                "bullets": [
                    "Developed text classification and entity extraction models using NLP, BERT, and Scikit-Learn.",
                    "Automated feature engineering pipelines in Python and Pandas across 50GB+ unstructured datasets.",
                    "Presented predictive analytics dashboards to executive stakeholders, driving 18% improvement in customer retention."
                ]
            }
        ],
        "projects": [
            {
                "name": "Semantic Code Search Engine",
                "tech": "Python, PyTorch, Hugging Face, FastAPI, Docker",
                "bullets": [
                    "Trained neural embedding model to perform semantic search across 100k open-source repositories.",
                    "Deployed live demo on AWS using Docker containers with continuous integration."
                ]
            }
        ],
        "education": [
            {
                "degree": "Master of Science",
                "major": "Data Science and Artificial Intelligence",
                "institution": "Columbia University",
                "year": "2020",
                "gpa": "3.9/4.0"
            },
            {
                "degree": "Bachelor of Science",
                "major": "Computer Science",
                "institution": "University of Michigan",
                "year": "2018",
                "gpa": "3.8/4.0"
            }
        ],
        "certifications": [
            "AWS Certified Machine Learning - Specialty",
            "Deep Learning Specialization (DeepLearning.AI)"
        ]
    }

    create_pdf("resume_senior_fullstack.pdf", fullstack_data)
    create_pdf("resume_data_scientist.pdf", ml_data)


if __name__ == "__main__":
    generate_all_samples()


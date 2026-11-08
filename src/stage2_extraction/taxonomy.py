"""
Comprehensive technical skills, tools, frameworks, and domain taxonomy.
Includes canonical naming, categorization, and alias normalization.
"""
from typing import Dict, List, Set

# Categorized Skill Taxonomy
SKILL_TAXONOMY: Dict[str, List[str]] = {
    "Programming Languages": [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "C", "Go", "Golang",
        "Rust", "Kotlin", "Swift", "PHP", "Ruby", "Scala", "R", "Dart", "Perl", "Bash",
        "Shell", "PowerShell", "SQL", "HTML5", "CSS3", "Sass"
    ],
    "Frameworks & Libraries": [
        "React", "React.js", "Next.js", "Vue", "Vue.js", "Angular", "Node.js", "Express.js",
        "FastAPI", "Django", "Flask", "Spring Boot", "ASP.NET", ".NET Core", "Ruby on Rails",
        "PyTorch", "TensorFlow", "Keras", "Scikit-Learn", "Pandas", "NumPy", "OpenCV",
        "Hugging Face", "LangChain", "LlamaIndex", "GraphQL", "Tailwind CSS", "Bootstrap",
        "Redux", "Kafka", "Celery", "RabbitMQ"
    ],
    "Cloud & DevOps": [
        "AWS", "Amazon Web Services", "Microsoft Azure", "Azure", "Google Cloud", "GCP",
        "Docker", "Kubernetes", "Helm", "Terraform", "Ansible", "Jenkins", "GitHub Actions",
        "GitLab CI", "CI/CD", "CircleCI", "ArgoCD", "Prometheus", "Grafana", "ELK Stack",
        "CloudFormation", "Serverless", "AWS Lambda", "ECS", "EKS", "GKE", "Linux", "Ubuntu"
    ],
    "Databases & Storage": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra", "DynamoDB",
        "Oracle", "SQLite", "Snowflake", "BigQuery", "Neo4j", "Firebase", "Supabase",
        "Vector DB", "Pinecone", "ChromaDB", "Milvus", "Weaviate"
    ],
    "Data Engineering & AI/ML": [
        "Machine Learning", "Deep Learning", "Natural Language Processing", "NLP",
        "Computer Vision", "Large Language Models", "LLMs", "RAG", "Data Pipelines",
        "Apache Spark", "Hadoop", "Airflow", "Databricks", "dbt", "ETL", "Data Warehousing",
        "Feature Engineering", "Generative AI", "Transformers", "BERT", "Fine-Tuning"
    ],
    "Software Engineering & Tools": [
        "Git", "GitHub", "GitLab", "Bitbucket", "Jira", "Confluence", "Postman", "Swagger",
        "REST APIs", "Microservices", "System Design", "Agile", "Scrum", "TDD", "CI/CD",
        "Unit Testing", "PyTest", "Jest", "Design Patterns", "Clean Code", "OOP"
    ],
    "Soft Skills & Leadership": [
        "Team Leadership", "Cross-functional Collaboration", "Mentorship", "Problem Solving",
        "Agile Methodology", "Project Management", "Technical Writing", "Stakeholder Management",
        "Code Review", "Client Facing", "Strategic Planning"
    ]
}

# Alias / Variations normalization mapping (lower-case key -> Canonical Skill Name)
SKILL_ALIASES: Dict[str, str] = {
    "js": "JavaScript",
    "ts": "TypeScript",
    "py": "Python",
    "cpp": "C++",
    "c#": "C#",
    "golang": "Go",
    "k8s": "Kubernetes",
    "postgres": "PostgreSQL",
    "mongo": "MongoDB",
    "tf": "TensorFlow",
    "torch": "PyTorch",
    "scikit learn": "Scikit-Learn",
    "sklearn": "Scikit-Learn",
    "reactjs": "React",
    "react.js": "React",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "vuejs": "Vue",
    "vue.js": "Vue",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "node": "Node.js",
    "spring": "Spring Boot",
    "springboot": "Spring Boot",
    "amazon web services": "AWS",
    "google cloud platform": "GCP",
    "google cloud": "GCP",
    "ms azure": "Azure",
    "microsoft azure": "Azure",
    "elastic search": "Elasticsearch",
    "llm": "Large Language Models",
    "llms": "Large Language Models",
    "genai": "Generative AI",
    "gen ai": "Generative AI",
    "natural language processing": "NLP",
    "ml": "Machine Learning",
    "dl": "Deep Learning",
    "cv": "Computer Vision",
    "restful api": "REST APIs",
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "restful apis": "REST APIs",
    "micro service": "Microservices",
    "micro-services": "Microservices",
    "microservices": "Microservices",
    "github action": "GitHub Actions",
    "github actions": "GitHub Actions",
    "cicd": "CI/CD",
    "ci / cd": "CI/CD",
}

# Industry Certifications Catalog
RECOGNIZED_CERTIFICATIONS = [
    # AWS
    "AWS Certified Solutions Architect",
    "AWS Certified Developer",
    "AWS Certified DevOps Engineer",
    "AWS Certified Machine Learning",
    "AWS Certified Cloud Practitioner",
    "AWS Certified Security",
    "AWS Certified Data Analytics",
    # Azure
    "Microsoft Certified: Azure Fundamentals",
    "Microsoft Certified: Azure Developer Associate",
    "Microsoft Certified: Azure Solutions Architect",
    "Microsoft Certified: Azure DevOps Engineer",
    "Microsoft Certified: Azure AI Engineer",
    "Microsoft Certified: Azure Data Scientist",
    # GCP
    "Google Cloud Certified Professional Cloud Architect",
    "Google Cloud Certified Professional Data Engineer",
    "Google Cloud Certified Professional Cloud Developer",
    "Google Cloud Certified Associate Cloud Engineer",
    # Kubernetes / Cloud Native
    "CKA", "Certified Kubernetes Administrator",
    "CKAD", "Certified Kubernetes Application Developer",
    "CKS", "Certified Kubernetes Security Specialist",
    # Project / Agile / Security
    "PMP", "Project Management Professional",
    "CAPM", "Certified Associate in Project Management",
    "Scrum Master", "PSM", "CSM",
    "CISSP", "CompTIA Security+", "CompTIA Network+", "CompTIA A+",
    "CEH", "Certified Ethical Hacker",
    "HashiCorp Certified: Terraform Associate"
]


"""
Resume Service — PDF parsing and skill/project extraction for personalized interviews.
"""

import logging
import re
from typing import Dict, List, Optional
from io import BytesIO

logger = logging.getLogger(__name__)


def parse_resume(file_bytes: bytes) -> Dict:
    """
    Parse a PDF resume and extract structured information.
    Returns a dict with skills, projects, education, experience, and raw_text.
    """
    try:
        import pdfplumber
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            pages_text = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            raw_text = "\n".join(pages_text)
    except Exception as e:
        logger.error(f"PDF parsing failed: {e}")
        return {"error": str(e), "raw_text": "", "skills": [], "projects": [], "education": [], "experience": []}

    return {
        "raw_text": raw_text,
        "skills": extract_skills(raw_text),
        "projects": extract_projects(raw_text),
        "education": extract_education(raw_text),
        "experience": extract_experience(raw_text),
        "summary": raw_text[:2000],  # First 2000 chars for AI context
    }


def extract_skills(text: str) -> List[str]:
    """Extract technical skills from resume text."""
    skill_keywords = [
        # Languages
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "Ruby", "Swift",
        "Kotlin", "R", "SQL", "Scala", "PHP", "Dart",
        # Web
        "React", "Vue", "Angular", "Next.js", "Node.js", "Express", "Django", "FastAPI", "Flask",
        "Spring Boot", "GraphQL", "REST", "HTML", "CSS", "TailwindCSS",
        # Data / AI / ML
        "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Pandas", "NumPy", "Matplotlib",
        "LangChain", "LlamaIndex", "Hugging Face", "OpenAI", "Groq", "RAG", "LLM",
        "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "MLflow", "Airflow",
        # Cloud & DevOps
        "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform", "CI/CD", "GitHub Actions",
        "Jenkins", "Linux", "Nginx",
        # Databases
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "SQLite", "DynamoDB",
        "Pinecone", "Weaviate", "ChromaDB",
        # Tools
        "Git", "Jira", "Figma", "Postman", "Jupyter",
    ]

    found = []
    text_lower = text.lower()
    for skill in skill_keywords:
        if skill.lower() in text_lower:
            found.append(skill)
    return list(set(found))


def extract_projects(text: str) -> List[str]:
    """Extract project names and brief descriptions."""
    projects = []
    lines = text.split("\n")

    project_section = False
    project_keywords = ["project", "projects", "personal projects", "side projects", "portfolio"]
    stop_keywords = ["education", "experience", "work experience", "employment", "skills", "certifications"]

    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        if any(kw in line_lower for kw in project_keywords) and len(line_stripped) < 50:
            project_section = True
            continue

        if project_section and any(kw in line_lower for kw in stop_keywords) and len(line_stripped) < 50:
            project_section = False

        if project_section and line_stripped:
            # Heuristic: project names are typically short lines with capitals or bullet points
            clean = re.sub(r"^[\-\•\*\>\d\.\)]+\s*", "", line_stripped)
            if clean and 5 < len(clean) < 120:
                projects.append(clean)
            if len(projects) >= 8:
                break

    return projects


def extract_education(text: str) -> List[str]:
    """Extract education entries."""
    education = []
    lines = text.split("\n")
    edu_section = False
    edu_keywords = ["education", "academic", "qualification", "degree"]
    stop_keywords = ["experience", "skills", "projects", "certifications", "awards"]

    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        if any(kw in line_lower for kw in edu_keywords) and len(line_stripped) < 50:
            edu_section = True
            continue

        if edu_section and any(kw in line_lower for kw in stop_keywords) and len(line_stripped) < 50:
            edu_section = False

        if edu_section and line_stripped and len(line_stripped) > 5:
            education.append(line_stripped)
            if len(education) >= 6:
                break

    return education


def extract_experience(text: str) -> List[str]:
    """Extract work experience entries."""
    experience = []
    lines = text.split("\n")
    exp_section = False
    exp_keywords = ["experience", "work experience", "employment", "work history", "professional experience"]
    stop_keywords = ["education", "skills", "projects", "certifications"]

    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        if any(kw in line_lower for kw in exp_keywords) and len(line_stripped) < 60:
            exp_section = True
            continue

        if exp_section and any(kw in line_lower for kw in stop_keywords) and len(line_stripped) < 50:
            exp_section = False

        if exp_section and line_stripped and len(line_stripped) > 5:
            experience.append(line_stripped)
            if len(experience) >= 10:
                break

    return experience


def build_resume_context(parsed: Dict) -> str:
    """Build a concise context string for the AI interviewer."""
    parts = []

    if parsed.get("skills"):
        parts.append(f"Technical Skills: {', '.join(parsed['skills'][:15])}")

    if parsed.get("projects"):
        parts.append("Projects:")
        for p in parsed["projects"][:4]:
            parts.append(f"  - {p}")

    if parsed.get("education"):
        parts.append("Education:")
        for e in parsed["education"][:3]:
            parts.append(f"  - {e}")

    if parsed.get("experience"):
        parts.append("Experience Highlights:")
        for ex in parsed["experience"][:4]:
            parts.append(f"  - {ex}")

    return "\n".join(parts) if parts else parsed.get("summary", "")[:500]

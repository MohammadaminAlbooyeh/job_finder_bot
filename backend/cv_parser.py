import io
import re
from typing import Dict, List

# Curated list of tech job titles and skills to look for in a CV.
# Ordered roughly by specificity so a more specific title wins as the suggested query.
JOB_TITLES = [
    "machine learning engineer", "data scientist", "data engineer", "data analyst",
    "devops engineer", "site reliability engineer", "cloud engineer", "security engineer",
    "backend developer", "back-end developer", "frontend developer", "front-end developer",
    "full stack developer", "full-stack developer", "mobile developer", "ios developer",
    "android developer", "flutter developer", "react developer", "vue developer",
    "angular developer", "node.js developer", "django developer", "flask developer",
    "python developer", "java developer", "c# developer", "php developer", "ruby developer",
    "go developer", "software engineer", "software architect", "qa engineer",
    "test automation engineer", "database administrator", "network engineer",
]

SKILLS = [
    "python", "django", "flask", "fastapi", "java", "javascript", "typescript", "react",
    "vue", "angular", "node.js", "node", "sql", "postgresql", "mysql", "mongodb", "redis",
    "docker", "kubernetes", "aws", "azure", "gcp", "linux", "git", "ci/cd", "pandas",
    "numpy", "tensorflow", "pytorch", "scikit-learn", "airflow", "spark", "kafka",
    "microservices", "rest api", "graphql", "html", "css", "php", "ruby", "go", "c#",
    "c++", "swift", "kotlin", "flutter",
]


def extract_text(filename: str, content: bytes) -> str:
    """Extract raw text from a CV file (.pdf, .docx or .txt)."""
    name = (filename or "").lower()

    if name.endswith(".pdf"):
        import pdfplumber

        text_parts = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts)

    if name.endswith(".docx"):
        import docx

        doc = docx.Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)

    # fall back to plain text
    return content.decode("utf-8", errors="ignore")


def analyze_cv(text: str) -> Dict:
    """Find likely job title(s) and skill keywords mentioned in the CV text."""
    text_lower = text.lower()

    matched_titles: List[str] = [title for title in JOB_TITLES if title in text_lower]
    matched_skills: List[str] = [skill for skill in SKILLS if re.search(r"\b" + re.escape(skill) + r"\b", text_lower)]

    if matched_titles:
        suggested_query = matched_titles[0]
    elif matched_skills:
        suggested_query = f"{matched_skills[0]} developer"
    else:
        suggested_query = "software developer"

    return {
        "suggested_query": suggested_query,
        "matched_titles": matched_titles,
        "matched_skills": matched_skills,
    }

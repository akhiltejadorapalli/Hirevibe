"""
Core 'AI' logic for the platform.

No external LLM API key is required for the app to run end-to-end — every
feature here works out of the box using NLP/heuristics (TF-IDF similarity,
keyword extraction, rule-based scoring). If an OPENAI/ANTHROPIC-style API
key is supplied via the LLM_API_KEY env var, `llm_complete()` will use it
to generate richer free-text output (cover letters, feedback); otherwise a
solid template-based fallback is used automatically.
"""
import os
import re
import json
from typing import List, Dict, Any, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

LLM_API_KEY = os.environ.get("LLM_API_KEY", "")

# ---------------------------------------------------------------------------
# Skill dictionary used across resume parsing / matching / gap analysis
# ---------------------------------------------------------------------------
SKILL_BANK = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "sql", "nosql", "mongodb", "postgresql", "mysql", "react", "angular",
    "vue", "node.js", "express", "django", "flask", "fastapi", "spring",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ci/cd",
    "git", "linux", "html", "css", "tailwind", "redux", "graphql", "rest api",
    "machine learning", "deep learning", "nlp", "computer vision",
    "data analysis", "data visualization", "pandas", "numpy", "tensorflow",
    "pytorch", "scikit-learn", "excel", "power bi", "tableau", "figma",
    "product management", "agile", "scrum", "project management",
    "communication", "leadership", "problem solving", "sales", "marketing",
    "seo", "content writing", "customer service", "accounting", "finance",
    "salesforce", "sap", "android", "ios", "swift", "kotlin", "flutter",
    "unit testing", "microservices", "system design", "api design",
]

SCAM_KEYWORDS = [
    "pay to apply", "processing fee", "registration fee", "send money",
    "wire transfer", "gift card", "training fee", "deposit required",
    "no experience needed earn", "work from home guaranteed income",
    "urgent hiring no interview", "whatsapp only", "telegram only",
    "western union", "bitcoin payment", "advance payment",
    "earn $$$ fast", "click here to claim", "ssn required upfront",
]

VAGUE_PHRASES = [
    "unlimited earning potential", "be your own boss", "no skills required",
    "guaranteed job", "immediate hire no interview required",
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


# ---------------------------------------------------------------------------
# Resume parsing / extraction
# ---------------------------------------------------------------------------
def extract_resume_info(raw_text: str) -> Dict[str, Any]:
    text = raw_text or ""
    lower = text.lower()

    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    phone_match = re.search(r"(\+?\(?\d[\d\-\s()]{7,}\d\)?)", text)

    found_skills = sorted({s for s in SKILL_BANK if s in lower})

    # crude section splitting
    def section(names: List[str]) -> str:
        for n in names:
            m = re.search(
                rf"{n}\s*[:\n](.+?)(?=\n[A-Z][A-Za-z ]{{2,20}}\s*[:\n]|\Z)",
                text, re.IGNORECASE | re.DOTALL,
            )
            if m:
                return m.group(1).strip()[:1500]
        return ""

    education = section(["education"])
    experience = section(["experience", "work experience", "employment history"])
    summary = section(["summary", "objective", "profile"])

    word_count = len(text.split())

    return {
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0).strip() if phone_match else None,
        "skills": found_skills,
        "education_raw": education,
        "experience_raw": experience,
        "summary_raw": summary,
        "word_count": word_count,
    }


# ---------------------------------------------------------------------------
# ATS / Resume quality analysis
# ---------------------------------------------------------------------------
ACTION_VERBS = [
    "led", "built", "developed", "designed", "implemented", "managed",
    "improved", "increased", "reduced", "created", "launched", "optimized",
    "automated", "delivered", "coordinated", "analyzed",
]


def analyze_resume(raw_text: str, structured: Dict[str, Any]) -> Tuple[int, List[str], List[str]]:
    text = raw_text or ""
    lower = text.lower()
    mistakes: List[str] = []
    suggestions: List[str] = []
    score = 100

    word_count = structured.get("word_count", len(text.split()))
    if word_count < 150:
        mistakes.append("Resume looks too short — recruiters may see it as incomplete.")
        suggestions.append("Expand your experience section with 3-5 bullet points per role.")
        score -= 15
    elif word_count > 1200:
        mistakes.append("Resume is quite long; ATS systems and recruiters prefer concise resumes.")
        suggestions.append("Trim to 1-2 pages and remove outdated or irrelevant roles.")
        score -= 8

    if not structured.get("email"):
        mistakes.append("No email address detected.")
        suggestions.append("Add a professional email address near the top of your resume.")
        score -= 10

    if not structured.get("phone"):
        mistakes.append("No phone number detected.")
        suggestions.append("Add a contact phone number for recruiters to reach you.")
        score -= 5

    if len(structured.get("skills", [])) < 4:
        mistakes.append("Very few recognizable skills found.")
        suggestions.append("Add a dedicated Skills section listing tools, languages, and frameworks.")
        score -= 15
    else:
        score += 5

    action_hits = sum(1 for v in ACTION_VERBS if v in lower)
    if action_hits < 3:
        mistakes.append("Few strong action verbs detected (e.g. 'led', 'built', 'improved').")
        suggestions.append("Start bullet points with action verbs and quantify impact (e.g. 'Increased sign-ups by 20%').")
        score -= 10

    if not re.search(r"\d+%|\$\d|\d+\s*(users|clients|projects|team|hours|days)", lower):
        mistakes.append("No quantifiable achievements found (numbers, %, $).")
        suggestions.append("Quantify results wherever possible — metrics stand out to both ATS and recruiters.")
        score -= 10

    if "objective" in lower and "summary" not in lower:
        suggestions.append("Consider replacing a generic 'Objective' with a targeted professional Summary.")

    if not structured.get("education_raw"):
        mistakes.append("Education section not clearly detected.")
        suggestions.append("Add a clearly labeled Education section.")
        score -= 8

    if re.search(r"\breferences available upon request\b", lower):
        suggestions.append("Remove 'References available upon request' — it's outdated and wastes space.")
        score -= 2

    score = max(0, min(100, score))
    if not mistakes:
        mistakes.append("No major issues detected — nice work!")
    if not suggestions:
        suggestions.append("Resume looks solid. Consider tailoring keywords per job application.")

    return score, mistakes, suggestions


# ---------------------------------------------------------------------------
# Resume <-> Job Description matching (TF-IDF cosine similarity + skill overlap)
# ---------------------------------------------------------------------------
def compute_match(resume_text: str, resume_skills: List[str], job_text: str, job_skills: List[str]) -> Dict[str, Any]:
    resume_text = resume_text or ""
    job_text = job_text or ""

    try:
        vec = TfidfVectorizer(stop_words="english", max_features=2000)
        tfidf = vec.fit_transform([resume_text, job_text])
        sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    except ValueError:
        sim = 0.0

    resume_skill_set = {s.lower() for s in resume_skills}
    job_skill_set = {s.lower() for s in (job_skills or [])}
    if not job_skill_set:
        # derive from job text using skill bank
        low = job_text.lower()
        job_skill_set = {s for s in SKILL_BANK if s in low}

    matched = sorted(resume_skill_set & job_skill_set)
    missing = sorted(job_skill_set - resume_skill_set)

    skill_ratio = (len(matched) / len(job_skill_set)) if job_skill_set else 0.5
    final_score = round((0.55 * skill_ratio + 0.45 * sim) * 100)
    final_score = max(0, min(100, final_score))

    return {
        "match_score": final_score,
        "matched_skills": matched,
        "missing_skills": missing,
    }


# ---------------------------------------------------------------------------
# Job safety / scam analysis
# ---------------------------------------------------------------------------
def analyze_job_safety(job_text: str, salary_min=None, salary_max=None, company: str = "") -> Dict[str, Any]:
    low = (job_text or "").lower()
    reasons = []
    risk = 0

    for kw in SCAM_KEYWORDS:
        if kw in low:
            reasons.append(f"Contains a common scam phrase: '{kw}'.")
            risk += 25

    for kw in VAGUE_PHRASES:
        if kw in low:
            reasons.append(f"Uses vague/too-good-to-be-true language: '{kw}'.")
            risk += 15

    if salary_min and salary_max and salary_max > 0:
        if salary_min > 0 and salary_max / max(salary_min, 1) > 4:
            reasons.append("Salary range is unusually wide, which can indicate a bait listing.")
            risk += 10

    if not company or len(company.strip()) < 2:
        reasons.append("Company name is missing or unclear.")
        risk += 15

    if re.search(r"\bwhatsapp\b|\btelegram\b", low):
        reasons.append("Asks candidates to move communication to WhatsApp/Telegram — a common scam pattern.")
        risk += 20

    if len(job_text or "") < 80:
        reasons.append("Job description is extremely short/vague.")
        risk += 10

    risk = min(100, risk)
    is_scam = risk >= 40
    return {"is_flagged_scam": is_scam, "risk_score": risk, "scam_reasons": reasons}


def analyze_job_quality(job_text: str, requirements: str, skills: List[str]) -> int:
    score = 60
    text = f"{job_text} {requirements}"
    if len(text.split()) > 80:
        score += 10
    if skills:
        score += min(20, len(skills) * 3)
    if re.search(r"salary|compensation|\$\d", (job_text or "").lower()):
        score += 10
    if re.search(r"benefits|health insurance|pto|remote", (job_text or "").lower()):
        score += 10
    return max(0, min(100, score))


# ---------------------------------------------------------------------------
# Project relevance analysis
# ---------------------------------------------------------------------------
def analyze_project_relevance(projects_text: str, job_skills: List[str]) -> Dict[str, Any]:
    low = (projects_text or "").lower()
    job_skill_set = {s.lower() for s in job_skills}
    hits = [s for s in job_skill_set if s in low]
    relevance = round(100 * len(hits) / len(job_skill_set)) if job_skill_set else 0
    return {"relevance_score": relevance, "relevant_skills_shown": hits}


# ---------------------------------------------------------------------------
# Readiness score (aggregate of resume score + skills breadth + applications)
# ---------------------------------------------------------------------------
def compute_readiness_score(ats_score: int, num_skills: int, applications_count: int) -> int:
    score = 0.5 * ats_score + min(30, num_skills * 2) + min(20, applications_count * 2)
    return round(max(0, min(100, score)))


# ---------------------------------------------------------------------------
# Skill gap & learning roadmap
# ---------------------------------------------------------------------------
LEARNING_LINKS = {
    "python": "Python for Everybody (Coursera) / official docs at docs.python.org",
    "sql": "Mode SQL Tutorial / SQLBolt",
    "react": "React official docs (react.dev) / Epic React",
    "aws": "AWS Cloud Practitioner Essentials (free, AWS Skill Builder)",
    "docker": "Docker official 'Get Started' guide",
    "machine learning": "Andrew Ng's Machine Learning Specialization (Coursera)",
    "data analysis": "Google Data Analytics Certificate",
    "communication": "Toastmasters / 'Talk Like TED' by Carmine Gallo",
    "project management": "Google Project Management Certificate",
}


def build_learning_roadmap(missing_skills: List[str]) -> List[Dict[str, str]]:
    roadmap = []
    for skill in missing_skills[:8]:
        resource = LEARNING_LINKS.get(
            skill, f"Search for a beginner-to-intermediate course on '{skill}' (Coursera/YouTube/official docs)."
        )
        roadmap.append({
            "skill": skill,
            "recommended_resource": resource,
            "estimated_time": "2-4 weeks (5-8 hrs/week)",
        })
    return roadmap


# ---------------------------------------------------------------------------
# Apply-or-improve advisor
# ---------------------------------------------------------------------------
def apply_or_improve_advice(match_score: int, missing_skills: List[str]) -> Dict[str, Any]:
    if match_score >= 75:
        verdict = "apply_now"
        message = "Strong match — you meet most requirements. Apply now."
    elif match_score >= 50:
        verdict = "apply_with_tailoring"
        message = "Decent match. Tailor your resume to highlight the overlapping skills, then apply."
    else:
        verdict = "improve_first"
        message = "Lower match. Consider closing the top skill gaps below before applying, or apply if you're open to a stretch role."
    return {
        "verdict": verdict,
        "message": message,
        "roadmap": build_learning_roadmap(missing_skills),
    }


# ---------------------------------------------------------------------------
# Cover letter generation (template-based; upgrades automatically if LLM key set)
# ---------------------------------------------------------------------------
def generate_cover_letter(candidate_name: str, job_title: str, company: str,
                           matched_skills: List[str], summary: str, tone: str = "professional") -> str:
    if LLM_API_KEY:
        try:
            return llm_complete(
                f"Write a {tone} 3-paragraph cover letter for {candidate_name} applying to "
                f"{job_title} at {company}. Relevant skills: {', '.join(matched_skills)}. "
                f"Background: {summary}"
            )
        except Exception:
            pass  # fall through to template

    skills_str = ", ".join(matched_skills[:6]) if matched_skills else "a strong, relevant skill set"
    return (
        f"Dear Hiring Manager,\n\n"
        f"I am excited to apply for the {job_title} role at {company}. With hands-on experience in "
        f"{skills_str}, I'm confident I can contribute from day one. "
        f"{summary.strip() + ' ' if summary else ''}"
        f"In my recent work, I've focused on delivering measurable outcomes and collaborating closely "
        f"with cross-functional teams, and I'm drawn to {company}'s mission and the impact this role can have.\n\n"
        f"I would welcome the opportunity to discuss how my background in {skills_str} aligns with your "
        f"team's needs. Thank you for considering my application — I look forward to speaking further.\n\n"
        f"Sincerely,\n{candidate_name}"
    )


# ---------------------------------------------------------------------------
# Mock interview engine
# ---------------------------------------------------------------------------
QUESTION_BANK = {
    "general": [
        "Tell me about yourself and your professional background.",
        "Why are you interested in this role/company?",
        "Describe a challenging problem you solved recently. What was your approach?",
        "Tell me about a time you worked in a team to deliver something under a tight deadline.",
        "Where do you see yourself in three years?",
        "What is a mistake you made at work, and what did you learn from it?",
        "How do you prioritize when you have multiple competing deadlines?",
        "What's a piece of feedback you received that changed how you work?",
    ],
    "software engineer": [
        "Walk me through how you would design a URL shortening service.",
        "Explain the difference between SQL and NoSQL databases and when you'd use each.",
        "How do you approach debugging a production issue you can't reproduce locally?",
        "Describe your experience with CI/CD pipelines.",
        "What's the difference between a process and a thread?",
        "Tell me about a time you had to refactor messy code — what was your strategy?",
    ],
    "data analyst": [
        "How would you handle a dataset with a large amount of missing values?",
        "Explain a time your analysis changed a business decision.",
        "What's the difference between correlation and causation, and why does it matter?",
        "How do you decide which chart type to use for a given dataset?",
    ],
    "product manager": [
        "How do you prioritize a product roadmap with limited engineering resources?",
        "Tell me about a product decision you made using data.",
        "How would you improve a product you use every day?",
        "Describe how you handle disagreement between engineering and design.",
    ],
}


def generate_interview_questions(role: str, num_questions: int = 5) -> List[str]:
    role_key = (role or "general").strip().lower()
    pool = list(QUESTION_BANK.get("general", []))
    for key, qs in QUESTION_BANK.items():
        if key != "general" and key in role_key:
            pool = qs + pool
            break
    return pool[:max(1, min(num_questions, len(pool)))]


def score_interview_answer(question: str, answer: str) -> Dict[str, Any]:
    answer = (answer or "").strip()
    words = answer.split()
    score = 40
    tips = []

    if len(words) < 15:
        tips.append("Answer is quite short — aim for 3-5 sentences with a concrete example.")
    else:
        score += 15

    if re.search(r"\b(i|my|we)\b", answer.lower()):
        score += 10
    else:
        tips.append("Use first-person examples from your own experience ('I led...', 'I built...').")

    if re.search(r"\bresult|impact|improved|increased|reduced|outcome\b", answer.lower()):
        score += 20
    else:
        tips.append("Mention the result or impact of your action (try the STAR method: Situation, Task, Action, Result).")

    if len(words) > 5 and not re.search(r"[.!?]$", answer):
        tips.append("Consider ending your answer with a clear concluding sentence.")

    if not tips:
        tips.append("Strong, structured answer with a clear example and outcome.")
        score += 15

    score = max(0, min(100, score))
    return {"score": score, "tips": tips}


# ---------------------------------------------------------------------------
# Candidate ranking (for recruiters)
# ---------------------------------------------------------------------------
def rank_candidates(job_text: str, job_skills: List[str], candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ranked = []
    for c in candidates:
        result = compute_match(c.get("resume_text", ""), c.get("skills", []), job_text, job_skills)
        ranked.append({**c, **result})
    ranked.sort(key=lambda x: x["match_score"], reverse=True)
    return ranked


# ---------------------------------------------------------------------------
# Salary insights (heuristic, since no live market-data API is wired up)
# ---------------------------------------------------------------------------
def salary_insights(title: str, location: str, skills: List[str]) -> Dict[str, Any]:
    base = 55000
    title_low = (title or "").lower()
    bumps = {
        "senior": 35000, "lead": 45000, "staff": 60000, "principal": 75000,
        "manager": 30000, "director": 70000, "junior": -10000, "intern": -30000,
        "engineer": 15000, "scientist": 20000, "architect": 40000,
    }
    for k, v in bumps.items():
        if k in title_low:
            base += v
    base += min(len(skills), 10) * 2500
    low = max(30000, round((base * 0.85) / 1000) * 1000)
    high = round((base * 1.2) / 1000) * 1000
    return {
        "estimated_range": f"${low:,} - ${high:,} / year",
        "note": "Estimate based on role seniority keywords and skill count — not live market data.",
    }


# ---------------------------------------------------------------------------
# Chatbot intent engine (CareerBot) — rule/keyword based with optional LLM boost
# ---------------------------------------------------------------------------
INTENTS = [
    ("job_search", ["find a job", "search job", "looking for a job", "job openings", "vacancy", "vacancies"]),
    ("resume_help", ["resume", "cv ", "cv,", "cv.", "improve my resume", "ats"]),
    ("interview_prep", ["interview", "mock interview", "prepare for interview"]),
    ("career_guidance", ["career path", "career advice", "should i switch career", "career change"]),
    ("skill_advice", ["learn", "skill gap", "what should i learn", "upskill", "course"]),
    ("application_advice", ["should i apply", "apply or improve", "am i qualified"]),
    ("salary", ["salary", "pay range", "compensation", "how much should i ask"]),
    ("motivation", ["rejected", "feeling down", "discouraged", "burnt out", "burnout", "motivation"]),
    ("greeting", ["hello", "hi", "hey", "good morning", "good evening"]),
]


def detect_intent(message: str) -> str:
    low = message.lower()
    for intent, keywords in INTENTS:
        if any(k in low for k in keywords):
            return intent
    return "general_advice"


CHATBOT_RESPONSES = {
    "job_search": "I can help with that! Head to Job Search to browse openings, or tell me a role/skill and I'll point you in the right direction.",
    "resume_help": "Upload your resume in the Resume Analyzer and I'll score it, flag issues, and suggest concrete fixes (ATS keywords, formatting, quantified impact).",
    "interview_prep": "Let's practice — I can generate role-specific mock interview questions and score your answers with feedback using the STAR method.",
    "career_guidance": "Tell me your current role, target role, and what's motivating the change, and I'll map out a realistic path with skill gaps to close.",
    "skill_advice": "Share a target job or role and I'll compare it to your resume skills and build you a short learning roadmap.",
    "application_advice": "Paste a job link or open a job page — I'll compute your match score and tell you whether to apply now or upskill first.",
    "salary": "I can give you a rough salary range based on the role, seniority, and skills. Which job title and location are you targeting?",
    "motivation": "Job searching is genuinely hard, and a rejection isn't a verdict on your worth. Want to look at what's working in your applications so far, or take a short break and revisit your search plan together?",
    "greeting": "Hi! I'm CareerBot — I can help you search jobs, analyze your resume, prep for interviews, or plan your next career move. What would you like to do?",
    "general_advice": "I can help with job search, resume feedback, interview prep, career guidance, skill roadmaps, and salary insights. What's on your mind?",
}


def chatbot_reply(message: str) -> Dict[str, Any]:
    intent = detect_intent(message)
    if LLM_API_KEY:
        try:
            reply = llm_complete(
                f"You are CareerBot, a supportive career assistant. Reply concisely and helpfully to: {message}"
            )
            return {"reply": reply, "intent": intent}
        except Exception:
            pass
    return {"reply": CHATBOT_RESPONSES.get(intent, CHATBOT_RESPONSES["general_advice"]), "intent": intent}


# ---------------------------------------------------------------------------
# Optional real-LLM hook (used only if LLM_API_KEY is configured by the user)
# ---------------------------------------------------------------------------
def llm_complete(prompt: str) -> str:
    """Calls an Anthropic-compatible completion endpoint if LLM_API_KEY is set.
    Kept isolated so the rest of the app works fully offline without it."""
    import urllib.request

    if not LLM_API_KEY:
        raise RuntimeError("No LLM_API_KEY configured")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps({
            "model": "claude-sonnet-4-6",
            "max_tokens": 600,
            "messages": [{"role": "user", "content": prompt}],
        }).encode(),
        headers={
            "Content-Type": "application/json",
            "x-api-key": LLM_API_KEY,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode())
    return "".join(b.get("text", "") for b in data.get("content", []))

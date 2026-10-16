from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr


# ---------- Auth / User ----------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "job_seeker"  # job_seeker | recruiter
    company_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    company_name: Optional[str] = None
    company_verified: bool
    profile_completion: int
    open_to_work: bool
    is_banned: bool = False

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    company_name: Optional[str] = None
    open_to_work: Optional[bool] = None


# ---------- Resume ----------
class ResumeOut(BaseModel):
    id: int
    filename: Optional[str]
    raw_text: str
    structured: Dict[str, Any]
    ats_score: int
    mistakes: List[str]
    suggestions: List[str]
    is_builder_resume: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeBuilderIn(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    summary: Optional[str] = ""
    skills: List[str] = []
    experience: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []
    projects: List[Dict[str, Any]] = []
    certifications: List[str] = []


# ---------- Jobs ----------
class JobCreate(BaseModel):
    title: str
    company: str
    location: str = "Remote"
    category: str = "General"
    employment_type: str = "Full-time"
    description: str
    requirements: str = ""
    skills_required: List[str] = []
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None


class JobOut(BaseModel):
    id: int
    recruiter_id: int
    title: str
    company: str
    location: str
    category: str
    employment_type: str
    description: str
    requirements: str
    skills_required: List[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    is_flagged_scam: bool
    scam_reasons: List[str]
    quality_score: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class JobMatchOut(BaseModel):
    job: JobOut
    match_score: int
    missing_skills: List[str]
    matched_skills: List[str]


# ---------- Applications ----------
class ApplicationCreate(BaseModel):
    job_id: int
    resume_id: Optional[int] = None
    cover_letter: Optional[str] = None
    status: str = "applied"


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[datetime] = None


class ApplicationOut(BaseModel):
    id: int
    job_id: int
    applicant_id: int
    resume_id: Optional[int]
    cover_letter: Optional[str]
    match_score: int
    status: str
    notes: str
    follow_up_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    job: Optional[JobOut] = None

    class Config:
        from_attributes = True


class CoverLetterRequest(BaseModel):
    job_id: int
    resume_id: Optional[int] = None
    tone: str = "professional"


# ---------- Interview ----------
class InterviewStartRequest(BaseModel):
    role: str
    job_id: Optional[int] = None
    num_questions: int = 5
    mode: str = "text"  # text | video


class InterviewAnswerRequest(BaseModel):
    session_id: int
    question_index: int
    answer: str


class InterviewSessionOut(BaseModel):
    id: int
    role: str
    mode: str
    questions: List[str]
    answers: List[Optional[str]]
    feedback: List[Optional[Dict[str, Any]]]
    overall_score: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Chatbot ----------
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    intent: str
    suggestions: List[str] = []


# ---------- Admin ----------
class ReportCreate(BaseModel):
    target_type: str
    target_id: int
    reason: str


class ReportOut(BaseModel):
    id: int
    reporter_id: int
    target_type: str
    target_id: int
    reason: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

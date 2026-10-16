from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="job_seeker")  # job_seeker | recruiter | admin
    company_name = Column(String, nullable=True)  # for recruiters
    company_verified = Column(Boolean, default=False)
    profile_completion = Column(Integer, default=10)
    open_to_work = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    resumes = relationship("Resume", back_populates="owner", cascade="all,delete")
    applications = relationship("Application", back_populates="applicant", cascade="all,delete")
    jobs_posted = relationship("Job", back_populates="recruiter", cascade="all,delete")
    saved_jobs = relationship("SavedJob", back_populates="user", cascade="all,delete")
    notifications = relationship("Notification", back_populates="user", cascade="all,delete")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String, nullable=True)
    raw_text = Column(Text, default="")
    structured = Column(JSON, default=dict)   # extracted info: skills, education, experience...
    ats_score = Column(Integer, default=0)
    mistakes = Column(JSON, default=list)
    suggestions = Column(JSON, default=list)
    is_builder_resume = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="resumes")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, default="Remote")
    category = Column(String, default="General")
    employment_type = Column(String, default="Full-time")
    description = Column(Text, default="")
    requirements = Column(Text, default="")
    skills_required = Column(JSON, default=list)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    is_flagged_scam = Column(Boolean, default=False)
    scam_reasons = Column(JSON, default=list)
    quality_score = Column(Integer, default=70)
    status = Column(String, default="active")  # active | closed | under_review
    created_at = Column(DateTime, default=datetime.utcnow)

    recruiter = relationship("User", back_populates="jobs_posted")
    applications = relationship("Application", back_populates="job", cascade="all,delete")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    applicant_id = Column(Integer, ForeignKey("users.id"))
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    cover_letter = Column(Text, nullable=True)
    match_score = Column(Integer, default=0)
    status = Column(String, default="saved")
    # saved -> applied -> shortlisted -> interview -> selected/rejected
    notes = Column(Text, default="")
    follow_up_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="applications")
    applicant = relationship("User", back_populates="applications")


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="saved_jobs")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    role = Column(String, default="General")
    mode = Column(String, default="text")  # text | video
    questions = Column(JSON, default=list)
    answers = Column(JSON, default=list)
    feedback = Column(JSON, default=list)
    overall_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)  # user | bot
    intent = Column(String, nullable=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    kind = Column(String, default="info")  # info | alert | reminder
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"))
    target_type = Column(String)  # job | user
    target_id = Column(Integer)
    reason = Column(Text)
    status = Column(String, default="open")  # open | resolved | dismissed
    created_at = Column(DateTime, default=datetime.utcnow)

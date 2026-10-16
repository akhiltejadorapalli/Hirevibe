from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_

from .. import models, schemas, security, services
from ..database import get_db

router = APIRouter(prefix="/api", tags=["job_seeker"])
require_seeker = security.require_role("job_seeker")


# ---------------- Resume ----------------
def _extract_text_from_upload(file: UploadFile) -> str:
    content = file.file.read()
    name = (file.filename or "").lower()
    try:
        if name.endswith(".pdf"):
            import io
            try:
                from pypdf import PdfReader
            except ImportError:
                from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(content))
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        elif name.endswith(".docx"):
            import io
            import docx
            d = docx.Document(io.BytesIO(content))
            return "\n".join(p.text for p in d.paragraphs)
        else:
            return content.decode(errors="ignore")
    except Exception:
        return content.decode(errors="ignore")


@router.post("/resumes/upload", response_model=schemas.ResumeOut)
def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db),
                   user: models.User = Depends(require_seeker)):
    raw_text = _extract_text_from_upload(file)
    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from this file.")

    structured = services.extract_resume_info(raw_text)
    score, mistakes, suggestions = services.analyze_resume(raw_text, structured)

    resume = models.Resume(
        owner_id=user.id, filename=file.filename, raw_text=raw_text,
        structured=structured, ats_score=score, mistakes=mistakes,
        suggestions=suggestions, is_builder_resume=False,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.post("/resumes/build", response_model=schemas.ResumeOut)
def build_resume(payload: schemas.ResumeBuilderIn, db: Session = Depends(get_db),
                  user: models.User = Depends(require_seeker)):
    parts = [f"Name: {payload.full_name}"]
    if payload.email:
        parts.append(f"Email: {payload.email}")
    if payload.phone:
        parts.append(f"Phone: {payload.phone}")
    if payload.summary:
        parts.append(f"Summary:\n{payload.summary}")
    if payload.skills:
        parts.append("Skills:\n" + ", ".join(payload.skills))
    if payload.experience:
        exp_lines = []
        for e in payload.experience:
            exp_lines.append(f"{e.get('title','')} at {e.get('company','')} ({e.get('dates','')})\n{e.get('description','')}")
        parts.append("Experience:\n" + "\n".join(exp_lines))
    if payload.projects:
        proj_lines = [f"{p.get('name','')}: {p.get('description','')}" for p in payload.projects]
        parts.append("Projects:\n" + "\n".join(proj_lines))
    if payload.education:
        edu_lines = [f"{e.get('degree','')} - {e.get('school','')} ({e.get('dates','')})" for e in payload.education]
        parts.append("Education:\n" + "\n".join(edu_lines))
    if payload.certifications:
        parts.append("Certifications:\n" + ", ".join(payload.certifications))

    raw_text = "\n\n".join(parts)
    structured = services.extract_resume_info(raw_text)
    structured["skills"] = sorted(set(structured.get("skills", []) + [s.lower() for s in payload.skills]))
    score, mistakes, suggestions = services.analyze_resume(raw_text, structured)

    resume = models.Resume(
        owner_id=user.id, filename=f"{payload.full_name} - Resume", raw_text=raw_text,
        structured=structured, ats_score=score, mistakes=mistakes,
        suggestions=suggestions, is_builder_resume=True,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("/resumes", response_model=List[schemas.ResumeOut])
def list_resumes(db: Session = Depends(get_db), user: models.User = Depends(require_seeker)):
    return db.query(models.Resume).filter(models.Resume.owner_id == user.id).order_by(models.Resume.created_at.desc()).all()


@router.get("/resumes/{resume_id}", response_model=schemas.ResumeOut)
def get_resume(resume_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_seeker)):
    r = db.query(models.Resume).filter(models.Resume.id == resume_id, models.Resume.owner_id == user.id).first()
    if not r:
        raise HTTPException(404, "Resume not found")
    return r


@router.delete("/resumes/{resume_id}")
def delete_resume(resume_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_seeker)):
    r = db.query(models.Resume).filter(models.Resume.id == resume_id, models.Resume.owner_id == user.id).first()
    if not r:
        raise HTTPException(404, "Resume not found")
    db.delete(r)
    db.commit()
    return {"ok": True}


# ---------------- Job search / matching ----------------
@router.get("/jobs", response_model=List[schemas.JobOut])
def search_jobs(q: Optional[str] = None, location: Optional[str] = None,
                 category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Job).filter(models.Job.status == "active")
    if q:
        like = f"%{q}%"
        query = query.filter(or_(models.Job.title.ilike(like), models.Job.description.ilike(like), models.Job.company.ilike(like)))
    if location:
        query = query.filter(models.Job.location.ilike(f"%{location}%"))
    if category:
        query = query.filter(models.Job.category.ilike(f"%{category}%"))
    return query.order_by(models.Job.created_at.desc()).limit(100).all()


@router.get("/jobs/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return job


def _latest_resume(db: Session, user_id: int) -> Optional[models.Resume]:
    return db.query(models.Resume).filter(models.Resume.owner_id == user_id).order_by(models.Resume.created_at.desc()).first()


@router.get("/jobs/{job_id}/match")
def match_job(job_id: int, resume_id: Optional[int] = None, db: Session = Depends(get_db),
              user: models.User = Depends(require_seeker)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    resume = None
    if resume_id:
        resume = db.query(models.Resume).filter(models.Resume.id == resume_id, models.Resume.owner_id == user.id).first()
    else:
        resume = _latest_resume(db, user.id)
    if not resume:
        raise HTTPException(400, "Upload or build a resume first.")

    job_text = f"{job.title} {job.description} {job.requirements}"
    match = services.compute_match(resume.raw_text, resume.structured.get("skills", []), job_text, job.skills_required)
    advice = services.apply_or_improve_advice(match["match_score"], match["missing_skills"])
    project_relevance = services.analyze_project_relevance(
        resume.structured.get("experience_raw", "") + " " + resume.structured.get("summary_raw", ""),
        job.skills_required or match["matched_skills"] + match["missing_skills"],
    )
    return {
        "job_id": job.id, "resume_id": resume.id, **match,
        "advice": advice, "project_relevance": project_relevance,
    }


@router.get("/jobs-recommended")
def recommended_jobs(resume_id: Optional[int] = None, db: Session = Depends(get_db),
                      user: models.User = Depends(require_seeker)):
    resume = None
    if resume_id:
        resume = db.query(models.Resume).filter(models.Resume.id == resume_id, models.Resume.owner_id == user.id).first()
    else:
        resume = _latest_resume(db, user.id)
    if not resume:
        return []

    jobs = db.query(models.Job).filter(models.Job.status == "active").limit(200).all()
    results = []
    for job in jobs:
        job_text = f"{job.title} {job.description} {job.requirements}"
        match = services.compute_match(resume.raw_text, resume.structured.get("skills", []), job_text, job.skills_required)
        results.append({"job": job, "match_score": match["match_score"],
                         "matched_skills": match["matched_skills"], "missing_skills": match["missing_skills"]})
    results.sort(key=lambda r: r["match_score"], reverse=True)
    return results[:20]


@router.get("/readiness-score")
def readiness_score(db: Session = Depends(get_db), user: models.User = Depends(require_seeker)):
    resume = _latest_resume(db, user.id)
    apps_count = db.query(models.Application).filter(models.Application.applicant_id == user.id).count()
    ats = resume.ats_score if resume else 0
    num_skills = len(resume.structured.get("skills", [])) if resume else 0
    score = services.compute_readiness_score(ats, num_skills, apps_count)
    return {"readiness_score": score, "ats_score": ats, "num_skills": num_skills, "applications": apps_count}


@router.get("/salary-insights")
def salary_insights(title: str, location: str = "", db: Session = Depends(get_db),
                     user: models.User = Depends(require_seeker)):
    resume = _latest_resume(db, user.id)
    skills = resume.structured.get("skills", []) if resume else []
    return services.salary_insights(title, location, skills)


# ---------------- Save / Shortlist ----------------
@router.post("/jobs/{job_id}/save")
def save_job(job_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_seeker)):
    exists = db.query(models.SavedJob).filter(models.SavedJob.job_id == job_id, models.SavedJob.user_id == user.id).first()
    if exists:
        return {"ok": True, "already_saved": True}
    sj = models.SavedJob(job_id=job_id, user_id=user.id)
    db.add(sj)
    db.commit()
    return {"ok": True}


@router.delete("/jobs/{job_id}/save")
def unsave_job(job_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_seeker)):
    sj = db.query(models.SavedJob).filter(models.SavedJob.job_id == job_id, models.SavedJob.user_id == user.id).first()
    if sj:
        db.delete(sj)
        db.commit()
    return {"ok": True}


@router.get("/saved-jobs", response_model=List[schemas.JobOut])
def list_saved_jobs(db: Session = Depends(get_db), user: models.User = Depends(require_seeker)):
    saved = db.query(models.SavedJob).filter(models.SavedJob.user_id == user.id).all()
    job_ids = [s.job_id for s in saved]
    if not job_ids:
        return []
    return db.query(models.Job).filter(models.Job.id.in_(job_ids)).all()


# ---------------- Cover letter ----------------
@router.post("/cover-letter")
def cover_letter(payload: schemas.CoverLetterRequest, db: Session = Depends(get_db),
                  user: models.User = Depends(require_seeker)):
    job = db.query(models.Job).filter(models.Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    resume = None
    if payload.resume_id:
        resume = db.query(models.Resume).filter(models.Resume.id == payload.resume_id, models.Resume.owner_id == user.id).first()
    else:
        resume = _latest_resume(db, user.id)

    matched_skills = []
    summary = ""
    if resume:
        job_text = f"{job.title} {job.description} {job.requirements}"
        match = services.compute_match(resume.raw_text, resume.structured.get("skills", []), job_text, job.skills_required)
        matched_skills = match["matched_skills"]
        summary = resume.structured.get("summary_raw", "")

    letter = services.generate_cover_letter(user.name, job.title, job.company, matched_skills, summary, payload.tone)
    return {"cover_letter": letter}


# ---------------- Applications / Tracker ----------------
@router.post("/applications", response_model=schemas.ApplicationOut)
def create_application(payload: schemas.ApplicationCreate, db: Session = Depends(get_db),
                        user: models.User = Depends(require_seeker)):
    job = db.query(models.Job).filter(models.Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    existing = db.query(models.Application).filter(
        models.Application.job_id == payload.job_id, models.Application.applicant_id == user.id
    ).first()

    resume = None
    if payload.resume_id:
        resume = db.query(models.Resume).filter(models.Resume.id == payload.resume_id, models.Resume.owner_id == user.id).first()
    else:
        resume = _latest_resume(db, user.id)

    match_score = 0
    if resume:
        job_text = f"{job.title} {job.description} {job.requirements}"
        match_score = services.compute_match(resume.raw_text, resume.structured.get("skills", []), job_text, job.skills_required)["match_score"]

    if existing:
        existing.status = payload.status
        existing.cover_letter = payload.cover_letter or existing.cover_letter
        existing.resume_id = resume.id if resume else existing.resume_id
        existing.match_score = match_score or existing.match_score
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    app = models.Application(
        job_id=payload.job_id, applicant_id=user.id, resume_id=resume.id if resume else None,
        cover_letter=payload.cover_letter, match_score=match_score, status=payload.status,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


@router.get("/applications", response_model=List[schemas.ApplicationOut])
def list_applications(status: Optional[str] = None, db: Session = Depends(get_db),
                       user: models.User = Depends(require_seeker)):
    query = db.query(models.Application).filter(models.Application.applicant_id == user.id)
    if status:
        query = query.filter(models.Application.status == status)
    return query.order_by(models.Application.updated_at.desc()).all()


@router.put("/applications/{app_id}", response_model=schemas.ApplicationOut)
def update_application(app_id: int, payload: schemas.ApplicationUpdate, db: Session = Depends(get_db),
                        user: models.User = Depends(require_seeker)):
    app = db.query(models.Application).filter(models.Application.id == app_id, models.Application.applicant_id == user.id).first()
    if not app:
        raise HTTPException(404, "Application not found")
    if payload.status is not None:
        app.status = payload.status
    if payload.notes is not None:
        app.notes = payload.notes
    if payload.follow_up_date is not None:
        app.follow_up_date = payload.follow_up_date
    app.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(app)
    return app


@router.delete("/applications/{app_id}")
def delete_application(app_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_seeker)):
    app = db.query(models.Application).filter(models.Application.id == app_id, models.Application.applicant_id == user.id).first()
    if not app:
        raise HTTPException(404, "Application not found")
    db.delete(app)
    db.commit()
    return {"ok": True}


# ---------------- Interview prep / mock interview ----------------
@router.post("/interview/start", response_model=schemas.InterviewSessionOut)
def start_interview(payload: schemas.InterviewStartRequest, db: Session = Depends(get_db),
                     user: models.User = Depends(require_seeker)):
    questions = services.generate_interview_questions(payload.role, payload.num_questions)
    session = models.InterviewSession(
        user_id=user.id, job_id=payload.job_id, role=payload.role, mode=payload.mode,
        questions=questions, answers=[None] * len(questions), feedback=[None] * len(questions),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/interview/answer", response_model=schemas.InterviewSessionOut)
def answer_interview(payload: schemas.InterviewAnswerRequest, db: Session = Depends(get_db),
                      user: models.User = Depends(require_seeker)):
    session = db.query(models.InterviewSession).filter(
        models.InterviewSession.id == payload.session_id, models.InterviewSession.user_id == user.id
    ).first()
    if not session:
        raise HTTPException(404, "Interview session not found")
    if payload.question_index >= len(session.questions):
        raise HTTPException(400, "Invalid question index")

    feedback = services.score_interview_answer(session.questions[payload.question_index], payload.answer)

    answers = list(session.answers)
    feedbacks = list(session.feedback)
    answers[payload.question_index] = payload.answer
    feedbacks[payload.question_index] = feedback
    session.answers = answers
    session.feedback = feedbacks

    scored = [f["score"] for f in feedbacks if f]
    session.overall_score = round(sum(scored) / len(scored)) if scored else 0

    db.commit()
    db.refresh(session)
    return session


@router.get("/interview/{session_id}", response_model=schemas.InterviewSessionOut)
def get_interview(session_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_seeker)):
    session = db.query(models.InterviewSession).filter(
        models.InterviewSession.id == session_id, models.InterviewSession.user_id == user.id
    ).first()
    if not session:
        raise HTTPException(404, "Interview session not found")
    return session


@router.get("/interview", response_model=List[schemas.InterviewSessionOut])
def list_interviews(db: Session = Depends(get_db), user: models.User = Depends(require_seeker)):
    return db.query(models.InterviewSession).filter(models.InterviewSession.user_id == user.id).order_by(models.InterviewSession.created_at.desc()).all()


# ---------------- Notifications ----------------
@router.get("/notifications")
def list_notifications(db: Session = Depends(get_db), user: models.User = Depends(security.get_current_user)):
    notes = db.query(models.Notification).filter(models.Notification.user_id == user.id).order_by(models.Notification.created_at.desc()).limit(50).all()
    return notes


@router.put("/notifications/{note_id}/read")
def mark_notification_read(note_id: int, db: Session = Depends(get_db), user: models.User = Depends(security.get_current_user)):
    n = db.query(models.Notification).filter(models.Notification.id == note_id, models.Notification.user_id == user.id).first()
    if n:
        n.is_read = True
        db.commit()
    return {"ok": True}

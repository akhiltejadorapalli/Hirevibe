from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, security, services
from ..database import get_db

router = APIRouter(prefix="/api/recruiter", tags=["recruiter"])
require_recruiter = security.require_role("recruiter")


@router.post("/jobs", response_model=schemas.JobOut)
def post_job(payload: schemas.JobCreate, db: Session = Depends(get_db),
             user: models.User = Depends(require_recruiter)):
    job_text = f"{payload.title} {payload.description} {payload.requirements}"
    safety = services.analyze_job_safety(job_text, payload.salary_min, payload.salary_max, payload.company)
    quality = services.analyze_job_quality(payload.description, payload.requirements, payload.skills_required)

    job = models.Job(
        recruiter_id=user.id, title=payload.title, company=payload.company,
        location=payload.location, category=payload.category, employment_type=payload.employment_type,
        description=payload.description, requirements=payload.requirements,
        skills_required=payload.skills_required, salary_min=payload.salary_min, salary_max=payload.salary_max,
        is_flagged_scam=safety["is_flagged_scam"], scam_reasons=safety["scam_reasons"],
        quality_score=quality,
        status="under_review" if safety["is_flagged_scam"] else "active",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/jobs", response_model=List[schemas.JobOut])
def my_jobs(db: Session = Depends(get_db), user: models.User = Depends(require_recruiter)):
    return db.query(models.Job).filter(models.Job.recruiter_id == user.id).order_by(models.Job.created_at.desc()).all()


@router.put("/jobs/{job_id}", response_model=schemas.JobOut)
def update_job(job_id: int, payload: schemas.JobCreate, db: Session = Depends(get_db),
                user: models.User = Depends(require_recruiter)):
    job = db.query(models.Job).filter(models.Job.id == job_id, models.Job.recruiter_id == user.id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    for field, value in payload.dict().items():
        setattr(job, field, value)

    job_text = f"{job.title} {job.description} {job.requirements}"
    safety = services.analyze_job_safety(job_text, job.salary_min, job.salary_max, job.company)
    job.is_flagged_scam = safety["is_flagged_scam"]
    job.scam_reasons = safety["scam_reasons"]
    job.quality_score = services.analyze_job_quality(job.description, job.requirements, job.skills_required)
    db.commit()
    db.refresh(job)
    return job


@router.put("/jobs/{job_id}/status")
def set_job_status(job_id: int, status: str, db: Session = Depends(get_db),
                    user: models.User = Depends(require_recruiter)):
    job = db.query(models.Job).filter(models.Job.id == job_id, models.Job.recruiter_id == user.id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    if status not in ("active", "closed", "under_review"):
        raise HTTPException(400, "Invalid status")
    job.status = status
    db.commit()
    return {"ok": True}


@router.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_recruiter)):
    job = db.query(models.Job).filter(models.Job.id == job_id, models.Job.recruiter_id == user.id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    db.delete(job)
    db.commit()
    return {"ok": True}


@router.get("/jobs/{job_id}/applicants", response_model=List[schemas.ApplicationOut])
def view_applicants(job_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_recruiter)):
    job = db.query(models.Job).filter(models.Job.id == job_id, models.Job.recruiter_id == user.id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return db.query(models.Application).filter(models.Application.job_id == job_id).order_by(models.Application.match_score.desc()).all()


@router.get("/jobs/{job_id}/rank-candidates")
def rank_candidates(job_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_recruiter)):
    job = db.query(models.Job).filter(models.Job.id == job_id, models.Job.recruiter_id == user.id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    apps = db.query(models.Application).filter(models.Application.job_id == job_id).all()

    candidates = []
    for a in apps:
        resume = db.query(models.Resume).filter(models.Resume.id == a.resume_id).first() if a.resume_id else None
        applicant = db.query(models.User).filter(models.User.id == a.applicant_id).first()
        candidates.append({
            "application_id": a.id,
            "applicant_id": a.applicant_id,
            "applicant_name": applicant.name if applicant else "Unknown",
            "resume_text": resume.raw_text if resume else "",
            "skills": resume.structured.get("skills", []) if resume else [],
            "current_status": a.status,
        })

    job_text = f"{job.title} {job.description} {job.requirements}"
    ranked = services.rank_candidates(job_text, job.skills_required, candidates)
    for r in ranked:
        r.pop("resume_text", None)
    return ranked


@router.put("/applications/{app_id}/status")
def update_applicant_status(app_id: int, status: str, db: Session = Depends(get_db),
                             user: models.User = Depends(require_recruiter)):
    app = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app:
        raise HTTPException(404, "Application not found")
    job = db.query(models.Job).filter(models.Job.id == app.job_id, models.Job.recruiter_id == user.id).first()
    if not job:
        raise HTTPException(403, "Not your job posting")
    app.status = status
    db.commit()

    note = models.Notification(
        user_id=app.applicant_id,
        message=f"Your application for '{job.title}' at {job.company} was updated to: {status.replace('_',' ').title()}.",
        kind="alert",
    )
    db.add(note)
    db.commit()
    return {"ok": True}


@router.get("/analytics")
def recruiter_analytics(db: Session = Depends(get_db), user: models.User = Depends(require_recruiter)):
    jobs = db.query(models.Job).filter(models.Job.recruiter_id == user.id).all()
    job_ids = [j.id for j in jobs]
    total_apps = db.query(models.Application).filter(models.Application.job_id.in_(job_ids)).count() if job_ids else 0
    by_status = {}
    if job_ids:
        for a in db.query(models.Application).filter(models.Application.job_id.in_(job_ids)).all():
            by_status[a.status] = by_status.get(a.status, 0) + 1
    return {
        "total_jobs": len(jobs),
        "active_jobs": sum(1 for j in jobs if j.status == "active"),
        "total_applicants": total_apps,
        "applicants_by_status": by_status,
    }

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])
require_admin = security.require_role("admin")


@router.get("/users", response_model=List[schemas.UserOut])
def manage_users(role: Optional[str] = None, db: Session = Depends(get_db), user: models.User = Depends(require_admin)):
    q = db.query(models.User)
    if role:
        q = q.filter(models.User.role == role)
    return q.order_by(models.User.created_at.desc()).all()


@router.put("/users/{user_id}/ban")
def ban_user(user_id: int, banned: bool = True, db: Session = Depends(get_db), user: models.User = Depends(require_admin)):
    target = db.query(models.User).filter(models.User.id == user_id).first()
    if not target:
        raise HTTPException(404, "User not found")
    target.is_banned = banned
    db.commit()
    return {"ok": True}


@router.put("/recruiters/{user_id}/verify")
def verify_recruiter(user_id: int, verified: bool = True, db: Session = Depends(get_db),
                      user: models.User = Depends(require_admin)):
    target = db.query(models.User).filter(models.User.id == user_id, models.User.role == "recruiter").first()
    if not target:
        raise HTTPException(404, "Recruiter not found")
    target.company_verified = verified
    db.commit()
    return {"ok": True}


@router.get("/jobs", response_model=List[schemas.JobOut])
def manage_jobs(flagged_only: bool = False, db: Session = Depends(get_db), user: models.User = Depends(require_admin)):
    q = db.query(models.Job)
    if flagged_only:
        q = q.filter(models.Job.is_flagged_scam == True)  # noqa: E712
    return q.order_by(models.Job.created_at.desc()).all()


@router.put("/jobs/{job_id}/status")
def set_job_status(job_id: int, status: str, db: Session = Depends(get_db), user: models.User = Depends(require_admin)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    if status not in ("active", "closed", "under_review"):
        raise HTTPException(400, "Invalid status")
    job.status = status
    db.commit()
    return {"ok": True}


@router.get("/reports", response_model=List[schemas.ReportOut])
def list_reports(db: Session = Depends(get_db), user: models.User = Depends(require_admin)):
    return db.query(models.Report).order_by(models.Report.created_at.desc()).all()


@router.put("/reports/{report_id}")
def resolve_report(report_id: int, status: str, db: Session = Depends(get_db), user: models.User = Depends(require_admin)):
    r = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not r:
        raise HTTPException(404, "Report not found")
    if status not in ("open", "resolved", "dismissed"):
        raise HTTPException(400, "Invalid status")
    r.status = status
    db.commit()
    return {"ok": True}


@router.get("/analytics")
def platform_analytics(db: Session = Depends(get_db), user: models.User = Depends(require_admin)):
    total_users = db.query(models.User).count()
    seekers = db.query(models.User).filter(models.User.role == "job_seeker").count()
    recruiters = db.query(models.User).filter(models.User.role == "recruiter").count()
    total_jobs = db.query(models.Job).count()
    flagged_jobs = db.query(models.Job).filter(models.Job.is_flagged_scam == True).count()  # noqa: E712
    total_apps = db.query(models.Application).count()
    open_reports = db.query(models.Report).filter(models.Report.status == "open").count()
    return {
        "total_users": total_users, "job_seekers": seekers, "recruiters": recruiters,
        "total_jobs": total_jobs, "flagged_jobs": flagged_jobs,
        "total_applications": total_apps, "open_reports": open_reports,
    }


# ---------------- Reports (any authenticated user can file one) ----------------
report_router = APIRouter(prefix="/api", tags=["reports"])


@report_router.post("/reports", response_model=schemas.ReportOut)
def file_report(payload: schemas.ReportCreate, db: Session = Depends(get_db),
                 user: models.User = Depends(security.get_current_user)):
    r = models.Report(reporter_id=user.id, target_type=payload.target_type,
                       target_id=payload.target_id, reason=payload.reason)
    db.add(r)
    db.commit()
    db.refresh(r)

    if payload.target_type == "job":
        job = db.query(models.Job).filter(models.Job.id == payload.target_id).first()
        if job:
            job.status = "under_review"
            db.commit()
    return r

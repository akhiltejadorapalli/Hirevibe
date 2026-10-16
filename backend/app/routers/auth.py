from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=schemas.Token)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if payload.role not in ("job_seeker", "recruiter"):
        payload.role = "job_seeker"

    user = models.User(
        name=payload.name,
        email=payload.email,
        hashed_password=security.hash_password(payload.password),
        role=payload.role,
        company_name=payload.company_name if payload.role == "recruiter" else None,
        profile_completion=20,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = security.create_access_token({"sub": str(user.id)})
    return {"access_token": token, "user": user}


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not security.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if user.is_banned:
        raise HTTPException(status_code=403, detail="Account has been banned")
    token = security.create_access_token({"sub": str(user.id)})
    return {"access_token": token, "user": user}


@router.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(security.get_current_user)):
    return user


@router.put("/me", response_model=schemas.UserOut)
def update_profile(payload: schemas.ProfileUpdate, db: Session = Depends(get_db),
                    user: models.User = Depends(security.get_current_user)):
    if payload.name is not None:
        user.name = payload.name
    if payload.company_name is not None:
        user.company_name = payload.company_name
    if payload.open_to_work is not None:
        user.open_to_work = payload.open_to_work

    completion = 20
    if user.name:
        completion += 10
    if db.query(models.Resume).filter(models.Resume.owner_id == user.id).first():
        completion += 30
    if user.role == "recruiter" and user.company_name:
        completion += 20
    completion += 10
    user.profile_completion = min(100, completion)

    db.commit()
    db.refresh(user)
    return user

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas, security, services
from ..database import get_db

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])


@router.post("/message", response_model=schemas.ChatResponse)
def send_message(payload: schemas.ChatRequest, db: Session = Depends(get_db),
                  user: models.User = Depends(security.get_current_user)):
    db.add(models.ChatMessage(user_id=user.id, role="user", content=payload.message))

    result = services.chatbot_reply(payload.message)
    intent = result["intent"]

    suggestions_map = {
        "job_search": ["Search Jobs", "View recommended jobs"],
        "resume_help": ["Upload resume", "Build resume"],
        "interview_prep": ["Start mock interview"],
        "career_guidance": ["Chat more about your goals"],
        "skill_advice": ["View skill gap roadmap"],
        "application_advice": ["Check match score on a job"],
        "salary": ["Get salary insights"],
        "motivation": ["View application tracker"],
        "greeting": ["Search Jobs", "Analyze my resume", "Practice interview"],
        "general_advice": ["Search Jobs", "Analyze my resume", "Practice interview"],
    }

    db.add(models.ChatMessage(user_id=user.id, role="bot", intent=intent, content=result["reply"]))
    db.commit()

    return {"reply": result["reply"], "intent": intent, "suggestions": suggestions_map.get(intent, [])}


@router.get("/history")
def chat_history(db: Session = Depends(get_db), user: models.User = Depends(security.get_current_user)):
    msgs = db.query(models.ChatMessage).filter(models.ChatMessage.user_id == user.id).order_by(models.ChatMessage.created_at.asc()).limit(200).all()
    return [{"role": m.role, "content": m.content, "intent": m.intent, "created_at": m.created_at} for m in msgs]

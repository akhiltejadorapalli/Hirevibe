from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine
from .routers import auth, seeker, recruiter, admin, chatbot

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-Powered Job Search, Resume & Career Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(seeker.router)
app.include_router(recruiter.router)
app.include_router(admin.router)
app.include_router(admin.report_router)
app.include_router(chatbot.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}

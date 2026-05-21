import os
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import init_db
from app.routes.auth import router as auth_router
from app.routes.meetings import router as meetings_router
from app.routes.bot_upload import router as bot_upload_router
from app.routes.advanced import router as advanced_router
from app.routes.payments import router as payments_router
from app.routes.legal import router as legal_router
from app.routes.feedback import router as feedback_router

load_dotenv()

app = FastAPI(title="ASYNCPROOF Marketing Ready API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://asyncproof.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https://.*\\.vercel\\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(auth_router)
app.include_router(meetings_router)
app.include_router(bot_upload_router)
app.include_router(advanced_router)
app.include_router(payments_router)
app.include_router(legal_router)
app.include_router(feedback_router)

@app.get("/")
def home():
    return {"message": "ASYNCPROOF backend running"}

@app.get("/api/cors-test")
def cors_test():
    return {"message": "CORS working"}

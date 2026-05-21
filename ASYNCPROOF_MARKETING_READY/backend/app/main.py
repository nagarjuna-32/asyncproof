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

ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS",
        "https://asyncproof.vercel.app"
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"message":"ASYNCPROOF backend running"}

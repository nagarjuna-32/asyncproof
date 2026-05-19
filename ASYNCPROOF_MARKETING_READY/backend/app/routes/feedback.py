from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File, Form, Request
from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from app.db.database import get_conn, row_to_dict
from app.services.security import decode_token
from app.services.plans import normalize_plan
import json
from datetime import datetime

router = APIRouter(prefix="/api", tags=["feedback"])


def current_user(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    payload = decode_token(authorization.replace("Bearer ", ""))
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"id": int(payload["sub"]), "email": payload["email"]}


class FeedbackCreate(BaseModel):
    rating: int
    category: Literal[
        "general",
        "bug",
        "feature_request",
        "payment_issue",
        "meeting_issue",
        "ai_issue",
        "recording_problem",
        "login_issue",
        "storage_issue",
        "transcription_issue",
        "summary_issue",
        "translation_issue",
    ] = "general"
    message: str


class FeedbackResponse(BaseModel):
    id: int
    status: str
    screenshot_url: Optional[str] = None


class AdminFeedbackUpdate(BaseModel):
    status: Literal["new", "reviewed", "resolved"]
    admin_notes: Optional[str] = None


@router.post("/feedback")
def create_feedback(
    rating: int = Form(...),
    category: str = Form("general"),
    message: str = Form(...),
    email: Optional[EmailStr] = Form(None),
    screenshot: Optional[UploadFile] = File(None),
    user=Depends(current_user),
):
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="rating must be 1-5")

    allowed_categories = {
        "general",
        "bug",
        "feature_request",
        "payment_issue",
        "meeting_issue",
        "ai_issue",
        "recording_problem",
        "login_issue",
        "storage_issue",
        "transcription_issue",
        "summary_issue",
        "translation_issue",
    }
    if category not in allowed_categories:
        category = "general"

    screenshot_url = None
    # For now we only accept/store metadata; local/dev storage is handled in future.
    if screenshot:
        screenshot_url = f"local://{screenshot.filename}"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO feedback(user_id,email,rating,category,message,screenshot_url,status,admin_notes)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
                """,
                (user["id"], email or user["email"], rating, category, message, screenshot_url, "new", ""),
            )
            fid = cur.fetchone()["id"]

    return {"id": fid, "status": "new", "screenshot_url": screenshot_url}


@router.get("/user/feedback")
def list_my_feedback(user=Depends(current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM feedback WHERE user_id=%s ORDER BY created_at DESC LIMIT 100", (user["id"],))
            rows = cur.fetchall()
    return {"items": [row_to_dict(r) for r in rows]}


@router.get("/admin/feedback")
def admin_feedback(user=Depends(current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT role FROM users WHERE id=%s", (user["id"],))
            role = (cur.fetchone() or {}).get("role")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Admin only")
            cur.execute(
                """
                SELECT * FROM feedback ORDER BY created_at DESC LIMIT 200
                """
            )
            rows = cur.fetchall()
    return {"items": [row_to_dict(r) for r in rows]}


@router.patch("/admin/feedback/{id}")
def patch_admin_feedback(id: int, data: AdminFeedbackUpdate, user=Depends(current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT role FROM users WHERE id=%s", (user["id"],))
            role = (cur.fetchone() or {}).get("role")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Admin only")
            cur.execute(
                """
                UPDATE feedback
                SET status=%s, admin_notes=COALESCE(%s, admin_notes)
                WHERE id=%s
                RETURNING *
                """,
                (data.status, data.admin_notes, id),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return {"item": row_to_dict(row)}


@router.delete("/feedback/{id}")
def delete_feedback(id: int, user=Depends(current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM feedback WHERE id=%s AND user_id=%s", (id, user["id"]))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Feedback not found")
            cur.execute("DELETE FROM feedback WHERE id=%s", (id,))
    return {"deleted": True}


# Optional: API endpoint for auto-logging errors (used by server-side hooks)
# Kept simple to avoid breaking existing flows.
class AutoLogRequest(BaseModel):
    category: str = "bug"
    message: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"


@router.post("/feedback/auto-log")
def auto_log_error(payload: AutoLogRequest, request: Request):
    # System logs are stored as anonymous feedback rows with user_id NULL.
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO feedback(user_id,email,rating,category,message,screenshot_url,status,admin_notes)
                VALUES(NULL,NULL,0,%s,%s,NULL,'new',%s)
                RETURNING id
                """,
                (payload.category, payload.message[:5000], f"severity={payload.severity}"),
            )
            fid = cur.fetchone()["id"]
    return {"id": fid}


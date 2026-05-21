from fastapi import APIRouter, HTTPException, Depends, Header, UploadFile, File, Request
from pydantic import BaseModel
from pathlib import Path
import uuid, os, shutil, requests, json

from app.db.database import get_conn, row_to_dict
from app.services.security import decode_token
from app.services.transcription_pipeline import transcribe_summarize_action_translate
from app.services.storage import store_recording
from app.services.plans import normalize_plan

router = APIRouter(prefix="/api/meetings", tags=["meetings"])

UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

BOT_SERVICE_URL = os.getenv("BOT_SERVICE_URL", "http://127.0.0.1:9000")


def get_value(row, key, index):
    if isinstance(row, dict):
        return row.get(key)
    return row[index]


def current_user(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    payload = decode_token(authorization.replace("Bearer ", ""))

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {
        "id": int(payload["sub"]),
        "email": payload["email"]
    }


class MeetingCreate(BaseModel):
    title: str
    meeting_link: str
    platform: str = "google_meet"
    consent_confirmed: bool = False


@router.post("")
def create_meeting(data: MeetingCreate, request: Request, user=Depends(current_user)):
    if not data.consent_confirmed:
        raise HTTPException(
            status_code=400,
            detail="Recording consent confirmation required"
        )

    consent_text = "This meeting will be recorded by ASYNCPROOF AI Assistant."

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT plan FROM users WHERE id=%s",
                (user["id"],)
            )

            row = cur.fetchone()

            plan = "free"
            if row:
                plan = normalize_plan(get_value(row, "plan", 0) or "free")

            # During beta: allow meeting creation.
            # Later you can enable free limit again.
            # if plan == "free":
            #     cur.execute("""
            #         SELECT COUNT(*) AS count
            #         FROM meetings
            #         WHERE user_id=%s
            #         AND created_at >= date_trunc('month', NOW())
            #     """, (user["id"],))
            #     used_row = cur.fetchone()
            #     used = int(get_value(used_row, "count", 0) or 0)
            #     if used >= 3:
            #         raise HTTPException(
            #             status_code=402,
            #             detail="Free plan limit reached: 3 meetings/month. Upgrade to Premium or Team."
            #         )

            cur.execute(
                """
                INSERT INTO meetings(
                    user_id,
                    title,
                    meeting_link,
                    platform,
                    consent_confirmed,
                    status
                )
                VALUES(%s,%s,%s,%s,%s,%s)
                RETURNING id
                """,
                (
                    user["id"],
                    data.title,
                    data.meeting_link,
                    data.platform,
                    data.consent_confirmed,
                    "created"
                )
            )

            meeting_row = cur.fetchone()
            meeting_id = get_value(meeting_row, "id", 0)

            cur.execute(
                """
                INSERT INTO consent_logs(
                    meeting_id,
                    user_id,
                    consent_text,
                    ip_address,
                    user_agent
                )
                VALUES(%s,%s,%s,%s,%s)
                """,
                (
                    meeting_id,
                    user["id"],
                    consent_text,
                    request.client.host if request.client else None,
                    request.headers.get("user-agent")
                )
            )

    return {
        "id": meeting_id,
        "message": "Meeting created with recording consent log",
        "plan": plan,
        "consent_notice": consent_text
    }


@router.get("")
def list_meetings(user=Depends(current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM meetings
                WHERE user_id=%s
                ORDER BY created_at DESC
                """,
                (user["id"],)
            )

            rows = cur.fetchall()

    return [row_to_dict(r) for r in rows]


@router.post("/{meeting_id}/start-bot")
def start_bot(meeting_id: int, user=Depends(current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM meetings
                WHERE id=%s AND user_id=%s
                """,
                (meeting_id, user["id"])
            )

            meeting = cur.fetchone()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    job_id = str(uuid.uuid4())

    meeting_link = get_value(meeting, "meeting_link", 3)

    try:
        response = requests.post(
            f"{BOT_SERVICE_URL}/bot/start",
            json={
                "job_id": job_id,
                "meeting_id": meeting_id,
                "meeting_link": meeting_link,
                "bot_name": "ASYNCPROOF AI Assistant"
            },
            timeout=10
        )

        bot_response = response.json()
        status = bot_response.get("status", "queued")
        message = bot_response.get("message", "Bot requested")

    except Exception as e:
        status = "bot_service_unavailable"
        message = str(e)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO bot_jobs(
                    meeting_id,
                    job_id,
                    status,
                    message,
                    started_at
                )
                VALUES(%s,%s,%s,%s,NOW())
                """,
                (
                    meeting_id,
                    job_id,
                    status,
                    message
                )
            )

            cur.execute(
                "UPDATE meetings SET status=%s WHERE id=%s",
                ("bot_started", meeting_id)
            )

    return {
        "job_id": job_id,
        "status": status,
        "message": message
    }


@router.post("/{meeting_id}/recording")
def upload_recording(
    meeting_id: int,
    file: UploadFile = File(...),
    user=Depends(current_user)
):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM meetings
                WHERE id=%s AND user_id=%s
                """,
                (meeting_id, user["id"])
            )

            meeting = cur.fetchone()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    safe_name = f"{uuid.uuid4()}_{Path(file.filename or 'recording.mp4').name}"
    path = UPLOAD_DIR / safe_name

    with path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    pipeline = transcribe_summarize_action_translate(str(path))
    transcript = pipeline.get("transcript", "")
    report = pipeline.get("report", {})
    storage = store_recording(str(path))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO recordings(
                    meeting_id,
                    user_id,
                    filename,
                    file_path,
                    content_type,
                    storage_provider,
                    storage_url,
                    has_video,
                    has_audio,
                    premium_only
                )
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    meeting_id,
                    user["id"],
                    file.filename or safe_name,
                    str(path),
                    file.content_type,
                    storage.get("storage_provider", "local"),
                    storage.get("storage_url"),
                    True,
                    True,
                    True
                )
            )

            cur.execute(
                """
                INSERT INTO ai_reports(
                    meeting_id,
                    transcript,
                    summary,
                    key_points,
                    decisions,
                    action_items,
                    deadlines,
                    language,
                    productivity_score,
                    waste_score,
                    speakers,
                    analytics,
                    translation
                )
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(meeting_id)
                DO UPDATE SET
                    transcript=EXCLUDED.transcript,
                    summary=EXCLUDED.summary,
                    key_points=EXCLUDED.key_points,
                    decisions=EXCLUDED.decisions,
                    action_items=EXCLUDED.action_items,
                    deadlines=EXCLUDED.deadlines,
                    language=EXCLUDED.language,
                    productivity_score=EXCLUDED.productivity_score,
                    waste_score=EXCLUDED.waste_score,
                    speakers=EXCLUDED.speakers,
                    analytics=EXCLUDED.analytics,
                    translation=EXCLUDED.translation
                """,
                (
                    meeting_id,
                    transcript,
                    report.get("summary", ""),
                    report.get("key_points", ""),
                    report.get("decisions", ""),
                    report.get("action_items", ""),
                    report.get("deadlines", ""),
                    report.get("language", "auto"),
                    int(report.get("productivity_score", 0) or 0),
                    int(report.get("waste_score", 0) or 0),
                    json.dumps(report.get("speakers", [])),
                    json.dumps(report.get("analytics", {})),
                    json.dumps(
                        pipeline.get(
                            "translation",
                            report.get("translation", {})
                        )
                    )
                )
            )

            cur.execute(
                "UPDATE meetings SET status=%s WHERE id=%s",
                ("processed", meeting_id)
            )

    return {
        "message": "Recording uploaded and processed",
        "report": report
    }


@router.get("/{meeting_id}/report")
def get_report(meeting_id: int, user=Depends(current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM meetings
                WHERE id=%s AND user_id=%s
                """,
                (meeting_id, user["id"])
            )

            meeting = cur.fetchone()

            if not meeting:
                raise HTTPException(status_code=404, detail="Meeting not found")

            cur.execute(
                "SELECT * FROM ai_reports WHERE meeting_id=%s",
                (meeting_id,)
            )

            report = cur.fetchone()

    return {
        "meeting": row_to_dict(meeting),
        "report": row_to_dict(report) if report else None
    }

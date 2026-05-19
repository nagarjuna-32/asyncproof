from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File
from pathlib import Path
import uuid
import shutil
import json

from app.db.database import get_conn
from app.services.bot_upload import verify_bot_secret
from app.services.transcription_pipeline import transcribe_summarize_action_translate
from app.services.storage import store_recording

router = APIRouter(tags=["bot-upload"])

UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def dummy_user():
    return {"id": None}


@router.post("/api/bot/meetings/{meeting_id}/upload-recording")
def upload_recording_from_bot(
    meeting_id: int,
    x_bot_secret: str | None = Header(default=None, alias="X-Bot-Secret"),
    file: UploadFile = File(...),
    user=Depends(dummy_user),
):
    verify_bot_secret(x_bot_secret)
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing recording filename")

    content_type = file.content_type or "video/mp4"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, user_id FROM meetings WHERE id=%s", (meeting_id,))
            meeting = cur.fetchone()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    safe_name = f"{uuid.uuid4()}_{Path(file.filename).name}"
    path = UPLOAD_DIR / safe_name
    with path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    size = path.stat().st_size if path.exists() else 0
    if size <= 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    pipeline_result = transcribe_summarize_action_translate(str(path))
    transcript = pipeline_result.get("transcript", "")
    report = pipeline_result.get("report", {})
    translation = pipeline_result.get("translation", {})
    storage = store_recording(str(path))

    with get_conn() as conn:
        with conn.cursor() as cur:
            user_id = int(meeting["user_id"])
            cur.execute(
                """INSERT INTO recordings(meeting_id,user_id,filename,file_path,content_type,storage_provider,storage_url,has_video,has_audio,premium_only)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (meeting_id, user_id, file.filename, str(path), content_type, storage.get("storage_provider","local"), storage.get("storage_url"), True, True, True),
            )
            cur.execute(
                """
                INSERT INTO ai_reports(meeting_id,transcript,summary,key_points,decisions,action_items,deadlines,language,productivity_score,waste_score,speakers,analytics,translation)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(meeting_id) DO UPDATE SET
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
                    json.dumps(translation),
                ),
            )
            cur.execute("UPDATE meetings SET status=%s WHERE id=%s", ("processed", meeting_id))

    return {
        "message": "Recording uploaded and processed",
        "meeting_id": meeting_id,
        "recording": {
            "filename": file.filename,
            "file_path": str(path),
            "content_type": content_type,
            "size_bytes": size,
        },
        "report": report,
        "translation": translation,
        "status": "success",
    }

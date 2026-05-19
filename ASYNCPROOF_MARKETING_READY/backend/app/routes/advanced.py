
import os, uuid, json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from app.db.database import get_conn, row_to_dict
from app.services.security import decode_token
from app.services.ai_processor import ask_meeting_ai, translate_text
from app.services.scheduler import schedule_bot_join
from app.services.calendar import create_calendar_event_stub

router = APIRouter(prefix="/api", tags=["advanced"])


def current_user(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    payload = decode_token(authorization.replace("Bearer ", ""))
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"id": int(payload["sub"]), "email": payload["email"]}

class SearchRequest(BaseModel):
    query: str

class TranslationRequest(BaseModel):
    text: str
    target_language: str = "English"

class LiveTranscriptRequest(BaseModel):
    speaker: str = "unknown"
    text: str
    language: str = "auto"
    started_at_seconds: float = 0

class MemoryRequest(BaseModel):
    memory_type: str = "general"
    content: str
    meeting_id: Optional[int] = None

class SubscriptionRequest(BaseModel):
    plan: str = "pro"
    provider: str = "stripe"

class ScheduleRequest(BaseModel):
    meeting_id: int
    join_at_iso: str

@router.post("/ai/search")
def ai_search(data: SearchRequest, user=Depends(current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            like = f"%{data.query}%"
            cur.execute("""
                SELECT m.id, m.title, r.summary, r.action_items, r.decisions
                FROM meetings m LEFT JOIN ai_reports r ON r.meeting_id=m.id
                WHERE m.user_id=%s AND (m.title ILIKE %s OR COALESCE(r.transcript,'') ILIKE %s OR COALESCE(r.summary,'') ILIKE %s)
                ORDER BY m.created_at DESC LIMIT 20
            """, (user['id'], like, like, like))
            rows = cur.fetchall()
    answer = ask_meeting_ai(data.query, rows)
    return {"answer": answer, "results": [row_to_dict(r) for r in rows]}

@router.post("/translate")
def translate(data: TranslationRequest, user=Depends(current_user)):
    return translate_text(data.text, data.target_language)

@router.post("/meetings/{meeting_id}/live-transcript")
def add_live_transcript(meeting_id: int, data: LiveTranscriptRequest, user=Depends(current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM meetings WHERE id=%s AND user_id=%s", (meeting_id, user['id']))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Meeting not found")
            cur.execute("""
                INSERT INTO live_transcript_events(meeting_id,speaker,text,language,started_at_seconds)
                VALUES(%s,%s,%s,%s,%s) RETURNING id
            """, (meeting_id, data.speaker, data.text, data.language, data.started_at_seconds))
            event_id = cur.fetchone()['id']
    return {"id": event_id, "message": "Live transcript event saved"}

@router.get("/meetings/{meeting_id}/live-transcript")
def list_live_transcript(meeting_id: int, user=Depends(current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM meetings WHERE id=%s AND user_id=%s", (meeting_id, user['id']))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Meeting not found")
            cur.execute("SELECT * FROM live_transcript_events WHERE meeting_id=%s ORDER BY created_at ASC", (meeting_id,))
            rows = cur.fetchall()
    return [row_to_dict(r) for r in rows]

@router.post("/memory")
def save_memory(data: MemoryRequest, user=Depends(current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO meeting_memories(user_id,meeting_id,memory_type,content)
                VALUES(%s,%s,%s,%s) RETURNING id
            """, (user['id'], data.meeting_id, data.memory_type, data.content))
            mid = cur.fetchone()['id']
    return {"id": mid, "message": "Meeting memory saved"}

@router.get("/memory")
def list_memory(user=Depends(current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM meeting_memories WHERE user_id=%s ORDER BY created_at DESC LIMIT 100", (user['id'],))
            rows = cur.fetchall()
    return [row_to_dict(r) for r in rows]

@router.get("/analytics")
def analytics(user=Depends(current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) AS total_meetings,
                       COALESCE(AVG(r.productivity_score),0)::int AS avg_productivity,
                       COALESCE(AVG(r.waste_score),0)::int AS avg_waste
                FROM meetings m LEFT JOIN ai_reports r ON r.meeting_id=m.id
                WHERE m.user_id=%s
            """, (user['id'],))
            overview = cur.fetchone()
            cur.execute("""
                SELECT m.id,m.title,r.productivity_score,r.waste_score,r.analytics,m.created_at
                FROM meetings m LEFT JOIN ai_reports r ON r.meeting_id=m.id
                WHERE m.user_id=%s ORDER BY m.created_at DESC LIMIT 30
            """, (user['id'],))
            meetings = cur.fetchall()
    return {"overview": row_to_dict(overview), "meetings": [row_to_dict(m) for m in meetings]}

@router.post("/subscriptions/checkout")
def create_subscription(data: SubscriptionRequest, user=Depends(current_user)):
    # Production hook: replace this with Stripe Checkout Session creation.
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO subscriptions(user_id,provider,plan,status) VALUES(%s,%s,%s,%s) RETURNING id", (user['id'], data.provider, data.plan, 'pending'))
            sid = cur.fetchone()['id']
    return {"subscription_id": sid, "checkout_url": os.getenv('STRIPE_CHECKOUT_URL', 'configure-stripe-checkout-url'), "message": "Subscription checkout created/stubbed"}

@router.get("/premium/recordings/{meeting_id}")
def premium_recording(meeting_id: int, user=Depends(current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT plan FROM users WHERE id=%s", (user['id'],))
            plan = (cur.fetchone() or {}).get('plan', 'free')
            if plan not in ('pro','premium','enterprise'):
                raise HTTPException(status_code=402, detail="Premium plan required for full recording playback")
            cur.execute("SELECT * FROM recordings WHERE meeting_id=%s AND user_id=%s ORDER BY created_at DESC LIMIT 1", (meeting_id, user['id']))
            rec = cur.fetchone()
    if not rec: raise HTTPException(status_code=404, detail="Recording not found")
    return row_to_dict(rec)

@router.post("/scheduler/auto-join")
def auto_join(data: ScheduleRequest, user=Depends(current_user)):
    result = schedule_bot_join(data.meeting_id, data.join_at_iso)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE meetings SET bot_join_at=%s,status='scheduled' WHERE id=%s AND user_id=%s", (data.join_at_iso, data.meeting_id, user['id']))
    return result

@router.post("/calendar/create-event/{meeting_id}")
def calendar_event(meeting_id: int, user=Depends(current_user)):
    result = create_calendar_event_stub(meeting_id, user['id'])
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE meetings SET calendar_event_id=%s WHERE id=%s AND user_id=%s", (result['calendar_event_id'], meeting_id, user['id']))
    return result

@router.get("/admin/dashboard")
def admin_dashboard(user=Depends(current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT role FROM users WHERE id=%s", (user['id'],))
            role = (cur.fetchone() or {}).get('role')
            if role != 'admin':
                raise HTTPException(status_code=403, detail="Admin only")
            cur.execute("SELECT COUNT(*) AS users FROM users")
            users = cur.fetchone()
            cur.execute("SELECT COUNT(*) AS meetings FROM meetings")
            meetings = cur.fetchone()
            cur.execute("SELECT COUNT(*) AS recordings FROM recordings")
            recordings = cur.fetchone()
    return {"users": row_to_dict(users), "meetings": row_to_dict(meetings), "recordings": row_to_dict(recordings)}

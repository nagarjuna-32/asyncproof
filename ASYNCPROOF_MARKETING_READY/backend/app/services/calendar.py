
import uuid

def create_calendar_event_stub(meeting_id: int, user_id: int) -> dict:
    # Production: connect Google Calendar OAuth and create a real event.
    return {"calendar_event_id": f"cal_stub_{meeting_id}_{uuid.uuid4().hex[:8]}", "provider": "google", "status": "stub_created"}

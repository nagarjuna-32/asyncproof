
def schedule_bot_join(meeting_id: int, join_at_iso: str) -> dict:
    # Production: run Celery/Redis beat or APScheduler worker to call /start-bot at this time.
    return {"meeting_id": meeting_id, "join_at": join_at_iso, "status": "scheduled", "worker": "configure Celery/APScheduler for automatic execution"}

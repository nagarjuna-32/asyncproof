import os
from fastapi import HTTPException


def verify_bot_secret(x_bot_secret: str | None) -> None:
    expected = os.getenv("BOT_UPLOAD_SECRET", "").strip()
    if not expected:
        raise HTTPException(status_code=500, detail="BOT_UPLOAD_SECRET not configured")

    if not x_bot_secret or x_bot_secret.strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid X-Bot-Secret")


import os
from pathlib import Path
import requests


def upload_recording(
    backend_url: str,
    bot_secret: str,
    meeting_id: int,
    mp4_path: str,
    filename: str | None = None,
) -> dict:
    url = f"{backend_url.rstrip('/')}/api/bot/meetings/{meeting_id}/upload-recording"
    x_bot_secret = bot_secret

    file_name = filename or Path(mp4_path).name

    with open(mp4_path, "rb") as f:
        files = {
            "file": (file_name, f, "video/mp4"),
        }
        headers = {"X-Bot-Secret": x_bot_secret}
        resp = requests.post(url, headers=headers, files=files, timeout=300)

    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}

    resp.raise_for_status()
    return data


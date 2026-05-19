import os
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from playwright.async_api import async_playwright


app = FastAPI(title="ASYNCPROOF Visible Meeting Bot Service")
jobs = {}

try:
    from .recorder import record_with_ffmpeg
    from .uploader import upload_recording
except ImportError:
    from recorder import record_with_ffmpeg
    from uploader import upload_recording


class BotStartRequest(BaseModel):
    job_id: str
    meeting_id: int
    meeting_link: str
    bot_name: str = "ASYNCPROOF AI Assistant"

@app.get("/")
def home():
    return {"message": "ASYNCPROOF bot service running"}

@app.post("/bot/start")
async def start_bot(data: BotStartRequest):
    jobs[data.job_id] = {"status": "queued", "message": "Bot job queued", "meeting_id": data.meeting_id}
    asyncio.create_task(run_google_meet_bot(data))
    return {"job_id": data.job_id, "status": "queued", "message": "Bot is starting"}

@app.get("/bot/status/{job_id}")
def status(job_id: str):
    return jobs.get(job_id, {"status": "not_found"})

async def safe_click(page, selectors):
    for selector in selectors:
        try:
            loc = page.locator(selector)
            if await loc.count() > 0:
                await loc.first.click(timeout=3000)
                return True
        except Exception:
            continue
    return False

async def run_google_meet_bot(data: BotStartRequest):
    job_id = data.job_id
    try:
        jobs[job_id]["status"] = "opening_browser"
        jobs[job_id]["message"] = "Opening browser"

        async with async_playwright() as p:
            headless = os.getenv("BOT_HEADLESS", "true").lower() in ("1", "true", "yes")
            browser = await p.chromium.launch(
                headless=headless,
                args=[
                    "--use-fake-ui-for-media-stream",
                    "--use-fake-device-for-media-stream",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled"
                ]
            )

            context = await browser.new_context(
                permissions=["microphone", "camera"],
                viewport={"width": 1366, "height": 768}
            )

            page = await context.new_page()
            await page.goto(data.meeting_link, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(7000)

            jobs[job_id]["status"] = "meeting_opened"
            jobs[job_id]["message"] = "Meeting page opened"

            for selector in ['input[aria-label="Your name"]', 'input[placeholder="Your name"]', 'input[type="text"]']:
                try:
                    loc = page.locator(selector)
                    if await loc.count() > 0:
                        await loc.first.fill(data.bot_name)
                        break
                except Exception:
                    pass

            await safe_click(page, [
                'button[aria-label*="Turn off microphone"]',
                'button[aria-label*="microphone"]',
                'div[role="button"][aria-label*="microphone"]'
            ])

            await safe_click(page, [
                'button[aria-label*="Turn off camera"]',
                'button[aria-label*="camera"]',
                'div[role="button"][aria-label*="camera"]'
            ])

            joined = await safe_click(page, [
                'button:has-text("Join now")',
                'button:has-text("Ask to join")',
                'button:has-text("Join")',
                'button:has-text("Request to join")'
            ])

            if joined:
                jobs[job_id]["status"] = "live_or_waiting_for_admit"
                jobs[job_id]["message"] = "Join clicked. Bot is live or waiting for host approval."
            else:
                jobs[job_id]["status"] = "manual_join_required"
                jobs[job_id]["message"] = "Could not detect join button. Check browser window."

            # Recording phase (consent-based / visible bot)
            # Safety limit: match the wait time below in a single ffmpeg run.
            record_seconds = int(os.getenv("BOT_RECORD_SECONDS", "1800"))
            jobs[job_id]["status"] = "recording"
            jobs[job_id]["message"] = "Recording meeting (visible bot)"

            output_dir = os.getenv("RECORDINGS_DIR", "./recordings")
            mp4_path = None
            try:
                mp4_path = record_with_ffmpeg(
                    output_dir=output_dir,
                    output_filename=f"meeting_{data.meeting_id}_{job_id}.mp4",
                    duration_seconds=record_seconds,
                )
            except Exception as e:
                jobs[job_id]["status"] = "recording_failed"
                jobs[job_id]["message"] = str(e)

            if not mp4_path:
                jobs[job_id]["status"] = "ended_without_upload"
                jobs[job_id]["message"] = "Bot ended; recording was not created. Check FFmpeg/display audio setup."
                await browser.close()
                return

            jobs[job_id]["status"] = "recording_uploaded"
            jobs[job_id]["message"] = "Uploading recording to backend"
            if mp4_path:
                backend_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
                bot_secret = os.getenv("BOT_UPLOAD_SECRET", "")
                if not bot_secret:
                    raise RuntimeError("BOT_UPLOAD_SECRET not set in bot_service env")

                upload_res = upload_recording(
                    backend_url=backend_url,
                    bot_secret=bot_secret,
                    meeting_id=data.meeting_id,
                    mp4_path=str(mp4_path),
                )
                jobs[job_id]["message"] = f"Upload complete"

            jobs[job_id]["status"] = "ended"
            jobs[job_id]["message"] = jobs[job_id].get("message", "Bot session ended")
            await browser.close()


    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["message"] = str(e)

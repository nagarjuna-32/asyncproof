import os
import json
import subprocess
import tempfile
from pathlib import Path

from app.services.ai_processor import transcribe_audio, generate_ai_report


def extract_audio_to_wav(mp4_path: str, wav_path: str) -> None:
    """Extract audio from an MP4 using ffmpeg into mono 16kHz wav."""
    # ffmpeg must exist on the host running this backend (or in the Docker image)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        mp4_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "wav",
        wav_path,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def transcribe_summarize_action_translate(mp4_path: str) -> dict:
    """Runs: extract audio -> transcribe -> summary/action/decisions -> translate.

    Translation is implemented as a lightweight second AI step. If OPENAI_API_KEY
    is not configured, placeholders are returned by the underlying helpers.
    """
    with tempfile.TemporaryDirectory() as td:
        wav_path = str(Path(td) / "audio.wav")
        try:
            extract_audio_to_wav(mp4_path, wav_path)
            transcript = transcribe_audio(wav_path)
        except Exception as exc:
            transcript = (
                "Audio extraction/transcription fallback: uploaded recording was saved, "
                f"but ffmpeg/audio processing failed: {exc}. "
                "Install ffmpeg and upload a valid audio/video file for real transcription."
            )
        report = generate_ai_report(transcript)

        # Translation placeholder/second step:
        # If OPENAI_API_KEY is configured, reuse generate_ai_report-style model call
        # but ask for translation. Otherwise return placeholder.
        lang = report.get("language", "auto") or "auto"
        summary = report.get("summary", "")
        action_items = report.get("action_items", "")

        translated = {
            "language": lang,
            "transcript_translated": transcript,
            "summary_translated": summary,
            "action_items_translated": action_items,
        }

        # If OPENAI_API_KEY missing, generate_ai_report already returned placeholders.
        # We keep translation as a placeholder in that case.
        if os.getenv("OPENAI_API_KEY", "").strip():
            try:
                from openai import OpenAI

                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
                prompt = (
                    "Translate the meeting content into the requested language. "
                    "Return strict JSON with keys: transcript_translated, summary_translated, action_items_translated, language.\n\n"
                    f"Requested language: {lang}\n\n"
                    f"Transcript:\n{transcript}\n\n"
                    f"Summary:\n{summary}\n\n"
                    f"Action items:\n{action_items}\n"
                )
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Return valid JSON only."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )
                translated = json.loads(resp.choices[0].message.content)
            except Exception:
                # Keep defaults if translation fails
                pass

        return {
            "transcript": transcript,
            "report": report,
            "translation": translated,
        }


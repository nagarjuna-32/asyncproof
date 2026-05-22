import os
import json
import subprocess
import tempfile
from pathlib import Path

from app.services.ai_processor import transcribe_audio, generate_ai_report


def extract_audio_to_wav(input_path: str, wav_path: str) -> None:
    ext = Path(input_path).suffix.lower()

    # If already audio, ffmpeg still normalizes it to wav
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "wav",
        wav_path,
    ]

    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )


def safe_report(transcript: str, error: str = "") -> dict:
    return {
        "summary": (
            "Recording uploaded successfully. "
            "AI transcription/report fallback was generated."
        ),
        "key_points": [
            "Recording stored",
            "Processing pipeline executed",
            "Real transcription needs FFmpeg/OpenAI configured"
        ],
        "decisions": [
            "Continue ASYNCPROOF testing"
        ],
        "action_items": [
            "Check Render FFmpeg installation",
            "Add valid OPENAI_API_KEY",
            "Upload clear audio/video file"
        ],
        "deadlines": [
            "Next testing cycle"
        ],
        "language": "en",
        "productivity_score": 70,
        "waste_score": 20,
        "speakers": [],
        "analytics": {
            "fallback": True,
            "error": error
        },
        "translation": {
            "language": "en",
            "summary_translated": (
                "Recording uploaded successfully. "
                "Translation fallback generated."
            ),
            "action_items_translated": [
                "Check FFmpeg",
                "Check OpenAI key"
            ]
        }
    }


def transcribe_summarize_action_translate(file_path: str) -> dict:
    transcript = ""
    error_message = ""

    try:
        with tempfile.TemporaryDirectory() as td:
            wav_path = str(Path(td) / "audio.wav")
            extract_audio_to_wav(file_path, wav_path)
            transcript = transcribe_audio(wav_path)
    except Exception as exc:
        error_message = str(exc)
        transcript = (
            "Fallback transcript: recording was uploaded and saved, "
            "but audio extraction/transcription failed. "
            f"Reason: {error_message}"
        )

    try:
        report = generate_ai_report(transcript)
        if not isinstance(report, dict):
            report = safe_report(transcript, "generate_ai_report returned invalid format")
    except Exception as exc:
        report = safe_report(transcript, str(exc))

    if not report.get("summary"):
        report = safe_report(transcript, "Empty summary generated")

    translated = report.get("translation") or {
        "language": report.get("language", "en"),
        "transcript_translated": transcript,
        "summary_translated": report.get("summary", ""),
        "action_items_translated": report.get("action_items", []),
    }

    if os.getenv("OPENAI_API_KEY", "").strip():
        try:
            from openai import OpenAI

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
            prompt = f"""
Return valid JSON only.

Translate the meeting content.

Keys:
transcript_translated
summary_translated
action_items_translated
language

Transcript:
{transcript}

Summary:
{report.get("summary", "")}

Action Items:
{report.get("action_items", "")}
"""
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "Return valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            translated = json.loads(resp.choices[0].message.content)
        except Exception:
            pass

    return {
        "transcript": transcript,
        "report": report,
        "translation": translated,
    }

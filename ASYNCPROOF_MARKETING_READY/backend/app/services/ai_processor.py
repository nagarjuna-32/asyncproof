
import os, json, re
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def _client():
    from openai import OpenAI
    return OpenAI(api_key=OPENAI_API_KEY)

def _json_from_text(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text or "", re.S)
        if m:
            try: return json.loads(m.group(0))
            except Exception: pass
        return {}

def transcribe_audio(file_path: str) -> str:
    if not OPENAI_API_KEY:
        return f"Transcription placeholder: configure OPENAI_API_KEY to enable Whisper/OpenAI transcription. File: {file_path}"
    try:
        with open(file_path, "rb") as audio_file:
            result = _client().audio.transcriptions.create(model="whisper-1", file=audio_file)
        return result.text
    except Exception as e:
        return f"Transcription failed: {e}"

def generate_ai_report(transcript: str) -> dict:
    fallback = {
        "summary": "Meeting processed. Configure OPENAI_API_KEY for real AI summary.",
        "key_points": "Recording stored\nTranscript pipeline connected\nAnalytics pipeline ready",
        "decisions": "No decisions detected in placeholder mode.",
        "action_items": "Connect OpenAI key, upload meeting recording, review report.",
        "deadlines": "No deadlines detected.",
        "language": "auto",
        "productivity_score": 72,
        "waste_score": 28,
        "speakers": [{"speaker":"unknown","talk_time_seconds":0}],
        "analytics": {"focus_score":72,"talk_balance":"unknown","repeated_topics":[],"sentiment":"neutral"},
        "translation": {}
    }
    if not OPENAI_API_KEY:
        return fallback
    prompt = f"""
Analyze this meeting transcript for a production meeting intelligence app.
Return strict JSON only with keys:
summary, key_points, decisions, action_items, deadlines, language, productivity_score, waste_score, speakers, analytics, translation.
analytics must include focus_score, talk_balance, repeated_topics, sentiment, estimated_time_wasted_minutes.
Transcript:\n{transcript}
"""
    try:
        resp = _client().chat.completions.create(
            model=os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4o-mini"),
            messages=[{"role":"system","content":"Return valid JSON only."},{"role":"user","content":prompt}],
            temperature=0.2,
        )
        data = _json_from_text(resp.choices[0].message.content)
        return {**fallback, **data}
    except Exception as e:
        fallback["summary"] = f"AI report generation failed: {e}"
        fallback["productivity_score"] = 0
        fallback["waste_score"] = 0
        return fallback

def translate_text(text: str, target_language: str="English") -> dict:
    if not OPENAI_API_KEY:
        return {"target_language": target_language, "translated_text": f"Translation placeholder for {target_language}: {text}"}
    try:
        resp = _client().chat.completions.create(
            model=os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4o-mini"),
            messages=[{"role":"system","content":"Translate accurately."},{"role":"user","content":f"Translate to {target_language}:\n{text}"}],
            temperature=0.1,
        )
        return {"target_language": target_language, "translated_text": resp.choices[0].message.content}
    except Exception as e:
        return {"target_language": target_language, "error": str(e), "translated_text": text}

def ask_meeting_ai(query: str, rows) -> str:
    context = json.dumps([dict(r) for r in rows], default=str)[:12000]
    if not OPENAI_API_KEY:
        return f"Found {len(rows)} matching meeting item(s). Configure OPENAI_API_KEY for natural-language AI search answers."
    try:
        resp = _client().chat.completions.create(
            model=os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4o-mini"),
            messages=[{"role":"system","content":"Answer from the user's meeting context only."},{"role":"user","content":f"Question: {query}\nContext: {context}"}],
            temperature=0.2,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"AI search failed: {e}"

from fastapi import APIRouter

router = APIRouter(prefix="/api/legal", tags=["legal"])

CONSENT_NOTICE = "This meeting will be recorded by ASYNCPROOF AI Assistant. By continuing, you confirm that recording is allowed and necessary participants are informed/consented."

PRIVACY_POLICY = """
ASYNCPROOF Privacy Policy

We process meeting links, meeting metadata, uploaded/recorded audio-video files, transcripts, summaries, action items, translations, analytics, and account information to provide AI meeting intelligence.

Recording and consent: ASYNCPROOF AI Assistant must be visible in the meeting. Users are responsible for confirming recording permission and informing participants according to applicable law and organization policy.

AI processing: Recordings may be sent to configured AI providers such as OpenAI/Whisper for transcription, summarization, translation, speaker analysis, and search.

Storage: Recordings should be stored in configured secure cloud storage such as S3, Cloudinary, Supabase Storage, or compatible object storage. Local storage is for development only.

Security: Use HTTPS, JWT authentication, strong secrets, database backups, private storage buckets, signed URLs, and strict access control.

Deletion: Users should be able to request deletion of recordings, transcripts, reports, and account data. Admins must remove associated cloud files and database rows.
""".strip()

TERMS = """
ASYNCPROOF Terms of Use

ASYNCPROOF provides AI meeting recording, transcription, translation, summary, action-item extraction, and analytics tools. You must only use it for meetings where recording and AI processing are permitted.

You must not use ASYNCPROOF for hidden recording, surveillance, confidential meetings without authorization, or illegal activity.

Plan limits: Free users receive 3 meetings/month with summary and action items only. Premium users receive recording playback, translation, AI search, meeting memory, and productivity analytics. Team users receive admin dashboard, team analytics, calendar integration, and increased storage.

Payments: Razorpay/Stripe may be used for subscriptions. Refunds, plan changes, and cancellations should be described clearly on your live website.

Liability: AI outputs can be inaccurate. Users must verify summaries, deadlines, and decisions before relying on them.
""".strip()

@router.get("/consent")
def get_consent_notice():
    return {"notice": CONSENT_NOTICE}

@router.get("/privacy")
def get_privacy_policy():
    return {"title": "Privacy Policy", "content": PRIVACY_POLICY}

@router.get("/terms")
def get_terms():
    return {"title": "Terms of Use", "content": TERMS}

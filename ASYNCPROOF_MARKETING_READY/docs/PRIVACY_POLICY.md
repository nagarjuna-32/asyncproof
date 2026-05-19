# Privacy Policy

ASYNCPROOF processes meeting links, meeting metadata, audio/video recordings, transcripts, summaries, translations, action items, deadlines, decisions, analytics, account information, and subscription records to provide AI meeting intelligence.

## Recording consent
ASYNCPROOF AI Assistant must be visible in the meeting. Users are responsible for confirming that recording is permitted and that participants are informed according to applicable law, company policy, and meeting rules.

## AI processing
Recordings and transcripts may be processed by configured AI providers such as OpenAI/Whisper for transcription, summarization, translation, speaker analysis, meeting search, and productivity analytics.

## Storage
Recordings should be stored in secure cloud storage such as S3, Cloudflare R2, Supabase Storage, or Cloudinary. Local storage is for development only.

## Data deletion
Users should be able to request deletion of recordings, transcripts, summaries, analytics, and account data. Admins must delete both database rows and files stored in cloud storage.

## Security
Use HTTPS, JWT authentication, strong secrets, private storage buckets, signed URLs, database backups, and restricted admin access.

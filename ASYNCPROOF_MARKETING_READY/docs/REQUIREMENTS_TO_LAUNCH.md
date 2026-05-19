# ASYNCPROOF Launch Requirements

## 1. Required accounts / keys

### Backend / database
- PostgreSQL database URL from Render, Railway, Supabase, Neon, or VPS PostgreSQL.
- Strong `SECRET_KEY`.
- `ALLOWED_ORIGINS` set to your real frontend domain.

### AI
- `OPENAI_API_KEY` for Whisper/transcription, summary, action items, translation, AI search, and meeting memory.
- Recommended model env: `OPENAI_SUMMARY_MODEL=gpt-4o-mini`.

### Payment gateway
You can provide either:
- Razorpay payment link: `RAZORPAY_PAYMENT_LINK`
- Razorpay API keys for full automation: `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`
- Optional Stripe fallback: `STRIPE_SECRET_KEY`, `STRIPE_CHECKOUT_URL`, `STRIPE_WEBHOOK_SECRET`

### Secure storage
Production must not depend on local uploads. Provide one of:
- AWS S3 / Cloudflare R2 compatible bucket: `STORAGE_PROVIDER=s3`, `S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- Supabase Storage: `STORAGE_PROVIDER=supabase`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_BUCKET`
- Cloudinary: `STORAGE_PROVIDER=cloudinary`, `CLOUDINARY_URL`

### Bot service / VPS
The meeting bot needs a VPS because Playwright/Chrome/FFmpeg need real server resources.
Recommended minimum:
- Ubuntu 22.04/24.04
- 2 vCPU
- 4 GB RAM minimum, 8 GB better
- 40 GB SSD
- Docker + Docker Compose
- FFmpeg + Chromium/Playwright browser dependencies

## 2. Monetization plans added

### Free Plan
- 3 meetings/month
- Summary + action items only
- No full recording playback

### Premium Plan: ₹199–₹499/month
- Full recording playback
- Translation
- AI search
- Meeting memory
- Productivity analytics

### Team Plan: ₹999+/month
- Admin dashboard
- Team analytics
- Calendar integration
- More storage
- Team controls

## 3. Consent and privacy requirements

The frontend and backend now require the consent notice:

> This meeting will be recorded by ASYNCPROOF AI Assistant.

Before public launch, add a visible notice in your meeting bot name/description and website onboarding. Users must confirm that meeting recording is allowed and participants are informed.

## 4. Suggested hosting

### Frontend
- Vercel or Netlify
- Set `VITE_API_URL=https://your-backend-domain.com`

### Backend
- Render, Railway, or VPS
- Use PostgreSQL only
- Set all env variables

### Database
- Render PostgreSQL, Railway PostgreSQL, Supabase, Neon, or VPS PostgreSQL

### Bot service
- VPS recommended
- Needs Chrome/Playwright/FFmpeg support

## 5. Before taking real money

- Replace manual Razorpay payment-link flow with verified webhook activation.
- Add refund/cancellation policy.
- Add deletion API for recordings and transcripts.
- Enable private storage bucket and signed URLs.
- Add rate limiting and admin monitoring.
- Add backups.

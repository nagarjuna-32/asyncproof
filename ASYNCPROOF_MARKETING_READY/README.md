# ASYNCPROOF — Production Advanced PostgreSQL AI Meeting Platform

ASYNCPROOF is an AI meeting intelligence platform with visible recording consent, PostgreSQL backend, JWT authentication, payment-plan hooks, secure storage hooks, AI reports, analytics, meeting memory, and deployment documentation.

## Added business-ready features

- Required recording consent notice: **“This meeting will be recorded by ASYNCPROOF AI Assistant.”**
- Consent logs saved in PostgreSQL
- Free/Premium/Team monetization plans
- Razorpay payment-link checkout hook
- Stripe checkout fallback hook
- Secure storage router for S3, Supabase, Cloudinary, or local development
- Privacy Policy and Terms API endpoints
- Privacy Policy and Terms markdown documents
- PostgreSQL-only database schema
- JWT authentication
- Premium recording playback gate
- AI transcription/summary/action items/deadlines/decisions/translation hooks
- Speaker detection JSON fields
- AI search and meeting memory APIs
- Waste score and productivity analytics
- Live transcription event API
- Calendar integration stub
- Auto-join scheduler hook
- Admin dashboard API
- Docker deployment
- VPS deployment guide

## Plans

### Free
- 3 meetings/month
- Summary + action items only
- No full recording playback

### Premium — ₹199–₹499/month
- Full recording playback
- Translation
- AI search
- Meeting memory
- Productivity analytics

### Team — ₹999+/month
- Admin dashboard
- Team analytics
- Calendar integration
- More storage
- Team controls

## Required environment variables

Copy `.env.example` to `.env` and set real values.

Important production values:

```bash
DATABASE_URL=postgresql://...
SECRET_KEY=your-long-random-secret
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
OPENAI_API_KEY=sk-...
BOT_SERVICE_URL=https://your-bot-service-domain
BOT_UPLOAD_SECRET=your-bot-secret

# Payment
RAZORPAY_PAYMENT_LINK=https://rzp.io/...
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
STRIPE_SECRET_KEY=
STRIPE_CHECKOUT_URL=

# Storage
STORAGE_PROVIDER=s3
S3_BUCKET=your-private-bucket
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-south-1
```

## Run locally with Docker

```bash
cp .env.example .env
docker compose up --build
```

Backend: `http://localhost:8000`  
Bot service: `http://localhost:9000`  
PostgreSQL: `localhost:5432`

Frontend local run:

```bash
cd frontend
npm install
npm run dev
```

## Main backend endpoints

### Auth
- `POST /api/auth/register`
- `POST /api/auth/login`

### Meetings
- `POST /api/meetings` — requires consent
- `GET /api/meetings`
- `POST /api/meetings/{id}/start-bot`
- `POST /api/meetings/{id}/recording`
- `GET /api/meetings/{id}/report`

### Plans and payments
- `GET /api/plans`
- `POST /api/payments/checkout`
- `POST /api/payments/manual-confirm`
- `POST /api/webhooks/razorpay`

### Legal
- `GET /api/legal/consent`
- `GET /api/legal/privacy`
- `GET /api/legal/terms`

### Advanced
- `POST /api/ai/search`
- `POST /api/translate`
- `POST /api/meetings/{id}/live-transcript`
- `GET /api/meetings/{id}/live-transcript`
- `POST /api/memory`
- `GET /api/memory`
- `GET /api/analytics`
- `GET /api/premium/recordings/{meeting_id}`
- `POST /api/scheduler/auto-join`
- `POST /api/calendar/create-event/{meeting_id}`
- `GET /api/admin/dashboard`

## Hosting recommendation

- Frontend: Vercel or Netlify
- Backend: Render, Railway, or VPS
- Database: PostgreSQL on Render/Railway/Supabase/Neon/VPS
- Bot service: VPS recommended because Playwright/Chrome/FFmpeg need real server resources
- Storage: S3/R2/Supabase/Cloudinary, not local disk

## Important production warning

Before taking real money from users, complete verified payment webhooks, private cloud storage with signed URLs, deletion workflows, refund/cancellation policy, rate limiting, monitoring, backups, and full consent/legal review.

See `docs/REQUIREMENTS_TO_LAUNCH.md`, `docs/PRIVACY_POLICY.md`, and `docs/TERMS_OF_USE.md`.

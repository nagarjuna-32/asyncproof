- [x] Inspect repo structure and existing meeting/AI pipeline code
- [x] Implement new backend endpoint: POST /api/bot/meetings/{meeting_id}/upload-recording

- [x] Secure endpoint with BOT_UPLOAD_SECRET via X-Bot-Secret header

- [x] Backend: save MP4 to uploads/, write recordings path, and run transcription/summary/action/translation pipeline

- [x] Backend: update/extend DB schema only if required

- [x] Bot service: add recorder.py (ffmpeg recording with validation) and uploader.py (upload MP4 to backend endpoint)

- [x] Bot service: wire recorder/uploader into google_meet_bot.py and keep bot visible as ASYNCPROOF Assistant

- [x] Environment vars: ensure backend expects BOT_UPLOAD_SECRET and BACKEND_URL (backend .env example)

- [x] Update bot_service/requirements.txt if needed

- [ ] Quick verification commands: curl upload endpoint + end-to-end run (bot->record->upload->report)



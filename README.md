# Yojana Mitra — Notice Explainer

AI-assisted government/legal notice explainer (PS-06 AI for Bharat). Photo upload → plain-language explanation in Hindi/Marathi + deterministic escalation flag + follow-up Q&A.

## Quickstart

```bash
# backend (default: fake AI, zero keys, zero spend)
cd backend && pip install . && PYTHONPATH=src uvicorn notice_explainer.main:app --port 8000

# real AI: copy .env.example to .env, set GEMINI_API_KEY, USE_FAKE_AI=false
# real Q&A agent additionally needs the LangChain extra: pip install ".[qa]"
# (fake mode — the default — never imports LangChain)

# frontend
cd frontend && npm install && npm run dev
```

## API

| Method | Endpoint | Notes |
|---|---|---|
| POST | `/api/v1/documents` | multipart `image` (JPG/PNG ≤10MB) + `targetLanguage` (hi/mr) → 202 `{jobId}` |
| GET | `/api/v1/documents/{job_id}` | poll until `completed` / `awaiting_review` / `failed` |
| POST | `/api/v1/documents/{job_id}/ask` | JSON `{question}` → `{answer}` with disclaimer; max 10/job; 400 empty, 404 unknown job |
| POST | `/api/v1/documents/{job_id}/voice-query` | STT; E-302 text-only fallback |
| POST | `/api/v1/documents/{job_id}/voice-speech` | TTS mp3, 204 when unavailable |
| GET | `/api/v1/review/queue` | open review cases |
| POST | `/api/v1/review/{job_id}/resolve` | approve / edit / reject |
| GET | `/api/v1/documents/{job_id}/events` | SSE status + result; 120 s cap |
| GET | `/api/v1/legal-aid` | national + state/district entries |
| POST | `/api/v1/channels/whatsapp/webhook` | Twilio form webhook; 404 unless WhatsApp env is set |

WhatsApp channel needs `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`,
`TWILIO_WHATSAPP_FROM`, `PUBLIC_BASE_URL` and `WHATSAPP_HASH_SALT`
(see `backend/.env.example`); otherwise the webhook stays 404.

Every explanation and every `/ask` answer ends with the not-legal-advice disclaimer. Escalation is deterministic and never modified by the Q&A agent (see `docs/adr/0003-qa-agent.md`).

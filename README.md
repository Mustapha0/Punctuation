# Punctuate Hybrid API

A small English punctuation backend with a deterministic Python fallback and an optional AI adapter.

## Features
- `POST /analyze`: returns punctuation suggestions with offsets, confidence, and explanations.
- `GET /health`: health check.
- Python rules work even when the AI provider is absent or unavailable.
- Optional AI endpoint can be configured later without changing the frontend contract.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000/docs` for interactive API documentation.

## Example request
```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"I was tired I went to sleep early","use_ai":false}'
```

## AI integration contract
Copy `.env.example` to `.env` and configure:
- `AI_ENABLED=true`
- `AI_ENDPOINT=https://your-service/analyze`
- `AI_API_KEY=...` (optional, server-side only)

The AI endpoint should accept `{"text":"..."}` and return:
```json
{
  "suggestions": [
    {
      "mark": ",",
      "kind": "comma",
      "start": 12,
      "end": 12,
      "confidence": 0.9,
      "explanation": "A comma separates the introductory phrase.",
      "alternatives": ["."]
    }
  ]
}
```
Offsets are zero-based character positions in the exact input string. The API validates bounds and ignores malformed positions. Adapt `app/ai_adapter.py` if your provider uses a different request/response format.

## Frontend integration
Send a POST request to `/analyze` with JSON `{ "text": typedText, "use_ai": true }`.
Render each suggestion as an approval choice. Do not automatically apply ambiguous suggestions.
For production, replace `allow_origins=["*"]` in `app/main.py` with your frontend's exact origin, add rate limiting/authentication, and use HTTPS.

## Important limitation
The Python fallback is deliberately conservative and heuristic-based. It cannot reliably infer intended meaning in every sentence. For example, "Let's eat, Grandma" and "Let's eat Grandma" show why punctuation depends on context. Confidence values are rough ranking hints, not calibrated probabilities.

## Browser editor
Run the API and open `http://127.0.0.1:8000/`. The editor (in `www/`) shows suggestions above the text area with Accept and Ignore actions, marks each proposed insertion point, and checks 750 ms after you stop typing. AI is optional; if it is disabled, times out, or fails, the API uses the Python rules engine. If the API is unreachable, the editor falls back to the on-device engine.

## Android app (offline)
The Android app wraps `www/` with Capacitor and uses `www/engine.js`, a JavaScript port of the Python rules, so it needs no server.

1. Create a GitHub repository and upload the **contents** of this folder (keep `.github/workflows/build-apk.yml`).
2. Open the **Actions** tab, then run **Build Android APK** (it also runs on every push to `main`).
3. When it finishes, download the `punctuate-debug-apk` artifact, unzip it, and install `app-debug.apk` on your phone.

Local checks: `npm test` (JS engine) and `pytest` (Python engine). Keep `app/python_engine.py` and `www/engine.js` in sync.

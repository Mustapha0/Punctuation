"""Optional adapter for a future AI service.

Expected POST JSON:
  {"text": "..."}
Expected response JSON:
  {"suggestions": [
    {"mark": ",", "kind": "comma", "start": 12, "end": 12,
     "confidence": 0.9, "explanation": "...", "alternatives": []}
  ]}

Keep provider credentials on the server. Never put API keys in browser code.
"""
import os
import httpx
from .schemas import Suggestion

async def analyze_with_ai(text: str) -> list[Suggestion] | None:
    endpoint = os.getenv("AI_ENDPOINT", "").strip()
    if not endpoint or os.getenv("AI_ENABLED", "false").lower() != "true":
        return None

    headers = {"Content-Type": "application/json"}
    key = os.getenv("AI_API_KEY", "").strip()
    if key:
        headers["Authorization"] = f"Bearer {key}"

    timeout = float(os.getenv("AI_TIMEOUT_SECONDS", "12"))
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(endpoint, json={"text": text}, headers=headers)
            response.raise_for_status()
            payload = response.json()

        raw = payload.get("suggestions", [])
        result = []
        for item in raw:
            start = int(item["start"])
            end = int(item.get("end", start))
            if not (0 <= start <= len(text) and 0 <= end <= len(text) and end >= start):
                continue
            result.append(Suggestion(
                id=str(item.get("id", f"ai-{len(result)+1}")),
                mark=str(item["mark"]),
                kind=str(item.get("kind", "punctuation")),
                start=start, end=end,
                confidence=max(0, min(1, float(item.get("confidence", .7)))),
                explanation=str(item.get("explanation", "AI punctuation suggestion.")),
                alternatives=list(item.get("alternatives", []))
            ))
        return result
    except Exception:
        # Failure is deliberately non-fatal: caller falls back to Python.
        return None

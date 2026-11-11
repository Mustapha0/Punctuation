from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

try:  # optional: lets `.env` configure the AI adapter
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .schemas import AnalyzeRequest, AnalyzeResponse, Suggestion
from .python_engine import analyze_with_python
from .ai_adapter import analyze_with_ai

app = FastAPI(title="Punctuate Hybrid API", version="1.2.0")
WEB_DIR = Path(__file__).resolve().parent.parent / "www"


@app.get("/", include_in_schema=False)
async def editor():
    return FileResponse(WEB_DIR / "index.html")


# Restrict this list to your deployed frontend origin before production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def apply_suggestions(text: str, suggestions: list[Suggestion]) -> str:
    """Preview text with only terminal punctuation applied.

    In a real UI, users should approve each suggestion before applying it.
    """
    result = text
    terminal = [s for s in suggestions
                if s.start == s.end and s.mark and s.kind in ("terminal_period", "question_mark")]
    if result.rstrip().endswith((".", "!", "?")):
        return result
    for s in sorted(terminal, key=lambda x: x.start, reverse=True)[:1]:
        result = result[:s.start] + s.mark + result[s.start:]
    return result


@app.get("/health")
async def health():
    return {"status": "ok", "service": "punctuate-hybrid"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    # Do not strip: suggestion offsets must match the exact text the client sent.
    text = request.text
    python_suggestions = analyze_with_python(text)
    ai_suggestions = None
    if request.use_ai:
        ai_suggestions = await analyze_with_ai(text)

    if ai_suggestions is None:
        suggestions = python_suggestions
        engine = "python"
        notes = ["AI was not configured or was unavailable; Python fallback was used."]
    else:
        # Combine both engines. Prefer AI at the same location, retain distinct
        # Python findings as fallback coverage.
        merged = {(s.start, s.mark, s.kind): s for s in python_suggestions}
        for s in ai_suggestions:
            merged[(s.start, s.mark, s.kind)] = s
        suggestions = sorted(merged.values(), key=lambda s: (s.start, -s.confidence))
        engine = "ai+python"
        notes = ["AI and Python results were combined. Review suggestions before accepting."]
    return AnalyzeResponse(
        text=text, suggestions=suggestions,
        corrected_text=apply_suggestions(text, suggestions),
        engine=engine, notes=notes,
    )

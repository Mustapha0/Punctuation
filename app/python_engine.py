"""Conservative, explainable punctuation heuristics.

Offsets refer to positions in the original input. Suggestions are advisory:
punctuation often depends on intended meaning and style.

The same rules are implemented in JavaScript in www/engine.js so the Android
app can work fully offline. Keep both files in sync.
"""
import re
import uuid
from .schemas import Suggestion

TRANSITIONS = {
    "however", "therefore", "moreover", "nevertheless", "meanwhile",
    "fortunately", "unfortunately", "instead", "consequently", "otherwise",
    "furthermore", "firstly", "secondly", "finally",
}
QUESTION_STARTS = {
    "who", "what", "where", "when", "why", "how", "which", "whose", "whom",
    "is", "are", "am", "was", "were", "do", "does", "did", "can", "could",
    "would", "will", "should", "have", "has",
}
VERBS = (
    r"(?:am|is|are|was|were|have|has|had|will|would|can|could|should|did|do|does|"
    r"went|go|want|wanted|think|thought|know|knew|feel|felt|saw|see|need|needed|"
    r"like|liked|arrived|left|started|stopped)"
)
# Words that can end a first clause ("I was tired | I went to sleep").
PREDICATE_WORDS = {
    "happy", "tired", "late", "ready", "home", "outside", "inside", "sleepy",
    "hungry", "sick", "busy", "upset", "angry", "sad", "early",
}
# Verbs that normally take a clause as their object ("I believed he was late"),
# so a new subject after them is NOT a sentence boundary.
CLAUSE_TAKING = {
    "believed", "realized", "realised", "noticed", "decided", "agreed", "hoped",
    "feared", "claimed", "argued", "assumed", "imagined", "suggested", "learned",
    "discovered", "remembered", "wished", "expected", "guessed", "pretended",
    "explained", "showed", "proved", "worried", "believing", "realizing",
    "realising", "noticing", "thinking", "knowing", "hoping", "saying",
    "feeling", "wishing", "assuming", "imagining", "suggesting", "learning",
}
SUBJECT_WORD = re.compile(r"\b(?:I|you|he|she|it|we|they|this|that|there)\b", re.I)
SENTENCE_END = re.compile(r"[.!?][\"')\]]*\s+")
INTRO_CLAUSE = re.compile(
    r"\s*(?:After|Before|When|While|Although|If|Because|Since|Unless|Whenever)\b"
    r"[^,.!?]{2,65}(?=\s+[A-Z])"
)


def _suggest(mark, kind, start, end, confidence, explanation, alternatives=None):
    return Suggestion(
        id=str(uuid.uuid4())[:8], mark=mark, kind=kind, start=start, end=end,
        confidence=confidence, explanation=explanation,
        alternatives=alternatives or [],
    )


def _at_sentence_start(before: str) -> bool:
    return bool(re.search(r"^\s*$|[.!?][\"')\]]?\s*$|\n\s*$", before))


def analyze_with_python(text: str) -> list[Suggestion]:
    out = []

    # Introductory transition adverbs at the start of a sentence:
    # "However I disagree" -> comma after the word.
    words = "|".join(sorted(TRANSITIONS, key=len, reverse=True))
    for m in re.finditer(r"\b(" + words + r")\b(?!\s*,)", text, re.I):
        end = m.end()
        rest = text[end:]
        if not rest[:1].isspace() or not rest.strip():
            continue
        if not _at_sentence_start(text[:m.start()]):
            continue
        if m.group(1).lower() == "instead" and re.match(r"\s+of\b", rest, re.I):
            continue
        out.append(_suggest(
            ",", "comma", end, end, .91,
            f"\u201c{m.group(0)}\u201d is often followed by a comma when used as an introductory transition."))

    # Likely run-on clauses: a completed predicate followed by a new subject.
    run_on = re.compile(
        r"\b([A-Za-z']+)\s+(?=(?:I|he|she|they|we|it|you)\s+" + VERBS + r"\b)", re.I)
    for m in run_on.finditer(text):
        word = m.group(1).lower()
        if word in CLAUSE_TAKING:
            continue
        if not (word in PREDICATE_WORDS or word.endswith(("ed", "ing"))):
            continue
        # The current sentence must already contain a subject before this word.
        ends = [e.end() for e in SENTENCE_END.finditer(text[:m.start()])]
        seg_start = ends[-1] if ends else 0
        if not SUBJECT_WORD.search(text[seg_start:m.start()]):
            continue
        pos = m.end(1)
        out.append(_suggest(
            ".", "possible_sentence_boundary", pos, pos, .62,
            "This may be the end of one independent thought and the start of another. Check the intended meaning.",
            ["", ",", ";", "and"]))

    # Terminal punctuation for the last sentence.
    stripped = text.rstrip()
    if stripped and not re.search(r"[.!?][\"')\]]?$", stripped) and not stripped.endswith((",", ";", ":")):
        ends = [e.end() for e in SENTENCE_END.finditer(stripped)]
        last = stripped[ends[-1]:] if ends else stripped
        first = re.match(r"\s*([A-Za-z']+)", last)
        if first and first.group(1).lower() in QUESTION_STARTS:
            out.append(_suggest(
                "?", "question_mark", len(stripped), len(stripped), .78,
                "This sentence begins with a common question word or auxiliary. If it is a direct question, use a question mark.",
                ["."]))
        else:
            out.append(_suggest(
                ".", "terminal_period", len(stripped), len(stripped), .86,
                "A complete statement usually ends with a full stop.",
                ["?", "!"]))

    # Missing comma after a common introductory dependent clause.
    intro = INTRO_CLAUSE.match(text)
    if intro:
        out.append(_suggest(
            ",", "introductory_clause_comma", intro.end(), intro.end(), .58,
            "An introductory dependent clause is often followed by a comma. Confirm the clause boundary."))

    # Deduplicate same-position/same-mark suggestions and sort by location.
    unique = {}
    for s in out:
        unique[(s.start, s.mark, s.kind)] = s
    return sorted(unique.values(), key=lambda x: (x.start, x.end))

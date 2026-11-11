/* On-device punctuation engine. Mirrors app/python_engine.py so the Android
   app works fully offline. Keep both files in sync. */
(function (root) {
  'use strict';
  const TRANSITIONS = ['however','therefore','moreover','nevertheless','meanwhile','fortunately',
    'unfortunately','instead','consequently','otherwise','furthermore','firstly','secondly','finally'];
  const QUESTION_STARTS = new Set(['who','what','where','when','why','how','which','whose','whom',
    'is','are','am','was','were','do','does','did','can','could','would','will','should','have','has']);
  const VERBS = '(?:am|is|are|was|were|have|has|had|will|would|can|could|should|did|do|does|' +
    'went|go|want|wanted|think|thought|know|knew|feel|felt|saw|see|need|needed|like|liked|arrived|left|started|stopped)';
  const PREDICATE_WORDS = new Set(['happy','tired','late','ready','home','outside','inside','sleepy',
    'hungry','sick','busy','upset','angry','sad','early']);
  const CLAUSE_TAKING = new Set(['believed','realized','realised','noticed','decided','agreed','hoped',
    'feared','claimed','argued','assumed','imagined','suggested','learned','discovered','remembered',
    'wished','expected','guessed','pretended','explained','showed','proved','worried','believing',
    'realizing','realising','noticing','thinking','knowing','hoping','saying','feeling','wishing',
    'assuming','imagining','suggesting','learning']);
  const SUBJECT_WORD = /\b(?:I|you|he|she|it|we|they|this|that|there)\b/i;
  const SENTENCE_END = /[.!?]["')\]]*\s+/g;
  const INTRO_CLAUSE = /^\s*(?:After|Before|When|While|Although|If|Because|Since|Unless|Whenever)\b[^,.!?]{2,65}(?=\s+[A-Z])/;

  let counter = 0;
  function suggest(mark, kind, start, end, confidence, explanation, alternatives) {
    return { id: 's' + (++counter) + Math.random().toString(36).slice(2, 6), mark, kind, start, end,
      confidence, explanation, alternatives: alternatives || [] };
  }
  function atSentenceStart(before) {
    return /^\s*$|[.!?]["')\]]?\s*$|\n\s*$/.test(before);
  }
  function lastSentenceEnd(s) {
    let last = 0, m; SENTENCE_END.lastIndex = 0;
    while ((m = SENTENCE_END.exec(s)) !== null) last = m.index + m[0].length;
    return last;
  }

  function analyze(text) {
    const out = [];
    const words = TRANSITIONS.slice().sort((a, b) => b.length - a.length).join('|');
    const trRe = new RegExp('\\b(' + words + ')\\b(?!\\s*,)', 'gi');
    let m;
    while ((m = trRe.exec(text)) !== null) {
      const end = m.index + m[0].length, rest = text.slice(end);
      if (!/^\s/.test(rest) || !rest.trim()) continue;
      if (!atSentenceStart(text.slice(0, m.index))) continue;
      if (m[1].toLowerCase() === 'instead' && /^\s+of\b/i.test(rest)) continue;
      out.push(suggest(',', 'comma', end, end, 0.91,
        '\u201c' + m[0] + '\u201d is often followed by a comma when used as an introductory transition.'));
    }

    const runOn = new RegExp("\\b([A-Za-z']+)\\s+(?=(?:I|he|she|they|we|it|you)\\s+" + VERBS + '\\b)', 'gi');
    while ((m = runOn.exec(text)) !== null) {
      const word = m[1].toLowerCase();
      if (CLAUSE_TAKING.has(word)) continue;
      if (!(PREDICATE_WORDS.has(word) || word.endsWith('ed') || word.endsWith('ing'))) continue;
      const before = text.slice(0, m.index);
      if (!SUBJECT_WORD.test(before.slice(lastSentenceEnd(before)))) continue;
      const pos = m.index + m[1].length;
      out.push(suggest('.', 'possible_sentence_boundary', pos, pos, 0.62,
        'This may be the end of one independent thought and the start of another. Check the intended meaning.',
        ['', ',', ';', 'and']));
    }

    const stripped = text.replace(/\s+$/, '');
    if (stripped && !/[.!?]["')\]]?$/.test(stripped) && !/[,;:]$/.test(stripped)) {
      const last = stripped.slice(lastSentenceEnd(stripped));
      const first = last.match(/^\s*([A-Za-z']+)/);
      if (first && QUESTION_STARTS.has(first[1].toLowerCase())) {
        out.push(suggest('?', 'question_mark', stripped.length, stripped.length, 0.78,
          'This sentence begins with a common question word or auxiliary. If it is a direct question, use a question mark.',
          ['.']));
      } else {
        out.push(suggest('.', 'terminal_period', stripped.length, stripped.length, 0.86,
          'A complete statement usually ends with a full stop.', ['?', '!']));
      }
    }

    const intro = text.match(INTRO_CLAUSE);
    if (intro) {
      const p = intro[0].length;
      out.push(suggest(',', 'introductory_clause_comma', p, p, 0.58,
        'An introductory dependent clause is often followed by a comma. Confirm the clause boundary.'));
    }

    const unique = new Map();
    for (const s of out) unique.set(s.start + '|' + s.mark + '|' + s.kind, s);
    const suggestions = Array.from(unique.values()).sort((a, b) => a.start - b.start || a.end - b.end);
    return { text, suggestions, engine: 'on-device', notes: [] };
  }

  const api = { analyze };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.PunctuateEngine = api;
})(typeof window !== 'undefined' ? window : globalThis);

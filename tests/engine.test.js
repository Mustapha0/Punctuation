const assert = require('assert');
const { analyze } = require('../www/engine.js');
const has = (t, mark, kind, at) => analyze(t).suggestions.some(s => s.mark === mark && s.kind === kind && (at === undefined || s.start === at));
const none = (t, kind) => !analyze(t).suggestions.some(s => s.kind === kind);

assert(has('I like reading books', '.', 'terminal_period', 20));
assert(has('Why are you late', '?', 'question_mark'));
assert(has('However I disagree.', ',', 'comma', 7));
assert(has('I was tired I went to sleep early', '.', 'possible_sentence_boundary', 11));
assert(has('I went home. Why are you late', '?', 'question_mark'));
assert(has('When John arrived Mary left', ',', 'introductory_clause_comma', 17));
// false positives that used to fire
assert(none('I believed he was right.', 'possible_sentence_boundary'));
assert(none('I know you are right.', 'possible_sentence_boundary'));
assert(none('She came first today.', 'comma'));
assert(none('Instead of going we stayed.', 'comma'));
assert(none('However, I disagree.', 'comma'));
assert(analyze('Done.').suggestions.length === 0);
assert(has('  Hello there  ', '.', 'terminal_period', 13)); // offsets use the original string
console.log('engine tests passed');

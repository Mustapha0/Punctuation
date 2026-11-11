from app.python_engine import analyze_with_python


def has(text, mark, kind, at=None):
    return any(s.mark == mark and s.kind == kind and (at is None or s.start == at)
               for s in analyze_with_python(text))


def none(text, kind):
    return not any(s.kind == kind for s in analyze_with_python(text))


def test_terminal_period():
    assert has("I like reading books", ".", "terminal_period", 20)


def test_question_mark():
    assert has("Why are you late", "?", "question_mark")


def test_question_in_last_sentence():
    assert has("I went home. Why are you late", "?", "question_mark")


def test_transition_comma():
    assert has("However I disagree.", ",", "comma", 7)


def test_run_on():
    assert has("I was tired I went to sleep early", ".", "possible_sentence_boundary", 11)


def test_intro_clause_comma_position():
    assert has("When John arrived Mary left", ",", "introductory_clause_comma", 17)


def test_no_false_positives():
    assert none("I believed he was right.", "possible_sentence_boundary")
    assert none("I know you are right.", "possible_sentence_boundary")
    assert none("She came first today.", "comma")
    assert none("Instead of going we stayed.", "comma")
    assert none("However, I disagree.", "comma")


def test_offsets_use_original_string():
    assert has("  Hello there  ", ".", "terminal_period", 13)

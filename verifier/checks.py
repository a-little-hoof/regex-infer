"""Checks shared by the tool verifiers. Pure functions of their arguments.

The rules here are the verifier's own copy of the hidden rules: it judges what a tool returned
without trusting the tool that returned it. tests/test_rules.py holds the two copies together.
"""

import re

from contract import Case

RULES = {
    Case.WIDGET_CODE: r"[A-Z]{2}-[0-9]{3}(-R)?",
    Case.SHELF_TAG: r"[A-Z][0-9]{1,2}\.[a-z]{2}",
    Case.BATCH_REF: r"B20[0-9]{2}/[1-9][0-9]{0,2}",
    Case.SEAT_LABEL: r"[1-9][0-9]?[A-F]",
}

LONGEST_PATTERN = 120


def result(valid, message, *, score=None, **details):
    return {
        "valid": valid,
        "score": float(valid) if score is None else score,
        "message": message,
        "details": details,
    }


def accepts(case, text):
    """Whether ``case``'s hidden rule accepts ``text``, by the verifier's own copy of the rule."""
    return re.fullmatch(RULES[case], text) is not None


def _nests_quantifiers(pattern):
    """Whether a quantified group itself holds a quantifier, the shape that backtracks badly.

    The standard library cannot interrupt a running match, so the verifier refuses this shape
    rather than run a pattern it could not stop.
    """
    quantified = []  # one entry per open group: whether it holds a quantifier
    in_class = False
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if char == "\\":
            index += 2
            continue
        if in_class:
            in_class = char != "]"
        elif char == "[":
            in_class = True
        elif char == "(":
            quantified.append(False)
        elif char == ")":
            holds = quantified.pop() if quantified else False
            after = pattern[index + 1 : index + 2]
            if holds and after in ("*", "+", "{"):
                return True
            # The group's own quantifiers stay inside its parent, quantified or not.
            if quantified and (holds or after in ("*", "+", "?", "{")):
                quantified[-1] = True
        elif char in "*+{" and quantified:
            quantified[-1] = True
        index += 1
    return False


def pattern_problem(pattern):
    """What is wrong with ``pattern`` as a regular expression to run, or None."""
    if not pattern.strip():
        return "pattern must not be blank"
    if pattern != pattern.strip():
        return "pattern must have no surrounding spaces"
    if len(pattern) > LONGEST_PATTERN:
        return f"pattern must be at most {LONGEST_PATTERN} characters, not {len(pattern)}"
    try:
        re.compile(pattern)
    except re.error as error:
        return f"pattern is not a regular expression: {error}"
    if _nests_quantifiers(pattern):
        return "pattern quantifies a group that is itself quantified, which can backtrack without end"
    return None


def mislabelled(pattern, examples):
    """The examples ``pattern`` labels differently from their own label."""
    compiled = re.compile(pattern)
    return [example for example in examples if (compiled.fullmatch(example.text) is not None) != example.matches]

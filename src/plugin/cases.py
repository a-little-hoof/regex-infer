"""Each case's hidden rule and its two disjoint example sets.

The rules are invented, so a pattern has to be inferred from the examples rather than recalled. The
holdout set is what the verifier judges a submitted pattern on, so a pattern that merely lists the
visible accepted strings fails: none of them appear here.
"""

from __future__ import annotations

import re

from contract import Case, Example

# Each case's hidden rule, matched whole. The verifier keeps its own copy, so these two must agree.
RULES = {
    Case.WIDGET_CODE: r"[A-Z]{2}-[0-9]{3}(-R)?",
    Case.SHELF_TAG: r"[A-Z][0-9]{1,2}\.[a-z]{2}",
    Case.BATCH_REF: r"B20[0-9]{2}/[1-9][0-9]{0,2}",
    Case.SEAT_LABEL: r"[1-9][0-9]?[A-F]",
}

# case -> (accepted, rejected). Every rejected string is a near miss: it breaks one part of the rule.
VISIBLE = {
    Case.WIDGET_CODE: (
        ("AB-123", "ZZ-000", "QT-456-R", "MN-789", "XY-001-R"),
        ("A-123", "ABC-123", "AB-12", "AB-1234", "ab-123", "AB-123-X", "AB123", "AB-123-R-R"),
    ),
    Case.SHELF_TAG: (
        ("A1.xy", "B42.ab", "Z9.qq", "M10.zz"),
        ("A.xy", "A123.xy", "A1.XY", "A1.x", "A1.xyz", "a1.xy", "A1xy"),
    ),
    Case.BATCH_REF: (
        ("B2024/7", "B2001/42", "B2099/100", "B2000/999"),
        ("B1999/7", "B2024/0", "B2024/07", "B2024/1000", "b2024/7", "B2024-7", "B2024/"),
    ),
    Case.SEAT_LABEL: (
        ("1A", "12F", "7C", "30B"),
        ("0A", "123A", "1G", "1a", "A1", "1", "12"),
    ),
}

HOLDOUT = {
    Case.WIDGET_CODE: (
        ("CD-999", "LM-555-R", "PQ-007", "TU-010"),
        ("CD-99", "cd-999", "CD-999-S", "-123", "CD-999-R-R", "CDE-999"),
    ),
    Case.SHELF_TAG: (
        ("C7.mn", "D55.pq", "K3.aa"),
        ("C7.m", "c7.mn", "C777.mn", "C7.mnp", "C7mn", "7C.mn"),
    ),
    Case.BATCH_REF: (
        ("B2010/5", "B2045/250", "B2033/1"),
        ("B2100/5", "B2010/05", "B2010", "B2010/5/5", "B20/5"),
    ),
    Case.SEAT_LABEL: (
        ("9D", "25E", "3A"),
        ("09D", "9H", "9d", "250E", "D9"),
    ),
}


def accepts(case: Case, text: str) -> bool:
    """Whether ``case``'s hidden rule accepts ``text``."""
    return re.fullmatch(RULES[case], text) is not None


def labelled(case: Case, sets: dict[Case, tuple[tuple[str, ...], tuple[str, ...]]]) -> list[Example]:
    """``sets``'s examples for ``case``, accepted ones first."""
    accepted, rejected = sets[case]
    return [Example(text=text, matches=True) for text in accepted] + [
        Example(text=text, matches=False) for text in rejected
    ]

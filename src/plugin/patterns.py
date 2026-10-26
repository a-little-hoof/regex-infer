"""try_pattern: run a candidate pattern over the case's visible examples."""

from __future__ import annotations

import re
from pathlib import Path

from contract import Example, TryInput, TryOutput
from plugin.cases import VISIBLE, labelled


def try_pattern(given: TryInput, workspace: Path) -> TryOutput:
    pattern = given.pattern.strip()
    if not pattern:
        raise ValueError("pattern must not be blank")
    try:
        compiled = re.compile(pattern)
    except re.error as error:
        raise ValueError(f"pattern is not a regular expression: {error}") from error
    examples = labelled(given.case, VISIBLE)
    wrong = [
        Example(text=example.text, matches=example.matches)
        for example in examples
        if (compiled.fullmatch(example.text) is not None) != example.matches
    ]
    return TryOutput(
        case=given.case,
        pattern=pattern,
        wrong=wrong,
        right=len(examples) - len(wrong),
        total=len(examples),
        all_right=not wrong,
    )

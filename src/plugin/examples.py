"""sample_examples and holdout_examples: the same lookup over the visible and the held-out set."""

from __future__ import annotations

from pathlib import Path

from contract import CaseInput, ExamplesOutput
from plugin.cases import HOLDOUT, VISIBLE, labelled


def sample_examples(given: CaseInput, workspace: Path) -> ExamplesOutput:
    return ExamplesOutput(case=given.case, examples=labelled(given.case, VISIBLE))


def holdout_examples(given: CaseInput, workspace: Path) -> ExamplesOutput:
    """The task's reference tool: NanoAgent runs it out of the model's sight."""
    return ExamplesOutput(case=given.case, examples=labelled(given.case, HOLDOUT))

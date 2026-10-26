"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    SAMPLE_EXAMPLES = "sample_examples"
    TRY_PATTERN = "try_pattern"
    HOLDOUT_EXAMPLES = "holdout_examples"


class Task(Enum):
    INFER_PATTERN = "infer-pattern"


class Case(Enum):
    WIDGET_CODE = "widget-code"
    SHELF_TAG = "shelf-tag"
    BATCH_REF = "batch-ref"
    SEAT_LABEL = "seat-label"


CASE = "Which labelled example set to work from; each case hides a different rule"
PATTERN = (
    "A Python regular expression for the case's hidden rule, matched whole with re.fullmatch,"
    " e.g. [A-Z]{2}-[0-9]{3}"
)


@dataclass
class Example(Output):
    text: Annotated[str, "The example string"]
    matches: Annotated[bool, "Whether the case's hidden rule accepts this string"]


@dataclass
class CaseInput(Output):
    case: Annotated[Case, CASE]


@dataclass
class ExamplesOutput(Output):
    case: Annotated[Case, "The case the examples come from"]
    examples: Annotated[list[Example], "The labelled examples, accepted ones first"]


@dataclass
class TryInput(Output):
    case: Annotated[Case, CASE]
    pattern: Annotated[str, PATTERN]


@dataclass
class TryOutput(Output):
    case: Annotated[Case, "The case the pattern was tested on"]
    pattern: Annotated[str, "The pattern, as given without surrounding spaces"]
    wrong: Annotated[list[Example], "The visible examples the pattern labels wrongly, with the rule's own label"]
    right: Annotated[int, "How many visible examples the pattern labels correctly"]
    total: Annotated[int, "How many visible examples the pattern was tested on"]
    all_right: Annotated[bool, "Whether the pattern labels every visible example correctly"]


@dataclass
class PatternOutput(Output):
    case: Annotated[Case, "The case the pattern is for, as the task gave it"]
    pattern: Annotated[str, PATTERN]


TOOLS = {
    Tool.SAMPLE_EXAMPLES: (CaseInput, ExamplesOutput),
    Tool.TRY_PATTERN: (TryInput, TryOutput),
    Tool.HOLDOUT_EXAMPLES: (CaseInput, ExamplesOutput),
}
TASKS = {
    Task.INFER_PATTERN: (CaseInput, PatternOutput),
}

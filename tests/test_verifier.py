from __future__ import annotations

from pathlib import Path

import pytest
from slimconfig import build_output, plain_output

import verifier
from contract import TASKS, TOOLS, Case, CaseInput, ExamplesOutput, Task, Tool, TryInput
from plugin import holdout_examples, sample_examples, try_pattern
from plugin.cases import RULES
from verifier.checks import pattern_problem

CANONICAL = dict(RULES)
# Spells out the visible accepted strings: right on every example the model sees, wrong on the rest.
OVERFITTED = "AB-123|ZZ-000|QT-456-R|MN-789|XY-001-R"


# The verifier gets contract instances, as NanoAgent's sandbox builds them from JSON.
def verify_input(tool: str, value: dict) -> dict:
    return verifier.verify_input(tool, build_output(value, TOOLS[Tool(tool)][0]))


def verify_output(tool: str, input_value: dict, output_value: dict, workspace: Path) -> dict:
    given, made = TOOLS[Tool(tool)]
    return verifier.verify_output(
        tool, build_output(input_value, given), build_output(output_value, made), str(workspace)
    )


def verify_task(task: str, arguments: dict, output: dict, workspace: Path, reference: dict | None = None) -> dict:
    given, made = TASKS[Task(task)]
    pinned = None if reference is None else build_output(reference, ExamplesOutput)
    given_value, made_value = build_output(arguments, given), build_output(output, made)
    return verifier.verify_task(task, given_value, made_value, pinned, str(workspace))


def holdout(case: Case, workspace: Path) -> dict:
    return plain_output(holdout_examples(CaseInput(case=case), workspace))


def submit(case: Case, pattern: str) -> dict:
    return {"case": case.value, "pattern": pattern}


def infer(case: Case, pattern: str, workspace: Path, reference: dict | None = None) -> dict:
    reference = holdout(case, workspace) if reference is None else reference
    return verify_task("infer-pattern", {"case": case.value}, submit(case, pattern), workspace, reference)


# --- correct ---------------------------------------------------------------


@pytest.mark.parametrize("case", list(Case))
def test_the_rule_itself_is_right_on_every_held_out_example(tmp_path: Path, case: Case) -> None:
    verdict = infer(case, CANONICAL[case], tmp_path)
    assert verdict["valid"] is True and verdict["score"] == 1.0


def test_a_differently_spelled_equivalent_pattern_passes(tmp_path: Path) -> None:
    assert infer(Case.WIDGET_CODE, "[A-Z][A-Z]-[0-9][0-9][0-9](-R){0,1}", tmp_path)["valid"] is True


# --- incorrect -------------------------------------------------------------


def test_a_pattern_that_lists_the_visible_examples_is_right_on_them_and_fails_the_task(tmp_path: Path) -> None:
    # The whole point of the held-out set: this pattern is perfect on everything the model is shown.
    seen = try_pattern(TryInput(case=Case.WIDGET_CODE, pattern=OVERFITTED), tmp_path)
    assert seen.all_right is True
    verdict = infer(Case.WIDGET_CODE, OVERFITTED, tmp_path)
    assert verdict["valid"] is False
    assert sorted(verdict["details"]["wrong"]) == ["CD-999", "LM-555-R", "PQ-007", "TU-010"]


def test_a_pattern_that_accepts_anything_fails(tmp_path: Path) -> None:
    assert infer(Case.WIDGET_CODE, ".*", tmp_path)["valid"] is False


def test_a_pattern_is_matched_whole_not_as_a_prefix(tmp_path: Path) -> None:
    assert infer(Case.WIDGET_CODE, "[A-Z]{2}", tmp_path)["valid"] is False


def test_the_submitted_case_must_be_the_one_asked_for(tmp_path: Path) -> None:
    verdict = verify_task(
        "infer-pattern",
        {"case": Case.WIDGET_CODE.value},
        submit(Case.SEAT_LABEL, CANONICAL[Case.SEAT_LABEL]),
        tmp_path,
        holdout(Case.WIDGET_CODE, tmp_path),
    )
    assert verdict["valid"] is False and "not widget-code" in verdict["message"]


# --- missing ---------------------------------------------------------------


def test_a_blank_pattern_is_refused(tmp_path: Path) -> None:
    assert infer(Case.WIDGET_CODE, "", tmp_path)["valid"] is False


def test_no_held_out_examples_is_refused(tmp_path: Path) -> None:
    empty = {"case": Case.WIDGET_CODE.value, "examples": []}
    verdict = infer(Case.WIDGET_CODE, CANONICAL[Case.WIDGET_CODE], tmp_path, empty)
    assert verdict["valid"] is False and "no held-out examples" in verdict["message"]


def test_held_out_examples_labelled_against_the_rule_are_refused(tmp_path: Path) -> None:
    # The verifier does not trust the reference tool either: it re-labels with its own copy.
    tampered = holdout(Case.WIDGET_CODE, tmp_path)
    tampered["examples"][0]["matches"] = False
    verdict = infer(Case.WIDGET_CODE, CANONICAL[Case.WIDGET_CODE], tmp_path, tampered)
    assert verdict["valid"] is False and "against the rule" in verdict["message"]


# --- malformed -------------------------------------------------------------


@pytest.mark.parametrize(
    ("pattern", "message"),
    [
        ("[A-Z", "not a regular expression"),
        ("  [A-Z]{2}-[0-9]{3}(-R)?  ", "surrounding spaces"),
        ("([A-Z]+)+-[0-9]{3}", "backtrack without end"),
        ("[A-Z]{2}-[0-9]{3}" + "|x" * 60, "at most 120 characters"),
    ],
)
def test_a_pattern_the_verifier_cannot_safely_run_is_refused(tmp_path: Path, pattern: str, message: str) -> None:
    verdict = infer(Case.WIDGET_CODE, pattern, tmp_path)
    assert verdict["valid"] is False and message in verdict["message"]


@pytest.mark.parametrize(
    ("pattern", "refused"),
    [
        (r"[A-Z]{2}-[0-9]{3}(-R)?", False),  # a group quantified by ?, with nothing quantified inside
        (r"[A-Z][0-9]{1,2}\.[a-z]{2}", False),
        (r"[A-Z][A-Z]-[0-9][0-9][0-9](-R){0,1}", False),
        (r".*", False),  # a quantifier outside any group
        (r"(a|b)+", False),
        (r"(ab){2}", False),
        (r"[(+]*", False),  # a paren and a quantifier that are only characters in a class
        (r"\(a+\)+", False),  # escaped parens are not a group
        (r"(a+)+", True),
        (r"(a*)*", True),
        (r"((a+))+", True),  # nested two groups deep
        (r"(a+){2}", True),  # a counted repeat of a quantified group still backtracks
        (r"(a?b+)*", True),
    ],
)
def test_the_backtracking_guard_refuses_only_nested_quantifiers(pattern: str, refused: bool) -> None:
    # Every rule the plugin ships has to get through, so the guard may not just refuse all groups.
    problem = pattern_problem(pattern)
    assert (problem is not None) is refused, problem


# --- boundary --------------------------------------------------------------


def test_one_wrong_held_out_example_is_still_a_failure_and_scores_just_under_one(tmp_path: Path) -> None:
    # Forgets that a row may not start with 0, which only 09D catches.
    verdict = infer(Case.SEAT_LABEL, "[0-9][0-9]?[A-F]", tmp_path)
    assert verdict["valid"] is False
    assert verdict["details"]["wrong"] == ["09D"]
    assert verdict["score"] == pytest.approx(7 / 8)


def test_score_falls_to_zero_when_every_held_out_example_is_wrong(tmp_path: Path) -> None:
    # Accepts exactly what the rule rejects and rejects what it accepts.
    verdict = infer(Case.SEAT_LABEL, "09D|9H|9d|250E|D9", tmp_path)
    assert verdict["valid"] is False and verdict["score"] == 0.0


# --- the tools' own checks -------------------------------------------------


def test_sample_and_holdout_examples_are_the_case_s_own(tmp_path: Path) -> None:
    for tool, run in (("sample_examples", sample_examples), ("holdout_examples", holdout_examples)):
        given = {"case": Case.SHELF_TAG.value}
        made = plain_output(run(CaseInput(case=Case.SHELF_TAG), tmp_path))
        assert verify_input(tool, given)["valid"] is True
        assert verify_output(tool, given, made, tmp_path)["valid"] is True
        assert verify_output(tool, {"case": Case.BATCH_REF.value}, made, tmp_path)["valid"] is False


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"examples": []}, "at least one example"),
        ({"examples": [{"text": "C7.mn", "matches": True}]}, "both an accepted and a rejected"),
        ({"examples": [{"text": "C7.mn", "matches": False}, {"text": "C7.m", "matches": True}]}, "against the rule"),
    ],
)
def test_examples_that_misrepresent_the_case_are_refused(tmp_path: Path, change: dict, message: str) -> None:
    given = {"case": Case.SHELF_TAG.value}
    made = plain_output(sample_examples(CaseInput(case=Case.SHELF_TAG), tmp_path)) | change
    verdict = verify_output("sample_examples", given, made, tmp_path)
    assert verdict["valid"] is False and message in verdict["message"]


def test_a_repeated_example_is_refused(tmp_path: Path) -> None:
    given = {"case": Case.SHELF_TAG.value}
    made = plain_output(sample_examples(CaseInput(case=Case.SHELF_TAG), tmp_path))
    made["examples"] = made["examples"] + [made["examples"][0]]
    assert verify_output("sample_examples", given, made, tmp_path)["valid"] is False


def test_try_pattern_reports_what_it_really_found(tmp_path: Path) -> None:
    given = {"case": Case.SEAT_LABEL.value, "pattern": "[0-9][0-9]?[A-F]"}
    made = plain_output(try_pattern(TryInput(case=Case.SEAT_LABEL, pattern="[0-9][0-9]?[A-F]"), tmp_path))
    assert verify_input("try_pattern", given)["valid"] is True
    assert verify_output("try_pattern", given, made, tmp_path)["valid"] is True
    assert made["wrong"] == [{"text": "0A", "matches": False}]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"right": 99}, "accounted for"),
        ({"all_right": True}, "all_right"),
        ({"total": 0, "right": 0, "wrong": [], "all_right": True}, "at least one example"),
        ({"wrong": [{"text": "1A", "matches": True}], "right": 10}, "labels"),
        ({"wrong": [{"text": "0A", "matches": True}], "right": 10}, "label the rule does not give"),
    ],
)
def test_a_try_pattern_report_that_does_not_add_up_is_refused(tmp_path: Path, change: dict, message: str) -> None:
    given = {"case": Case.SEAT_LABEL.value, "pattern": "[0-9][0-9]?[A-F]"}
    made = plain_output(try_pattern(TryInput(case=Case.SEAT_LABEL, pattern="[0-9][0-9]?[A-F]"), tmp_path)) | change
    verdict = verify_output("try_pattern", given, made, tmp_path)
    assert verdict["valid"] is False and message in verdict["message"]


def test_try_pattern_refuses_an_input_it_could_not_safely_run(tmp_path: Path) -> None:
    assert verify_input("try_pattern", {"case": Case.SEAT_LABEL.value, "pattern": "([0-9]+)+"})["valid"] is False
    assert verify_input("try_pattern", {"case": Case.SEAT_LABEL.value, "pattern": "[0-9"})["valid"] is False

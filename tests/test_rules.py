"""The invariants the whole design rests on: the two copies of the rules agree, and no held-out
example is one the model was shown."""

from __future__ import annotations

import pytest

from contract import Case
from plugin.cases import HOLDOUT, RULES, VISIBLE, accepts
from verifier.checks import RULES as VERIFIER_RULES
from verifier.checks import accepts as verifier_accepts


def texts(sets: dict, case: Case) -> list[str]:
    accepted, rejected = sets[case]
    return [*accepted, *rejected]


def test_every_case_has_a_rule_and_both_example_sets() -> None:
    assert set(RULES) == set(Case)
    assert set(VISIBLE) == set(Case)
    assert set(HOLDOUT) == set(Case)


def test_the_verifier_keeps_its_own_copy_of_the_rules_in_step() -> None:
    # The verifier may not import the plugin, so it holds the rules twice on purpose.
    assert VERIFIER_RULES == RULES


@pytest.mark.parametrize("case", list(Case))
def test_both_copies_of_a_rule_judge_every_example_the_same(case: Case) -> None:
    for text in texts(VISIBLE, case) + texts(HOLDOUT, case):
        assert accepts(case, text) == verifier_accepts(case, text), text


@pytest.mark.parametrize("case", list(Case))
def test_no_held_out_example_was_shown_to_the_model(case: Case) -> None:
    assert not set(texts(HOLDOUT, case)) & set(texts(VISIBLE, case))


@pytest.mark.parametrize("case", list(Case))
def test_every_example_carries_the_label_its_rule_gives_it(case: Case) -> None:
    for sets in (VISIBLE, HOLDOUT):
        accepted, rejected = sets[case]
        assert [text for text in accepted if not accepts(case, text)] == []
        assert [text for text in rejected if accepts(case, text)] == []


@pytest.mark.parametrize("case", list(Case))
def test_each_set_holds_both_an_accepted_and_a_rejected_example(case: Case) -> None:
    for sets in (VISIBLE, HOLDOUT):
        accepted, rejected = sets[case]
        assert accepted and rejected


@pytest.mark.parametrize("case", list(Case))
def test_no_example_is_repeated(case: Case) -> None:
    for sets in (VISIBLE, HOLDOUT):
        assert len(set(texts(sets, case))) == len(texts(sets, case))

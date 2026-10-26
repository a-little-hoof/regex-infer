"""try_pattern's checks, and the infer-pattern task judged on the held-out examples."""

from .checks import accepts, mislabelled, pattern_problem, result


def verify_input(value):
    problem = pattern_problem(value.pattern)
    if problem:
        return result(False, problem)
    return result(True, "pattern is a regular expression this verifier can run")


def verify_output(input_value, output_value, workspace):
    if output_value.case is not input_value.case:
        return result(False, f"the test is for {output_value.case.value}, not {input_value.case.value}")
    if output_value.pattern != input_value.pattern.strip():
        return result(False, "output must report the pattern it was given")
    problem = pattern_problem(output_value.pattern)
    if problem:
        return result(False, problem)
    if output_value.total <= 0:
        return result(False, "the pattern must be tested on at least one example")
    counted = output_value.right + len(output_value.wrong)
    if counted != output_value.total:
        return result(False, f"{counted} examples are accounted for, not {output_value.total}")
    if output_value.all_right != (not output_value.wrong):
        return result(False, "all_right must say whether the wrong list is empty")
    for example in output_value.wrong:
        if accepts(input_value.case, example.text) != example.matches:
            return result(False, f"wrong example {example.text!r} carries a label the rule does not give it")
    missed = [example.text for example in output_value.wrong if not mislabelled(output_value.pattern, [example])]
    if missed:
        return result(False, f"the pattern labels {missed} correctly, so they are not wrong")
    return result(True, f"{output_value.right} of {output_value.total} examples are labelled correctly")


def verify_task(arguments, output, reference, workspace):
    """infer-pattern: the submitted pattern judged on held-out examples the model never saw."""
    if output.case is not arguments.case:
        return result(False, f"the pattern is for {output.case.value}, not {arguments.case.value}")
    problem = pattern_problem(output.pattern)
    if problem:
        return result(False, problem)
    if reference.case is not arguments.case:
        return result(False, f"the held-out examples are for {reference.case.value}, not {arguments.case.value}")
    examples = reference.examples
    if not examples:
        return result(False, "there are no held-out examples to judge the pattern on")
    stale = [example.text for example in examples if accepts(arguments.case, example.text) != example.matches]
    if stale:
        return result(False, f"held-out examples {stale} are labelled against the rule")
    wrong = mislabelled(output.pattern, examples)
    right = len(examples) - len(wrong)
    if wrong:
        texts = [example.text for example in wrong]
        return result(
            False,
            f"the pattern is wrong on {len(wrong)} of {len(examples)} held-out examples: {texts}",
            score=right / len(examples),
            wrong=texts,
            held_out=len(examples),
        )
    return result(True, f"the pattern is right on all {len(examples)} held-out examples", held_out=len(examples))

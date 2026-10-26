"""sample_examples and holdout_examples: the examples must be the case's own, labelled by its rule."""

from .checks import accepts, result


def verify_input(value):
    # case is an Enum member, so the only wrong value is one the type already refuses.
    return result(True, f"{value.case.value} is a case")


def verify_output(input_value, output_value, workspace):
    if output_value.case is not input_value.case:
        return result(False, f"examples are for {output_value.case.value}, not {input_value.case.value}")
    examples = output_value.examples
    if not examples:
        return result(False, "output must hold at least one example")
    texts = [example.text for example in examples]
    if len(set(texts)) != len(texts):
        return result(False, "an example is returned twice")
    for example in examples:
        if accepts(input_value.case, example.text) != example.matches:
            return result(False, f"example {example.text!r} is labelled {example.matches}, against the rule")
    labels = {example.matches for example in examples}
    if labels != {True, False}:
        return result(False, "examples must hold both an accepted and a rejected string")
    if sorted(texts, key=lambda text: not accepts(input_value.case, text)) != texts:
        return result(False, "accepted examples must come before rejected ones")
    accepted = sum(example.matches for example in examples)
    return result(True, "examples are the case's own", accepted=accepted, rejected=len(examples) - accepted)

# Regex From Examples

A plugin for inductive inference: each case hides a rule over strings, and the
task is to recover it as a regular expression from labelled examples alone. The
plugin is a standard MCP server over stdio; NanoAgent owns its launch command,
environment, input and output checks and lifecycle.

## Tools

| Tool | Does | Code |
|---|---|---|
| `sample_examples` | Returns a case's visible labelled examples, accepted strings first. Every rejected string is a near miss that breaks one part of the rule | `src/plugin/examples.py` |
| `try_pattern` | Runs a candidate pattern over a case's visible examples with `re.fullmatch` and reports which of them it labels wrongly | `src/plugin/patterns.py` |
| `holdout_examples` | Returns a case's held-out labelled examples. It is `infer-pattern`'s reference tool, so no task lists it and the model never sees its output | `src/plugin/examples.py` |

### Tasks

| Task | Does | Runner |
|---|---|---|
| `infer-pattern` | Infers a case's hidden rule and writes a regular expression for it | `agent`, with `sample_examples` and `try_pattern`, against the `holdout_examples` reference |

The four cases (`widget-code`, `shelf-tag`, `batch-ref`, `seat-label`) are
invented formats rather than well-known ones such as IPv4 or ISO dates, so the
rule has to be inferred from the examples rather than recalled. Each case
carries two disjoint example sets. `sample_examples` and `try_pattern` work
from the visible set; `holdout_examples` holds the other, and NanoAgent runs it
first in a scratch workspace the task never sees.

That split is what makes the task checkable. A pattern that merely spells out
the accepted strings it was shown is right on every visible example and wrong
on every held-out one, so `verify_task` refuses it. Scoring is the share of
held-out examples labelled correctly, and only a clean sweep is valid.

## Layout

It has the standard plugin layout, which NanoAgent requires:

```text
.
├── nanoagent.yaml   # manifest (a slimconfig ManifestConfig): id, runtime, permissions, tools, tasks
├── contract.py      # each tool's and task's typed input and output: slimconfig Output classes
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env             # needed environment variable names (none here)
├── src/plugin/      # the MCP server (__main__.py, its IMPLEMENTATIONS table), cases.py and the tools
├── tests/           # test_verifier.py and test_rules.py, the design's invariants
├── ui/              # how the page draws the outputs: renderers.js and renderers.css
├── product/         # the product page a catalog shows: product.yaml and icon.svg
└── verifier/        # deterministic verifier package: checks.py, examples.py and patterns.py
```

`contract.py` types every value: the server builds each call's input into its
class and checks its output against its own, and NanoAgent and the verifier
get the same classes. A failing tool raises, and the MCP server returns an
error result.

`verifier/` is deterministic and imports only `re` and `contract`. Because it
may not import the plugin, it keeps its own copy of the four rules and labels
every example again with it: it never takes a tool's word for what a string
is, including the reference tool's. `tests/test_rules.py` holds the two copies
in step and keeps the visible and held-out sets disjoint.

A submitted pattern is model-written, and the standard library cannot interrupt
a running match, so `verifier/checks.py` refuses a pattern before running it if
it is blank, padded, over 120 characters, not a regular expression, or
quantifies a group that is itself quantified.

## Develop and run

```bash
uv sync --extra dev
uv run pytest
```

NanoAgent passes the folder the plugin may write to as `NANOAGENT_WORKSPACE`.
No tool writes to it: every case is held in `src/plugin/cases.py`, so a run
needs no network and no files.

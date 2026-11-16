# 05 — Build the Audit Pipeline

## Purpose

Trace how CodexGuard turns files into findings. This is a source-reading lab: use the tests and synthetic fixtures as evidence, and keep all target content inert.

## Learning outcomes

- Trace one file through discovery, bounded read, parsing/decoding, evaluation, redaction, and reporting.
- Explain the supported file patterns and default work limits.
- Describe what is covered by tests and what remains a heuristic or platform assumption.

## Guided activity

1. Read the workflow diagram in the root [`README.md`](../../../README.md#how-a-scan-works).
2. Follow one TOML file from [`scanner.py`](../../../codexguard/scanner.py) into [`config_parser.py`](../../../codexguard/config_parser.py), then to `evaluate_config` in [`rules.py`](../../../codexguard/rules.py).
3. Follow a text file into `evaluate_text`; note that `AGENTS.md` and environment examples use different rule paths.
4. Read [`reporter.py`](../../../codexguard/reporter.py). Identify the available formats and the conditions for writing a report.
5. Read relevant test names in [`docs/tests-and-fixtures.md`](../../tests-and-fixtures.md) and map one test to each stage. Do not execute test code in this documentation exercise.
6. Review the [`Security Rules`](../../security-rules.md) and name one supported case and one known blind spot for each rule.

## Check your understanding

- Which four filename patterns are discovered?
- Which limits bound traversal and individual reads?
- Why is confidence not a probability of exploitability?
- What does exit code 1 indicate, and is it an enforcement block?

## Expected artifact

A sequence diagram with **root → discovery → read/parse → rules → redaction/result → report**, annotated with one control and one limitation at each stage.

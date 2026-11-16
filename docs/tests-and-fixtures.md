# Tests and Fixtures

This page describes test intent from the test files; no tests are run as part of this documentation page.

## Test organization

| File | Coverage areas |
|---|---|
| [`test_scanner.py`](../tests/test_scanner.py) | Vulnerable/hardened fixture behavior, no execution/network tripwires, bounded/malformed inputs, symlink and path-swap handling, content/mode/mtime checks, traversal limits, and unreadable directories. |
| [`test_config_parser.py`](../tests/test_config_parser.py) | Valid and malformed TOML, root containment, symlinks, missing and non-regular inputs, sanitized failures, and parser compatibility selection. |
| [`test_rules.py`](../tests/test_rules.py) | Rule matching, approval/sandbox severity context, hook wording, ordinary MCP commands, instruction patterns, and common-secret redaction. |
| [`test_reporter.py`](../tests/test_reporter.py) | JSON schema, text/Markdown rendering, redaction, output containment, exclusive creation, symlink/hard-link rejection, and partial-write cleanup. |
| [`test_cli.py`](../tests/test_cli.py) | Exit codes, severity filtering, JSON output, report path safety, fatal input errors, version/rules commands, and module entry point. |
| [`test_packaging.py`](../tests/test_packaging.py) | Package metadata, console entry point, lock separation, catalog parity, Docker controls, and workflow declarations. |

## Fixtures

- [`fixtures/vulnerable/`](../fixtures/vulnerable/) is a synthetic sample with unsafe-looking settings, project instructions, and placeholder credentials. Tests expect matches across the implemented rules; values are not real credentials.
- [`fixtures/hardened/`](../fixtures/hardened/) is a lower-risk comparison sample. It is not proof that a real repository is safe.

Fixture commands recorded by the project include:

```sh
codexguard scan fixtures/vulnerable
codexguard scan fixtures/hardened
```

Prior project documentation records 3 discovered files and 8 findings for the vulnerable fixture, and 2 files and no findings for the hardened fixture. Those are historical recorded results, not results obtained during this documentation update. The test suite itself is run with `python3 -m pytest -v` in the supported development environment described by the dependency documentation.

## Extending coverage

When changing a security-sensitive behavior, add focused synthetic tests for both matching and non-matching cases. Keep credentials fake, verify evidence redaction, and include containment or non-execution assertions when relevant. Review [`CONTRIBUTING.md`](../CONTRIBUTING.md) and the [Threat Model](threat-model.md) before changing boundaries.

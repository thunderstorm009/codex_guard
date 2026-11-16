# Source Code Guide

This guide follows one scan from CLI input to report output. It describes the current implementation and does not require executing a target repository.

## Entry points

- [`codexguard/cli.py`](../codexguard/cli.py) defines `scan`, `version`, and `rules`, parses format/severity/output options, and maps findings and errors to exit codes.
- [`codexguard/__main__.py`](../codexguard/__main__.py) supports `python -m codexguard` by delegating to the CLI.
- [`codexguard/constants.py`](../codexguard/constants.py) holds report formats, severity names, version-adjacent names, and default resource bounds.

## Scan pipeline

1. **Choose a root.** The CLI requires a path argument for `scan`; `scanner.scan` resolves it and rejects missing or non-directory roots.
2. **Pin and traverse.** `scanner.py` uses directory descriptors, `scandir`, no-follow flags, and explicit counters to walk the selected tree. Symlinked directories are skipped; relevant symlink files are not followed.
3. **Select candidate files.** `_is_relevant` allows only `AGENTS.md`, `.codex/config.toml`, `.env.example`, and `.env.*.example`.
4. **Read within bounds.** Relevant files must be regular files and are read up to the configured per-file limit. Traversal limits are defined in `constants.py`.
5. **Decode or parse as data.** `config_parser.py` parses TOML bytes through `tomllib` or the `tomli` fallback. Text is decoded as UTF-8 with invalid bytes replaced. No scanned content is evaluated as code or followed as instructions.
6. **Evaluate rules.** `rules.py` runs the config or text evaluators and constructs structured findings from the metadata catalog.
7. **Collect and redact.** `ScanResult` and its serialization include counters, reached limits, per-file errors, and findings. Secret-like values are redacted in evidence and result fields.
8. **Render.** `reporter.py` produces text, JSON, or Markdown. If explicitly requested, a report is created with exclusive creation outside the scan root; existing destinations are refused.

## Key data structures

- `Rule`: ID, name, severity, confidence, description, rationale, and recommendation.
- Finding dictionaries: rule metadata plus assessment, file, location, evidence, and remediation guidance.
- `ScanError`: sanitized file label, stable error code, and generic message.
- `ScanResult`: summary counters, findings, errors, version, and limits reached.

## Where to continue reading

| Topic | Files |
|---|---|
| CLI and exit behavior | [`cli.py`](../codexguard/cli.py), [`__main__.py`](../codexguard/__main__.py) |
| Traversal and bounds | [`scanner.py`](../codexguard/scanner.py), [`constants.py`](../codexguard/constants.py) |
| TOML parsing and file access | [`config_parser.py`](../codexguard/config_parser.py) |
| Rule logic and redaction | [`rules.py`](../codexguard/rules.py), [`security_rules.json`](../rules/security_rules.json) |
| Report formats and writes | [`reporter.py`](../codexguard/reporter.py) |
| Data flow overview | [Architecture](architecture.md) |
| Guarantees and limitations | [Security Model](security-model.md), [Threat Model](threat-model.md) |

Filesystem descriptor behavior depends on the platform. The implementation documents a fail-closed scanner path when required primitives are unavailable, but race resistance is not absolute across operating systems and filesystems.

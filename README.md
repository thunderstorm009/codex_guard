# CodexGuard

CodexGuard is an independent community project and educational security auditing CLI for OpenAI Codex CLI configuration and project files. It is not an official OpenAI product, is not endorsed by OpenAI, and has no official affiliation with OpenAI. It reads a user-selected directory and reports patterns that may deserve manual security review.

## Problem and goals

Codex configuration, project instructions, hooks, MCP definitions, and environment examples can affect how development work is carried out. CodexGuard provides a small offline review of selected files. It is designed to treat those files as untrusted data, produce evidence with common secrets redacted, and leave the selected tree unchanged.

CodexGuard is not a policy enforcement system, a malware detector, or proof that a project is safe. Findings are heuristic warnings; a clean report is not a security guarantee.

## Features

- Explicit scan root; bounded discovery of `AGENTS.md`, `.codex/config.toml`, `.env.example`, and `.env.*.example` files.
- TOML parsing using `tomllib`, with a `tomli` fallback on Python versions before 3.11.
- Symlink-aware descriptor-based traversal and bounded reads.
- Seven independent heuristic rules, with evidence, assessment, confidence, and remediation guidance.
- Pattern-based redaction of common credential formats in findings, errors, and reports.
- Text, JSON, and Markdown reports.
- Optional report output uses exclusive file creation outside the scan root and refuses existing destinations.
- No automatic fixes.

## Security boundaries

- Scanned commands, hooks, scripts, MCP servers, and instructions are never executed or followed.
- The scan path makes no network requests and does not intentionally write to the scanned tree.
- Only the explicit scan root is traversed; symlinked directories are not followed.
- Limits constrain file size, total entries, directories, depth, relevant files, and open directory descriptors.
- Report files are written only when explicitly requested and must be outside the scan root.

These controls reduce risk; they do not provide complete race protection across every OS and filesystem. Reads can update access time on filesystems configured to do so. Redaction is heuristic and cannot recognize every secret format. Details are in [Security Model](docs/security-model.md) and [Threat Model](docs/threat-model.md).

## Python versions

Package metadata declares Python `>=3.9`. Python 3.9 and 3.10 are end-of-life and are not security-supported runtimes. The development lock uses pytest 9.0.3 and targets Python 3.11 or newer; pytest 9 does not support Python 3.9. Do not use an affected older pytest release to keep an EOL test environment. The configured release CI matrix is Python 3.11, 3.12, 3.13, and 3.14. Check GitHub Actions results for the exact commit before relying on CI.

The release preflight passed 63 tests on Python 3.12.16 with locked pytest 9.0.3. A separate Python 3.9.6 run also passed 63 tests using ambient pytest 8.4.2, but that version is affected by CVE-2025-71176; treat that run as functional compatibility evidence only, not secure release validation. See [Dependency Security](docs/dependency-security.md) and [Release Readiness](docs/release-readiness.md).

## Installation

From a complete source tree with `pyproject.toml` present:

```sh
python3 -m pip install -e .
codexguard --help
python3 -m codexguard --help
```

For development on Python 3.11 or newer, install the hash-locked tools:

```sh
python3 -m pip install --require-hashes -r requirements-dev.lock
python3 -m pip install --require-hashes -r requirements-audit.lock
python3 -m pytest -v
```

The audit lock is targeted at Python 3.12. Runtime dependencies are minimal; `tomli` is used only before Python 3.11.

## Usage

```sh
codexguard scan ./project
codexguard scan ./project --format json
codexguard scan ./project --format markdown
codexguard scan ./project --min-severity HIGH
codexguard scan ./project --format json --output ./reports/audit.json
codexguard version
codexguard rules
python3 -m codexguard scan ./project
```

Options:

- `--format`: `text` (default), `json`, or `markdown`.
- `--output PATH`: create a new report outside the scan root; existing paths are refused.
- `--min-severity LEVEL`: display and return finding status for findings at or above this severity. `--severity` is a compatibility alias.
- `--quiet`: do not print the rendered report to standard output.
- `--version`: print the package version. The `version` subcommand does the same.

Exit codes: `0` completed with no qualifying findings; `1` completed with qualifying findings; `2` invalid arguments or scan root; `3` an operational scan or report-write failure. Per-file errors are reported separately and do not necessarily make the whole scan fatal.

Example from the hardened fixture:

```text
CodexGuard 0.1.0 — offline security audit
Root: .../fixtures/hardened
Files scanned: 2 | skipped: 0 | findings: 0 | errors: 0

No findings.
```

The vulnerable fixture scan currently reports 3 files, 8 findings across CG-001 through CG-007, 0 errors, and exit code 1. Its credentials are synthetic. Those matches demonstrate rule behavior, not actual compromise.

## Rules

Severity is the rule's default; CG-002 is LOW by default and becomes MEDIUM when `sandbox_mode = "danger-full-access"` is also present. Examples below are synthetic.

| Rule | Default severity | Example match | Limits and manual review |
|---|---:|---|---|
| CG-001 Dangerous Sandbox Configuration | CRITICAL | `sandbox_mode = "danger-full-access"` | Recognizes selected explicit values only. Confirm effective settings and whether the value is intentional. |
| CG-002 No-Prompt Approval Policy | LOW; MEDIUM with unrestricted sandbox value | `approval_policy = "never"` | Does not infer all layered/runtime policy. Check the effective sandbox and approval behavior for this use case. |
| CG-003 Suspicious MCP Configuration | HIGH | MCP command uses `bash -c`, `python -c`, or download piped to a shell | Shell use is a review signal, not proof of maliciousness; benign wrappers may match and obfuscation may evade detection. Verify source, arguments, and effects. |
| CG-004 CODEX_HOME Redirection | MEDIUM | `CODEX_HOME=/some/path` in an environment example | Only matches assignment-like lines in scanned environment examples. Verify the actual process environment and target directory. |
| CG-005 Potential Secret Exposure | HIGH | `API_KEY=[REDACTED]` | Pattern-based coverage is incomplete. Verify safely whether a match is real; rotate a real exposed credential. |
| CG-006 Hook Requires Manual Review | LOW | A nonempty `hooks` setting | Presence alone is not evidence of unsafe behavior. Review hook triggers, executable, and scope; CodexGuard never runs it. |
| CG-007 Suspicious Project Instructions | MEDIUM | Text resembling “ignore previous instructions” or secret exfiltration | A small phrase set can miss context or flag benign text. Review surrounding instructions and repository intent. |

Rule definitions are in `rules/security_rules.json` and the packaged copy `codexguard/security_rules.json`. Findings explain evidence and heuristic assessment; confidence refers to the pattern match, not exploitability.

## Docker

The image is configured to run as UID/GID 10001. From a complete source tree:

```sh
docker build -f docker/Dockerfile -t codexguard:latest .
mkdir -p reports
docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --memory 256m --cpus 1 --pids-limit 64 \
  --mount type=bind,src="$(pwd)/fixtures/vulnerable",dst=/scan,readonly \
  --mount type=bind,src="$(pwd)/reports",dst=/reports \
  codexguard:latest scan /scan --format json --output /reports/audit.json
```

Make the separate report directory writable by UID 10001 and keep the target mount read-only. The command returns 1 for the vulnerable fixture because findings are expected. Docker controls were exercised locally on Docker Desktop for macOS; they do not establish complete isolation or hosted Linux behavior. See [Docker Guide](docs/docker-guide.md).

## Tests and local checks

```sh
python3 -m pytest -v
python3 -m codexguard scan fixtures/vulnerable
python3 -m codexguard scan fixtures/hardened
```

The final pre-publication test run passed 63 tests on Python 3.12.16 with locked pytest 9.0.3. Earlier recorded matrix runs used Python 3.11–3.14; see [Experiment Results](docs/experiment-results.md). The GitHub workflows are configuration only until actually executed by GitHub.

## Limitations

- Discovery covers a fixed set of filenames and does not establish all effective Codex settings.
- Rules and secret matching can produce false positives and false negatives.
- Descriptor-relative operations and no-follow semantics vary across operating systems and filesystems. Same-user concurrent filesystem races cannot be fully ruled out.
- The scanner does not inspect all host state, validate executable provenance, or remediate configuration.
- Ordinary reads may update atime on some filesystems.
- The project is distributed under the MIT License; see [LICENSE](LICENSE).
- CI workflow files are not a substitute for hosted results. Check the GitHub Actions page for the exact commit before relying on CI status.

## Contributing

Before proposing code changes, run the test suite. Add regression tests for security-sensitive behavior, use synthetic credentials only, and preserve Python 3.9 syntax/runtime compatibility without relying on EOL runtimes as security-supported environments. Never add code that executes scan-target content or makes network requests during a scan. Update documentation to distinguish observed evidence from design intent and heuristic claims.

## License

CodexGuard is licensed under the [MIT License](LICENSE), copyright (c) 2026 CodexGuard contributors.

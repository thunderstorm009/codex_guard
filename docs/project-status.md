# CodexGuard Project Status

**Snapshot:** 2026-11-15, immediately before the authorized publication commit/push. The repository and Actions status below describe the pre-publication check; verify GitHub Actions after publication.

## Project overview

CodexGuard is an independent community educational CLI for offline, read-only heuristic auditing of selected Codex configuration and project files. It does not execute scanned commands, hooks, scripts, MCP servers, or instructions; it makes no network requests during scans and does not auto-remediate files.

## Implemented components

- CLI commands `scan`, `version`, and `rules`; text, JSON, and Markdown reports; severity filtering; exit codes 0–3.
- Secure TOML parser with Python-version fallback, bounded reads, path containment, sanitized errors, and descriptor-based operations.
- Scanner for `.codex/config.toml`, `AGENTS.md`, and environment example files, with bounded discovery and symlink protections.
- Seven heuristic rules with redacted evidence and remediation guidance.
- Exclusive report creation outside scan root; existing paths are refused.
- Python package metadata and console entry point, hash-locked test/audit tools, tests, vulnerable/hardened fixtures, Docker image, GitHub workflow definitions, and MIT license.

## Verification evidence

| Check | Status | Evidence |
|---|---|---|
| Python 3.12.16 full tests | PASS | pytest 9.0.3 from the development lock; 63 passed. |
| Python 3.11–3.14 | Prior recorded PASS | Phase 7.1 records 63 tests per interpreter with pytest 9.0.3; not rerun in the current pass. |
| Python 3.9 ambient pytest | Not used for release | Python 3.9.6 has pytest 8.4.2, affected by CVE-2025-71176. |
| pip-audit | PASS | pip-audit 2.10.1; runtime, dev, and audit requirements all reported no known vulnerabilities. |
| Ruff / Bandit | PASS | Ruff 0.17.5 and Bandit 1.9.4, clean. |
| Gitleaks working tree | PASS | Gitleaks 8.30.1, redacted scan of tracked/untracked non-ignored tree, exit 0, no findings. |
| Package/CLI | PASS | Source install, wheel, console/module CLI checks passed. |
| Fixtures | PASS | Vulnerable: 3 files, 8 findings, 0 errors, exit 1. Hardened: 2 files, 0 findings/errors, exit 0. |
| Docker | PASS locally | Docker Desktop/macOS restricted profile tested; see `docker-guide.md` and `release-readiness.md`. |
| GitHub Actions | Pending | No workflows/runs existed in the pre-publication remote check. Check runs after push. |

## Git and publication snapshot

- Local branch `main` already has root commit `4be1c91c070611918279b847df96e5b2e3305f20`, containing the earlier approved 33-file subset.
- The requested complete release payload, including MIT License and previously untracked source/configuration/tests/fixtures/docs, is prepared as a follow-up commit. This preserves history; it is not a new root commit.
- `origin` resolves to `github.com/thunderstorm009/codex_lab`; pre-publication lookup found no remote branch refs.
- Virtual environments, Python caches, temporary files, build artifacts, and generated reports are excluded. Only the intentional `reports/.gitkeep` is included from reports.
- The source and docs make no claim of official OpenAI endorsement. The project is licensed under MIT; see `LICENSE`.

## Remaining considerations

- Check actual GitHub Actions results after the push; no remote result is claimed here.
- Repeat dependency and secret scans before future releases.
- Review heuristic findings manually; neither clean scans nor tests guarantee security.
- Descriptor protections and Docker controls are platform-dependent; concurrent filesystem races remain a limitation.
- Python 3.9 and 3.10 are EOL and are not security-supported runtimes.

## Next steps

1. Publish the reviewed complete release payload to the verified empty remote with a normal push.
2. Inspect the `tests` and `security-checks` GitHub Actions runs and record actual outcomes.
3. Address any genuine failures without reducing test or security coverage.

# Release Readiness

**Review date:** 2026-11-15. **Scope:** pre-publication verification of the complete local CodexGuard tree after MIT license addition. This is an evidence record, not security certification.

## Summary

**Pre-publication result: PASS with remote CI pending.** Local checks on Python 3.12.16 using the hash-locked development toolchain passed. Gitleaks found no leaks in the complete non-ignored working tree; pip-audit found no known vulnerabilities in runtime, development, or audit requirements; packaging, CLI, fixtures, Ruff, Bandit, and restricted Docker checks passed.

The local repository already contains root commit `4be1c91c070611918279b847df96e5b2e3305f20` with 33 paths. This publication adds the remaining project files and MIT License in a follow-up commit to preserve that history. Before publication, the intended GitHub repository had no branch refs, workflows, or Actions runs. Hosted CI results must be checked after the push.

## Local checks

| Check | Result | Evidence |
|---|---|---|
| Full pytest suite | **PASS** | Fresh Python 3.12.16 environment; `pytest==9.0.3` from `requirements-dev.lock`; `python -m pytest -v`: 63 passed. |
| Python 3.9 ambient test environment | **NOT USED for release test** | System Python 3.9.6 has pytest 8.4.2, affected by CVE-2025-71176. Do not use that environment for release validation. |
| Ruff | **PASS** | Ruff 0.17.5 from the locked development environment: `ruff check codexguard tests`, clean. |
| Bandit | **PASS** | Bandit 1.9.4: `bandit -q -r codexguard`, no findings. |
| Dependency installation | **PASS** | Development lock installed with `--require-hashes`; package installed from source; `pip check` reported no broken requirements. |
| Package wheel | **PASS** | `python -m pip wheel --no-deps --no-build-isolation .` built `codexguard-0.1.0-py3-none-any.whl`. |
| CLI installation | **PASS** | Installed `codexguard --help`, `codexguard version`, and both fixture scans worked. Module CLI help/version also passed. |
| Vulnerable fixture | **PASS (expected findings)** | 3 files, 8 findings across CG-001–CG-007, 0 errors, exit 1. Synthetic values; evidence redacted. |
| Hardened fixture | **PASS** | 2 files, 0 findings, 0 errors, exit 0. |
| Documentation and diff checks | **PASS** | Eleven requested docs exist; local Markdown links/trailing whitespace check clean; `git diff --check` clean before staging. |

## Dependency audit

**PASS.** pip-audit 2.10.1 installed from `requirements-audit.lock` audited `requirements.txt`, `requirements-dev.lock`, and `requirements-audit.lock`; all three returned “No known vulnerabilities found.”

The lock pins pytest 9.0.3. The GitHub-reviewed [CVE-2025-71176 / GHSA-6w46-j5rx-g56g](https://github.com/advisories/GHSA-6w46-j5rx-g56g) affects pytest `<9.0.3`; 9.0.3 is patched and requires Python >=3.10. The local ambient Python 3.9 pytest 8.4.2 is affected, but was not used for release validation. Python 3.9 and 3.10 are EOL and not security-supported runtimes.

## Secret scanning

**PASS.** Gitleaks 8.30.1 scanned approximately 1.55 MB of the non-ignored working tree, including tracked and untracked candidate files:

```sh
gitleaks dir . --redact --no-banner --config .gitleaks.toml \
  --report-format json --report-path /private/tmp/codexguard-final-release-gitleaks.json
```

Exit status 0; zero findings. `.gitleaks.toml` only extends default rules; there are no directory exclusions or `.gitleaksignore`. Two line-scoped `gitleaks:allow` comments in `tests/test_rules.py` apply to synthetic test cases. No blanket test, fixture, or documentation exclusions are configured. Gitleaks detection is heuristic; a clean result does not prove no secrets exist.

The previously available history scan of the existing one-commit local history passed with Gitleaks 8.30.1 and zero findings. Run `gitleaks git` again after the publication commit is created and before pushing so the final commit is covered.

## Docker

**PASS (local Docker Desktop/macOS).** Docker 29.6.2 built `codexguard:handover-20261115` from the complete working tree. Image inspection showed UID/GID 10001:10001 and entry point `codexguard`. Restricted runs used `--network none`, read-only root and scan mounts, all capabilities dropped, no-new-privileges, 256 MiB memory, one CPU, and PID limit 64. The vulnerable fixture produced 8 findings and exit 1, with JSON written to a separate report mount; the hardened fixture exited 0. In-container checks showed UID 10001, zero effective capabilities, `NoNewPrivs=1`, and denied writes to root and scan mounts. This does not establish complete isolation or behavior on every Docker host.

## Git and destination

- Remote name: `origin`.
- Sanitized destination: `github.com/thunderstorm009/codex_lab` (exact match).
- Current branch: `main`; existing local root commit: `4be1c91c070611918279b847df96e5b2e3305f20`.
- Pre-publication `git ls-remote --heads origin` returned no refs. No unrelated remote history was present to overwrite.
- The complete release inventory consists of project source, tests, safe synthetic fixtures, docs, workflows, package/dependency metadata and locks, Docker files, and `LICENSE`. Ignored venvs, caches, build output, and reports are excluded; `reports/.gitkeep` is retained.
- No credential `.env` file or private key is included. The synthetic `fixtures/vulnerable/.env.example` is intentionally part of test fixtures and was included in the Gitleaks scan.
- The project now includes the requested root MIT License. No existing copyright notice was removed or edited.

## Remote CI

**NOT RUN before publication.** GitHub showed the repository empty, with zero registered workflows and zero workflow runs at the pre-publication check. After the authorized push, inspect both `tests` and `security-checks` runs by commit SHA and update the handover with observed job results. Do not infer success from local tests.

## Remaining limitations

- Rules and secret matching may produce false positives and false negatives.
- Symlink and descriptor protections depend on OS/filesystem behavior; concurrent same-user races cannot be completely ruled out.
- Reads may update atime on some filesystems.
- Docker evidence applies to the exercised Docker Desktop/macOS configuration.
- Python 3.9/3.10 remain declared/compatibility concerns but are EOL and should not be represented as secure supported runtimes.
- No security certification or complete coverage is claimed.

# Release Readiness — Phase 7 Pre-Commit Audit

**Review date:** 2026-11-15 (Phase 7.1)

**Environment:** macOS 26.6.1; Python 3.11.15, 3.12.16, 3.13.13, and 3.14.5 available for the supported test matrix.
**Scope:** Phase 7.1 CI matrix correction, pytest advisory verification, dependency lock validation, and local checks. No stage, commit, push, reset, clean, or history rewrite was performed.

## Local verification

| Check | Status | Evidence |
|---|---|---|
| Full test suite on maintained matrix | **PASS** | 63 passed with pytest 9.0.3 on Python 3.11.15, 3.12.16, 3.13.13, and 3.14.5 using fresh environments from the regenerated `requirements-dev.lock`. |
| Python 3.9 / 3.10 | **NOT RUN in Phase 7.1** | Both versions are end-of-life and are removed from release CI. Historical Python 3.9 runtime smoke results are not current release verification. |
| Vulnerable fixture | **PASS** | `codexguard scan fixtures/vulnerable --format json --output /private/tmp/codexguard-phase7-vulnerable.json`: 3 files, 8 findings, 0 errors, expected exit 1. Findings are heuristic; fixture values are synthetic. |
| Hardened fixture | **PASS** | `codexguard scan fixtures/hardened --format json --output /private/tmp/codexguard-phase7-hardened.json`: 2 files, 0 findings, 0 errors, exit 0. |
| Package build/install | **PASS** | `pip wheel --no-deps --no-build-isolation` built `codexguard-0.1.0-py3-none-any.whl`; source installation succeeded in each Python 3.11–3.14 test environment. CLI help/version and both fixture exit behaviors passed under Python 3.12. |
| Gitleaks working-tree scan | **PASS** | Gitleaks 8.30.1, default rules enabled, no directory exclusions, redaction enabled; complete commit-candidate tree scan returned exit 0 with no findings. Ignored `.venv` was also scanned separately and returned exit 0. |
| Gitleaks Git-history scan | **NOT RUN** | The repository has no commits, so there is no commit history to scan. The security workflow includes a full-history scan after commits exist. |
| Ruff | **PASS** | Ruff 0.17.5: `ruff check codexguard tests`, all checks passed. |
| Bandit | **PASS** | Bandit 1.9.4: `bandit -q -r codexguard`, no findings. |
| pip-audit locked environment | **PASS** | pip-audit 2.10.1 reported no known vulnerabilities in the locked test and audit environments or the runtime requirements. Local environment scan skips the unpublished CodexGuard distribution. |
| Legacy Python 3.9 temp venv | **FAIL (out-of-repo, not release input)** | A prior `pip-audit --path` found 19 advisory records, including pytest 8.4.2, in `/tmp/codexguard-py39-venv`. This environment is outside the repository and locks; it was not used or changed in Phase 7.1. |
| Workflow YAML and action lint | **PASS** | actionlint 1.7.12 checked both workflow files without errors. |
| GitHub Actions remote run | **NOT RUN** | No workflow has run on GitHub. Do not infer remote success from local checks. |
| Docker build and restricted runtime | **PASS** | Built `codexguard:phase7-audit`, inspected configured user `10001:10001`, and ran both fixtures with network disabled, read-only root and scan mounts, all capabilities dropped, no-new-privileges, 256 MiB memory, 1 CPU, and PID limit 64. Vulnerable report: 3 files, 8 findings, 0 errors, expected exit 1; hardened scan exit 0. |

## Gitleaks configuration and command

`.gitleaks.toml` contains only `[extend] useDefault = true`; no project-defined global/rule allowlist, path exclusion, baseline, or custom rule exclusion is configured. Upstream defaults remain active. The only repo inline suppressions are two Gitleaks allow comments at `tests/test_rules.py:32` and `:33`, on synthetic test values. The full scan still covers source, tests, fixtures, and documentation. There are no directory-wide exclusions.

Local verification command:

```sh
gitleaks dir . --redact --no-banner --config .gitleaks.toml \
  --report-format json --report-path /private/tmp/codexguard-phase7-final-audit.json
```

Actual exit status: **0**, no findings (about 1.55 MB scanned). The separate command `gitleaks dir .venv --redact --no-banner --report-format json --report-path /private/tmp/codexguard-phase7-final-venv.json` also exited 0 (24,221 bytes scanned). Reports were written outside the workspace and output was redacted. Gitleaks only counts eligible scanned data; the `.venv` run does not establish that every binary or generated environment artifact was inspected. These scans do not prove that all secret formats are detectable. Git history has not been scanned.

## pytest advisory and Python versions

The exact advisory is [**CVE-2025-71176 / GHSA-6w46-j5rx-g56g**](https://github.com/advisories/GHSA-6w46-j5rx-g56g), also indexed as **PYSEC-2026-1845**. GitHub's advisory says pytest `< 9.0.3` is affected and `9.0.3` is patched. It describes predictable UNIX `/tmp/pytest-of-{user}` temporary directories, with local denial-of-service and possible privilege impact. Pytest 8.4.2 is affected. The current lock pins pytest 9.0.3 and is not affected. [PyPI metadata](https://pypi.org/project/pytest/9.0.3/) says it requires Python >=3.10, covering the selected 3.11–3.14 matrix.

The old, out-of-repository Python 3.9 environment had pytest 8.4.2 and was found vulnerable by pip-audit. Pytest 8.4.2 supports Python >=3.9, but must not be used as a workaround. Python 3.9 and 3.10 are end-of-life; neither is included in the corrected release CI matrix. Full local test runs passed 63 tests on each selected interpreter: Python 3.11.15, 3.12.16, 3.13.13, and 3.14.5.

The Python Developer's Guide lists Python 3.9 end-of-life as 2025-10-31 and Python 3.10 end-of-life as 2026-10-01: [Python version status](https://devguide.python.org/versions/). Python 3.9 and 3.10 are not security-supported runtimes. Python 3.11, 3.12, and 3.13 are in security-fix status, while Python 3.14 is in bug-fix status as of this review.

See [dependency-security.md](dependency-security.md) for advisory sources, tested package versions, and lock design.

## Dependency locks and install verification

- `requirements-dev.lock` pins test/static-analysis/build dependencies and includes SHA-256 hashes. It is compiled for Python 3.11, the minimum CI runtime.
- `requirements-audit.lock` separately pins pip-audit 2.10.1 and its complete dependency graph with hashes, compiled for Python 3.12. Its dependency tree is isolated from the test tools; it installs filelock 4.2.10 and is not a runtime dependency.
- Direct development pins are pytest 9.0.3, Ruff 0.17.5, Bandit 1.9.4, Flit Core 4.2.0, and tomli 2.5.0. The tomli dev pin exercises the Python 3.9 parser fallback on the maintained matrix; runtime requirements use it only below Python 3.11. The separate audit pin is pip-audit 2.10.1.
- The development lock installed with hash checking in fresh Python 3.11–3.14 environments; the project package installed afterward. The audit lock remains compiled for Python 3.12.
- The development lock was regenerated from `requirements-dev.in` for Python 3.11 using `uv pip compile ... --generate-hashes --upgrade`; the selected dependency versions and hashes were then installed and audited.
- `requirements.txt` contains only the Python 3.9 TOML compatibility dependency (`tomli==2.5.0` under Python <3.11).
- The project build backend is pinned to Flit Core 4.2.0, which supports Python 3.9; this avoids a build backend release that required Python 3.10+.
- In a fresh Python 3.12 environment containing both locks and the installed package, `pip-audit --local --progress-spinner off` reported no known vulnerabilities. It skipped the local CodexGuard distribution because that package is not published on PyPI. Direct audits of both locks and runtime requirements also reported no known vulnerabilities.

The separate, pre-existing `/tmp/codexguard-py39-venv` is not a checked-in dependency environment. An explicit earlier `pip-audit --path` found 19 advisory records across its installed pip 26.0.1, pytest 8.4.2, and setuptools 58.0.4. This environment is excluded from the repository and must not be used for release work; it was not modified or deleted.

The CLI refused a report path under `/tmp` because that path resolves through a symlinked parent on this host. Retrying with `/private/tmp` succeeded. The rejection is expected report-path hardening behavior, not a failed scan.

Regenerate the test lock with `uv pip compile requirements-dev.in --python-version 3.11 --generate-hashes --upgrade --output-file requirements-dev.lock`. Regenerate the audit lock from its `.in` file for Python 3.12 when its inputs change. Install with hashes, run pip-audit, and test the full CI matrix after any lock update.

## CI workflow review

Both workflows trigger on `push` and `pull_request`, not `pull_request_target`, and declare least-privilege `contents: read`. Checkout sets `persist-credentials: false`. Checkout v7.0.1 and setup-python v7.1.0 are pinned to immutable SHAs; Gitleaks is pinned by image digest. The workflows define no secret references, write permissions, artifact uploads, or deployment steps. PR code runs in tests, so maintainers must keep secrets unavailable to these jobs and review workflow changes. The test workflow now runs the full suite and fixture/CLI checks on Python 3.11, 3.12, 3.13, and 3.14; it has no 3.9 or 3.10 job. The security workflow runs Ruff, Bandit, pip-audit, and Gitleaks.

Local actionlint 1.7.12 validation passed after the matrix change. GitHub-hosted execution remains **NOT RUN**. Run both workflows on the intended GitHub repository and review the results before release.

## Remote CI verification

**NOT RUN.** No GitHub Actions job has executed for this workspace during this audit. Local actionlint validates workflow syntax and structure; it is not a substitute for a hosted run. No remote repository configuration was changed.

## Git readiness

`git status --short` shows all project files as untracked; the current branch has no commits. An `origin` remote is configured in the local Git metadata, but no commit or push was made. No remote URL was added or changed in this review.

`.gitignore` covers Python caches, virtual environments, build output, local environment files, key/certificate files, temporary/log files, macOS metadata, and generated reports while preserving `reports/.gitkeep` and `.env.example` fixtures. An ignored `.venv`, `.pytest_cache`, `.ruff_cache`, `build`, and `codexguard.egg-info` are present and must be excluded. `reports/` contains only `.gitkeep`. Filename inspection found no local `.env` file, private-key/certificate candidate, or symlink outside the ignored environment; the intentional `fixtures/vulnerable/.env.example` remains a REVIEW item because it contains synthetic secret-like test data. `git diff --check` returned 0, but all project files are untracked, so Git had no tracked patch to inspect.

Recommended initial commit, after human review:

1. Review `git status --short` and inspect all untracked files, especially fixtures, lock files, and workflow configuration.
2. Confirm no local `.env`, private key, report, cache, virtualenv, or temporary output is staged; run Gitleaks again immediately before staging.
3. Stage the reviewed project files and inspect `git diff --cached --check` and `git diff --cached`.
4. Create an initial commit only after approval, then let GitHub Actions run. Do not commit or push as part of this readiness review.

## Git history verification

**NOT RUN.** `git log --oneline -5` reports that the current `main` branch has no commits. Therefore there is no Git history for Gitleaks to scan. The configured CI history scan cannot establish anything until a commit is pushed and the workflow runs.

## Known limitations

- Python 3.9 and 3.10 are end-of-life and are not release CI targets; package metadata retaining a 3.9 floor does not mean those runtimes receive security support.
- Gitleaks and CodexGuard detection are heuristic and can miss unknown, transformed, or unrecognized secrets and unsafe behavior.
- Docker controls were tested locally on Docker Desktop/macOS; they do not establish complete isolation or hosted Linux behavior.
- pip-audit cannot audit the local CodexGuard package as a published distribution because it is not on PyPI; tests, source review, and the dependency locks cover other aspects.

## Remaining release blockers

1. **Remote CI has not run.** Treat release as pending until both workflows execute successfully on the intended GitHub repository.
2. **No initial commit exists.** Gitleaks history scanning cannot run against project history, and all current files remain untracked.
3. **Legacy Python 3.9 temporary environment is vulnerable.** Keep `/tmp/codexguard-py39-venv` out of release work; it is not part of the checked-in locks. The locked pytest is patched.

This review is not a security certification.

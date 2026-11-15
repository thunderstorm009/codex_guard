# Experiment Results

This log records observed commands and results. It is not a security certification. Test and audit results are snapshots tied to the listed runtime and dependency versions.

## Current local verification — 2026-11-15

- Platform: macOS.
- `python3 --version`: Python 3.9.6.
- `python3 -m pytest -v`: **63 passed in 0.32s**, pytest 8.4.2.
- Security caveat: pytest 8.4.2 is affected by CVE-2025-71176 (fixed in pytest 9.0.3). This run demonstrates functional behavior only and is not an acceptable secure release toolchain.
- Vulnerable fixture, `python3 -m codexguard scan fixtures/vulnerable --format json`: exit 1; 3 files, 8 findings covering CG-001 through CG-007, 0 errors. Fixture credentials are synthetic; finding evidence is redacted.
- Hardened fixture, `python3 -m codexguard scan fixtures/hardened --format json`: exit 0; 2 files, 0 findings, 0 errors.
- `python3 -m codexguard --help` and `python3 -m codexguard version`: passed.
- The output of a scan was parsed for aggregate counts and rule IDs; credential values were not printed in the verification summary.

## Previously recorded matrix and dependency checks — Phase 7.1

The prior verification record states that clean Python 3.11.15, 3.12.16, 3.13.13, and 3.14.5 environments installed the hash-locked development toolchain with pytest 9.0.3, and each ran 63 tests successfully. It also records pip-audit 2.10.1 clean for the development, audit, and runtime requirements; Ruff 0.17.5 and Bandit 1.9.4 with no findings; and actionlint 1.7.12 with no workflow syntax errors. These matrix and static checks were **not rerun** during this documentation pass.

## Docker evidence — prior local run

`docker-guide.md` records a Docker Desktop/macOS build and restricted-container exercise. The tested invocation used UID 10001, a read-only root filesystem, read-only scan mount, separate writable report mount, `--network none`, dropped capabilities, no-new-privileges, 256 MiB memory, one CPU, and a PID limit of 64. The vulnerable fixture produced 8 findings and exit 1; the hardened fixture produced no findings and exit 0. The Docker run was not repeated during this documentation pass. These results do not establish complete isolation or hosted Linux behavior.

## Git history and secret scan — Phase 11

- Gitleaks version: 8.30.1.
- Command: `gitleaks git . --redact --no-banner --config .gitleaks.toml --report-format json --report-path /private/tmp/codexguard-phase11-gitleaks-history.json`.
- Result: exit 0, one available commit scanned, zero findings.
- The scan covered the available local Git history at that time, not GitHub-hosted history. A clean scan is not proof that every secret format is absent.

The final pre-publication working-tree Gitleaks run is recorded below; rerun it before future releases because files may change.

## GitHub Actions — Phase 13 remote check

On 2026-11-15, GitHub displayed the intended repository as empty. Remote ref lookup returned no branch or tag refs. The GitHub Actions API returned zero registered workflows and zero workflow runs. Therefore there are no run IDs, job results, or failed-step logs to report; remote CI is **NOT RUN**. The committed local workflow definitions are not evidence of a hosted run, and the initial commit lacks files referenced by those definitions.

## Reusable experiment template

### Experiment: [name]

- Date and time:
- CodexGuard version / commit:
- Python version and platform:
- Tool/dependency versions:
- Fixture or test corpus (never use real credentials or personal configuration):
- Exact command:
- Expected behavior:
- Observed result and exit code:
- Files scanned / skipped, findings, errors, and limit reports:
- Redaction checks:
- Read-only / no-execution checks:
- False positives, false negatives, and deviations:
- Reviewer:

## Final publication preflight — 2026-11-15

- Test environment: fresh temporary Python 3.12.16 virtual environment; dependencies installed from `requirements-dev.lock` with `--require-hashes`; pytest 9.0.3.
- `python -m pytest -v`: **63 passed**.
- Ruff 0.17.5 (`ruff check codexguard tests`): clean.
- Bandit 1.9.4 (`bandit -q -r codexguard`): no findings.
- `pip-audit` 2.10.1 audited `requirements.txt`, `requirements-dev.lock`, and `requirements-audit.lock`; each reported no known vulnerabilities.
- `pip check`: no broken requirements. Source package installation and `pip wheel --no-deps --no-build-isolation .` succeeded. Console and module CLI help/version passed.
- Console CLI fixture scans: vulnerable fixture exit 1 (3 files, 8 findings, 0 errors); hardened fixture exit 0 (2 files, no findings or errors).
- Gitleaks 8.30.1: `gitleaks dir . --redact --no-banner --config .gitleaks.toml --report-format json --report-path /private/tmp/codexguard-final-release-gitleaks.json`; exit 0, approximately 1.55 MB scanned, 0 findings. Project config has no path exclusions; two specific test-line allow comments remain for synthetic values.
- Docker 29.6.2: image `codexguard:handover-20261115` built; configured user UID/GID 10001. Restricted fixture runs used no network, read-only root/scan mounts, all capabilities dropped, no-new-privileges, memory/CPU/PID limits, and a separate writable report mount. Vulnerable report: 3 files / 8 findings / 0 errors; hardened scan exit 0. In-container checks showed UID 10001, zero effective capabilities, `NoNewPrivs=1`, and denied writes to root and scan mounts.
- Remote state was checked before publication: GitHub showed the intended repository empty, no remote refs, zero registered workflows, and zero workflow runs. No hosted result can be claimed before the follow-up commit is pushed and Actions complete.
- The ambient Python 3.9.6 pytest 8.4.2 run (63 passed) is not used as release evidence because that pytest version is affected by CVE-2025-71176.

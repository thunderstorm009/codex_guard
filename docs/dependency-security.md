# Dependency Security

**Evidence reviewed:** 2026-11-15. Dependency audit results are time-sensitive and should be repeated before release.

## pytest advisory

| Field | Verified value |
|---|---|
| CVE | CVE-2025-71176 |
| GitHub advisory | GHSA-6w46-j5rx-g56g |
| OSV/PyPI audit identifier recorded previously | PYSEC-2026-1845 |
| Affected versions | pytest `< 9.0.3` |
| Patched version | pytest `9.0.3` |
| Development lock pin | pytest `9.0.3` |
| Locked version affected? | No |
| Patched release Python requirement | Python >=3.10 |

The [GitHub-reviewed advisory](https://github.com/advisories/GHSA-6w46-j5rx-g56g) says pytest versions before 9.0.3 are affected and 9.0.3 is patched. It describes pytest's predictable UNIX `/tmp/pytest-of-{user}` temporary directory behavior, with local denial-of-service or possible privilege impact. Pytest 8.4.2 is in the affected range. This is a test-tool issue, not a CodexGuard runtime dependency.

Authoritative references:

- [GitHub Advisory Database: GHSA-6w46-j5rx-g56g](https://github.com/advisories/GHSA-6w46-j5rx-g56g)
- [pytest 9.0.3 on PyPI](https://pypi.org/project/pytest/9.0.3/)
- [Python version status](https://devguide.python.org/versions/)

## Dependency layout

| File | Purpose | Target |
|---|---|---|
| `requirements.txt` | Runtime TOML compatibility dependency | `tomli` only before Python 3.11 |
| `requirements-dev.in` / `requirements-dev.lock` | Test, lint, security, and build tools with hashes | Compiled for Python 3.11; used for the intended Python 3.11–3.14 test matrix |
| `requirements-audit.in` / `requirements-audit.lock` | `pip-audit` and its hashed dependency graph | Compiled for Python 3.12 |
| `pyproject.toml` | Package metadata, runtime dependency marker, optional tools, entry point | Declares Python >=3.9; included in the release payload prepared in this workspace |

The test and audit locks are separate so the audit tool's dependency resolution does not constrain the cross-version test lock. The build backend is pinned to Flit Core 4.2.0. The development lock pins pytest 9.0.3, Ruff 0.17.5, Bandit 1.9.4, Flit Core 4.2.0, and tomli 2.5.0.

Python 3.9 and 3.10 are end-of-life and are not security-supported runtimes. Python 3.9 remains a declared compatibility floor, not a production support promise. Pytest 9.0.3 requires Python >=3.10, so the intended safe test lock does not support running the complete suite under Python 3.9.

## Verification evidence

**Current local test invocation (2026-11-15):** `python3 -m pytest -v` ran 63 tests on macOS with Python 3.9.6 and pytest 8.4.2; all passed functionally. Because pytest 8.4.2 is affected by CVE-2025-71176, this is not evidence of a secure test environment and must not be used for release validation.

**Previously recorded dependency/matrix checks (Phase 7.1, 2026-11-15):**

- Clean Python 3.11.15, 3.12.16, 3.13.13, and 3.14.5 environments installed the hashed development lock and ran 63 tests each with pytest 9.0.3.
- pip-audit 2.10.1 reported no known vulnerabilities for the development lock, audit lock, and runtime requirements at that time.
- Ruff 0.17.5 and Bandit 1.9.4 completed without findings at that time.
- Those checks were not rerun during this documentation pass.

A separate legacy Python 3.9 virtual environment was previously reported with vulnerable pytest and other advisory records. It is outside the repository and locks and must not be treated as a supported release environment.

## Lock maintenance

Regenerate the development lock for the minimum intended CI version, preserving hashes:

```sh
uv pip compile requirements-dev.in --python-version 3.11 \
  --generate-hashes --upgrade --output-file requirements-dev.lock
```

Regenerate the audit lock from `requirements-audit.in` for Python 3.12 when inputs change. Install lock files with `--require-hashes`, run pip-audit, and rerun the supported CI matrix after updates. A hash validates an artifact against the lock; it does not independently establish publisher trust or build provenance.

## Limitations

- Advisory databases and package metadata change; repeat audits before releases.
- pip-audit cannot assess the local CodexGuard source as a published distribution when it is not published.
- The current local Python 3.9.6 environment has pytest 8.4.2; it is advisory-affected even though the test suite passed.
- A clean audit only reflects the package metadata and advisory database available at scan time.

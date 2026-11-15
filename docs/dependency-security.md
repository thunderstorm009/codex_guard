# Dependency Security

**Reviewed:** 2026-11-15 (Phase 7.1)

## pytest advisory

| Field | Verified value |
|---|---|
| CVE | CVE-2025-71176 |
| GitHub advisory | GHSA-6w46-j5rx-g56g |
| OSV/PyPI audit identifier | PYSEC-2026-1845 |
| Affected versions | pytest `< 9.0.3` |
| Fixed version | pytest `9.0.3` |
| Current lock pin | pytest `9.0.3` |
| Is the locked version affected? | **No** |
| Python support | pytest 9.0.3 requires Python >=3.10; it supports every CI matrix version (3.11–3.14) |

The [GitHub-reviewed advisory](https://github.com/advisories/GHSA-6w46-j5rx-g56g) identifies CVE-2025-71176: pytest versions below 9.0.3 are affected, and 9.0.3 is the patched version. Pytest 8.4.2 is therefore affected. On UNIX, the issue concerns predictable `/tmp/pytest-of-{user}` temporary directories and can permit local denial of service or possibly privilege impacts. The checked-in development lock pins pytest 9.0.3, so it is not affected. This is a development-tool issue, not a CodexGuard runtime dependency.

The maintained CI matrix is Python 3.11, 3.12, 3.13, and 3.14. Pytest 9.0.3 supports all four. Python 3.9 and 3.10 are end-of-life according to the [Python Developer's Guide](https://devguide.python.org/versions/) and have been removed from release CI. The project retains a Python `>=3.9` runtime metadata floor for compatibility, but does not present EOL versions as security-supported.

Authoritative references:

- [GitHub Advisory Database: GHSA-6w46-j5rx-g56g](https://github.com/advisories/GHSA-6w46-j5rx-g56g)
- [pytest 9.0.3 on PyPI](https://pypi.org/project/pytest/9.0.3/) — fixed release, Python >=3.10
- [pytest 8.4.2 on PyPI](https://pypi.org/project/pytest/8.4.2/) — Python >=3.9 compatibility

## Dependency layout

| File | Purpose | Target |
|---|---|---|
| `requirements.txt` | Runtime compatibility dependency | Python 3.9+; tomli only below 3.11 |
| `requirements-dev.in` / `requirements-dev.lock` | pytest, Ruff, Bandit, Flit Core; exact transitive versions and hashes | Compile target Python 3.11, the minimum CI version |
| `requirements-audit.in` / `requirements-audit.lock` | pip-audit and its pinned dependency graph/hashes | Compile target Python 3.12 |

The audit tool has its own lock so its dependency resolution does not constrain the application test environment. The Python 3.12 audit lock selects filelock 4.2.10. The project does not need filelock at runtime.

The package build backend uses exact `flit_core==4.2.0`; Flit Core supports Python 3.9. This replaced the previous setuptools selection because that version required Python 3.10+, which broke Python 3.9 source installation.

## Verified versions and commands

On 2026-11-15:

- Python 3.11.15, 3.12.16, 3.13.13, and 3.14.5 clean environments: pytest 9.0.3; each `python -m pytest -v` run passed 63 tests using the regenerated Python 3.11-targeted lock.
- The checked-in `requirements-dev.lock` resolves to pytest 9.0.3; CVE-2025-71176 affects `<9.0.3`, so the locked pytest is not affected.
- pip-audit 2.10.1: no known vulnerabilities in `requirements-dev.lock`, `requirements-audit.lock`, or `requirements.txt`.
- Ruff 0.17.5: clean.
- Bandit 1.9.4: clean.
- Gitleaks 8.30.1: working-tree scan clean; see [release-readiness.md](release-readiness.md).

The test and audit locks installed successfully in clean Python virtual environments using hash checking; the development lock was installed on every CI matrix version. The project package installed successfully afterward. The development lock was regenerated from `requirements-dev.in` for Python 3.11 using uv with hashes and upgrades; pip-audit and all matrix test runs were repeated.

The separate legacy Python 3.9 virtual environment at `/tmp/codexguard-py39-venv` is not part of the repository or either lock. `pip-audit --path` reported 19 advisory records across pip 26.0.1, pytest 8.4.2, and setuptools 58.0.4. Do not use that environment for release work. It was left intact; this finding does not describe the checked-in runtime or development dependency set.

## Residual limitations

- Python 3.9 and 3.10 are EOL and are not release CI runtimes. The package metadata still permits Python 3.9 runtime installation, but that compatibility floor is not a security-support claim.
- Advisory databases change; repeat dependency audits before releases.
- Hash locking verifies downloaded artifacts against recorded hashes but does not independently establish maintainer trust or build provenance.
- A clean audit reflects the database and package metadata available at the time of the scan.

import json
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from codexguard import __version__
from codexguard.rules import load_rules


PROJECT = Path(__file__).resolve().parents[1]


def test_project_metadata_and_console_entrypoint() -> None:
    metadata = tomllib.loads((PROJECT / "pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]
    assert project["name"] == "codexguard"
    assert project["version"] == __version__
    assert project["requires-python"] == ">=3.9"
    assert metadata["build-system"]["requires"] == ["flit_core==4.2.0"]
    assert project["scripts"]["codexguard"] == "codexguard.cli:main"
    assert metadata["tool"]["flit"]["module"]["name"] == "codexguard"
    test_dependencies = project["optional-dependencies"]["test"]
    assert "pytest==9.0.3; python_version >= '3.10'" in test_dependencies
    assert not any("pytest" in requirement and "python_version < '3.10'" in requirement for requirement in test_dependencies)
    assert any("python_version >= '3.10'" in requirement for requirement in project["optional-dependencies"]["test"])


def test_development_and_audit_locks_are_separated_and_hashed() -> None:
    dev_inputs = (PROJECT / "requirements-dev.in").read_text(encoding="utf-8")
    dev_lock = (PROJECT / "requirements-dev.lock").read_text(encoding="utf-8")
    audit_inputs = (PROJECT / "requirements-audit.in").read_text(encoding="utf-8")
    audit_lock = (PROJECT / "requirements-audit.lock").read_text(encoding="utf-8")

    assert "pytest==9.0.3" in dev_inputs
    assert "pip-audit" not in dev_inputs
    assert "pip-audit==2.10.1" in audit_inputs
    assert "pytest==9.0.3" in dev_lock
    assert "pip-audit==2.10.1" not in dev_lock
    assert "pip-audit==2.10.1" in audit_lock
    assert "--hash=sha256:" in dev_lock
    assert "--hash=sha256:" in audit_lock


def test_bundled_rule_metadata_matches_repository_source() -> None:
    bundled = PROJECT / "codexguard" / "security_rules.json"
    source = PROJECT / "rules" / "security_rules.json"
    assert json.loads(bundled.read_text(encoding="utf-8")) == json.loads(source.read_text(encoding="utf-8"))
    assert len(load_rules()) == 7


def test_dockerfile_and_workflows_declare_required_controls() -> None:
    dockerfile = (PROJECT / "docker" / "Dockerfile").read_text(encoding="utf-8")
    assert "FROM python:3.12-slim@sha256:" in dockerfile
    assert "USER 10001:10001" in dockerfile
    assert 'ENTRYPOINT ["codexguard"]' in dockerfile

    tests_workflow = (PROJECT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
    security_workflow = (PROJECT / ".github" / "workflows" / "security-checks.yml").read_text(encoding="utf-8")
    assert all(f'"{version}"' in tests_workflow for version in ("3.11", "3.12", "3.13", "3.14"))
    assert '"3.10"' not in tests_workflow and '"3.9"' not in tests_workflow
    assert "python39-compatibility:" not in tests_workflow
    assert "fixtures/vulnerable" in tests_workflow and "fixtures/hardened" in tests_workflow
    assert "ruff check" in security_workflow
    assert "bandit" in security_workflow and "pip-audit" in security_workflow
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1" in security_workflow
    assert "actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0" in security_workflow
    assert "ghcr.io/gitleaks/gitleaks:v8.30.1@sha256:b109bc5f8f76a38196a3e413704fc5b9e3c32360bce4e4b603bd6f45b3721dbb" in security_workflow
    assert "GITHUB_TOKEN" not in security_workflow

    gitleaks_config = (PROJECT / ".gitleaks.toml").read_text(encoding="utf-8")
    assert "useDefault = true" in gitleaks_config
    assert "paths =" not in gitleaks_config

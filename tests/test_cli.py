import json
import subprocess
import sys
from pathlib import Path

from codexguard.cli import main


PROJECT = Path(__file__).resolve().parents[1]


def test_cli_exit_codes_and_severity_filter(capsys: object) -> None:
    vulnerable = PROJECT / "fixtures" / "vulnerable"
    hardened = PROJECT / "fixtures" / "hardened"
    assert main(["scan", str(vulnerable), "--quiet", "--severity", "CRITICAL"]) == 1
    assert main(["scan", str(hardened), "--quiet"]) == 0


def test_cli_json_output(capsys: object) -> None:
    code = main(["scan", str(PROJECT / "fixtures" / "hardened"), "--format", "json"])
    assert code == 0
    output = capsys.readouterr().out
    assert json.loads(output)["tool"] == "CodexGuard"


def test_cli_output_path_safety(tmp_path: Path) -> None:
    root = PROJECT / "fixtures" / "hardened"
    assert main(["scan", str(root), "--quiet", "--output", str(root / "result.json")]) == 2


def test_cli_missing_root_is_fatal(capsys: object, tmp_path: Path) -> None:
    assert main(["scan", str(tmp_path / "missing"), "--quiet"]) == 2
    assert "unavailable or invalid" in capsys.readouterr().err


def test_cli_fatal_error_does_not_echo_secret_like_path(capsys: object, tmp_path: Path) -> None:
    secret_path = tmp_path / "sk-FAKE_PATH_SECRET_0123456789abcdef"
    assert main(["scan", str(secret_path), "--quiet"]) == 2
    assert "FAKE_PATH_SECRET" not in capsys.readouterr().err


def test_version_and_rules_commands(capsys: object) -> None:
    assert main(["version"]) == 0
    assert "CodexGuard 0.1.0" in capsys.readouterr().out
    assert main(["rules"]) == 0
    output = capsys.readouterr().out
    assert "CG-001" in output and "CG-007" in output


def test_min_severity_alias_and_legacy_option() -> None:
    vulnerable = str(PROJECT / "fixtures" / "vulnerable")
    assert main(["scan", vulnerable, "--quiet", "--min-severity", "CRITICAL"]) == 1
    assert main(["scan", vulnerable, "--quiet", "--severity", "CRITICAL"]) == 1


def test_report_write_failure_returns_operational_exit_code(tmp_path: Path, capsys: object) -> None:
    root = PROJECT / "fixtures" / "hardened"
    report = tmp_path / "already-exists.json"
    report.write_text("preserve", encoding="utf-8")
    assert main(["scan", str(root), "--quiet", "--output", str(report)]) == 3
    assert report.read_text(encoding="utf-8") == "preserve"
    assert "could not be completed safely" in capsys.readouterr().err


def test_module_entrypoint_help_and_scan() -> None:
    help_result = subprocess.run(
        [sys.executable, "-m", "codexguard", "--help"],
        cwd=str(PROJECT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    assert help_result.returncode == 0
    assert "scan" in help_result.stdout
    scan_result = subprocess.run(
        [sys.executable, "-m", "codexguard", "scan", str(PROJECT / "fixtures" / "hardened"), "--quiet"],
        cwd=str(PROJECT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    assert scan_result.returncode == 0

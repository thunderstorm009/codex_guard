import json
import os
from pathlib import Path

import pytest

from codexguard.reporter import render_json, render_markdown, render_text, write_report
from codexguard import reporter
from codexguard.scanner import ScanResult


def sample() -> ScanResult:
    return ScanResult(
        scan_root="/tmp/example",
        files_scanned=1,
        findings=[{
            "rule_id": "CG-005", "rule_name": "Potential Secret Exposure", "severity": "HIGH",
            "title": "Potential Secret Exposure", "file": ".env.example", "location": "line 1",
            "description": "A credential pattern was found.", "evidence": "API_KEY=[REDACTED]",
            "assessment": "Heuristic match; verify the effective behavior in context.", "confidence": "MEDIUM",
            "why_it_matters": "It may be exposed.", "recommendation": "Remove and rotate it.",
        }],
    )


def test_json_report_schema() -> None:
    report = json.loads(render_json(sample()))
    assert report["tool"] == "CodexGuard"
    assert report["summary"]["findings"] == 1
    assert report["findings"][0]["evidence"] == "API_KEY=[REDACTED]"
    assert report["findings"][0]["confidence"] == "MEDIUM"


def test_reports_redact_secret_like_paths_and_errors() -> None:
    from codexguard.scanner import ScanError

    secret = "sk-FAKE_PATH_SECRET_0123456789abcdef"
    result = ScanResult(
        scan_root="/tmp/" + secret,
        errors=[ScanError(secret + ".toml", "read_error", "failed while reading " + secret)],
        findings=[dict(sample().findings[0], file=secret + ".env.example")],
    )
    report = render_json(result)
    assert secret not in report
    assert secret not in render_markdown(result)
    assert secret not in render_text(result)


def test_markdown_and_text_reports_render() -> None:
    assert "Potential Secret Exposure" in render_markdown(sample())
    assert "[HIGH] CG-005" in render_text(sample())


def test_report_output_rejects_scan_root_paths(tmp_path: Path) -> None:
    root = tmp_path / "scan"
    root.mkdir()
    with pytest.raises(ValueError):
        write_report("no", root / "report.json", root)


def test_report_output_writes_explicit_external_file(tmp_path: Path) -> None:
    root = tmp_path / "scan"
    root.mkdir()
    destination = tmp_path / "reports" / "result.json"
    destination.parent.mkdir()
    write_report("{}\n", destination, root)
    assert destination.read_text(encoding="utf-8") == "{}\n"


def test_report_output_refuses_existing_file(tmp_path: Path) -> None:
    root = tmp_path / "scan"
    root.mkdir()
    destination = tmp_path / "existing.json"
    destination.write_text("keep me", encoding="utf-8")

    with pytest.raises(ValueError):
        write_report("replace me", destination, root)
    assert destination.read_text(encoding="utf-8") == "keep me"


def test_report_output_refuses_symlink_destination(tmp_path: Path) -> None:
    root = tmp_path / "scan"
    root.mkdir()
    target = tmp_path / "target.json"
    target.write_text("keep me", encoding="utf-8")
    link = tmp_path / "report.json"
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks unavailable")

    with pytest.raises(ValueError):
        write_report("replace me", link, root)
    assert target.read_text(encoding="utf-8") == "keep me"


def test_report_output_refuses_symlink_parent(tmp_path: Path) -> None:
    root = tmp_path / "scan"
    root.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    link = tmp_path / "linked"
    try:
        link.symlink_to(external, target_is_directory=True)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks unavailable")

    with pytest.raises(ValueError):
        write_report("{}", link / "result.json", root)
    assert not (external / "result.json").exists()


def test_report_output_refuses_hard_link_to_scanned_file(tmp_path: Path) -> None:
    root = tmp_path / "scan"
    root.mkdir()
    source = root / "important.txt"
    source.write_text("do not overwrite", encoding="utf-8")
    link = tmp_path / "report.json"
    try:
        os.link(source, link)
    except (NotImplementedError, OSError):
        pytest.skip("hard links unavailable")

    with pytest.raises(ValueError):
        write_report("overwrite attempt", link, root)
    assert source.read_text(encoding="utf-8") == "do not overwrite"


def test_failed_report_write_removes_partial_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "scan"
    root.mkdir()
    destination = tmp_path / "partial.json"
    real_write = os.write

    def fail_write(fd: int, data: bytes) -> int:
        real_write(fd, data[:2])
        raise OSError("simulated write failure")

    monkeypatch.setattr(reporter.os, "write", fail_write)
    with pytest.raises(ValueError):
        write_report("partial content", destination, root)
    assert not destination.exists()

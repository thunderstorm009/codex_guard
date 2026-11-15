"""Text, JSON, and Markdown report rendering and guarded file output."""

import json
import os
from pathlib import Path

from .constants import APP_NAME
from .scanner import ScanResult


class ReportWriteError(ValueError):
    """Raised when an otherwise valid report destination cannot be written."""


def render_json(result: ScanResult) -> str:
    return json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n"


def render_markdown(result: ScanResult) -> str:
    report = result.to_dict()
    summary = report["summary"]
    lines = [
        "# {} Security Audit".format(APP_NAME),
        "",
        "- Scan root: `{}`".format(report["scan_root"]),
        "- Files scanned: {}".format(summary["files_scanned"]),
        "- Files skipped: {}".format(summary["files_skipped"]),
        "- Findings: {}".format(summary["findings"]),
        "- Errors: {}".format(summary["errors"]),
        "- Limits reached: {}".format(", ".join(summary["limits_reached"]) or "none"),
        "",
        "## Findings",
        "",
    ]
    if not report["findings"]:
        lines.append("No findings.")
    for finding in report["findings"]:
        lines.extend([
            "### {} — {} ({})".format(finding["rule_id"], finding["title"], finding["severity"]),
            "",
            "- File: `{}`".format(finding["file"]),
            "- Location: `{}`".format(finding["location"]),
            "- Description: {}".format(finding["description"]),
            "- Assessment: {} (confidence: {})".format(finding["assessment"], finding["confidence"]),
            "- Evidence: `{}`".format(finding["evidence"].replace("`", "\\`")),
            "- Why it matters: {}".format(finding["why_it_matters"]),
            "- Recommendation: {}".format(finding["recommendation"]),
            "",
        ])
    lines.extend(["## Scan errors", ""])
    if report["errors"]:
        for error in report["errors"]:
            lines.append("- `{}` ({}): {}".format(error["file"], error["code"], error["message"]))
    else:
        lines.append("None.")
    return "\n".join(lines) + "\n"


def render_text(result: ScanResult) -> str:
    report = result.to_dict()
    summary = report["summary"]
    lines = [
        "{} {} — offline security audit".format(APP_NAME, result.version),
        "Root: {}".format(report["scan_root"]),
        "Files scanned: {} | skipped: {} | findings: {} | errors: {}".format(
            summary["files_scanned"], summary["files_skipped"], summary["findings"], summary["errors"]
        ),
    ]
    if summary["limits_reached"]:
        lines.append("Limits reached: {}".format(", ".join(summary["limits_reached"])))
    for finding in report["findings"]:
        lines.extend([
            "",
            "[{}] {} {} — {}".format(finding["severity"], finding["rule_id"], finding["title"], finding["file"]),
            "  {}".format(finding["description"]),
            "  Assessment: {} (confidence: {})".format(finding["assessment"], finding["confidence"]),
            "  Evidence: {}".format(finding["evidence"]),
            "  Fix: {}".format(finding["recommendation"]),
        ])
    for error in report["errors"]:
        lines.append("ERROR {} ({}): {}".format(error["file"], error["code"], error["message"]))
    if not report["findings"]:
        lines.append("\nNo findings.")
    return "\n".join(lines) + "\n"


def render(result: ScanResult, output_format: str) -> str:
    if output_format == "json":
        return render_json(result)
    if output_format == "markdown":
        return render_markdown(result)
    if output_format == "text":
        return render_text(result)
    raise ValueError("unsupported report format")


def write_report(content: str, output_path: Path, scan_root: Path) -> None:
    """Create a new report outside the scan root without overwriting data."""
    root = scan_root.resolve(strict=True)
    requested = Path(output_path)
    lexical = requested.absolute()
    if any(parent.is_symlink() for parent in lexical.parents):
        raise ValueError("report parent directories must not be symlinks")
    destination = requested.resolve(strict=False)
    try:
        destination.relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError("report output must be outside the scan root")
    if requested.is_symlink():
        raise ValueError("report output must not be a symlink")
    if not destination.parent.is_dir():
        raise ValueError("report parent directory must already exist")

    parent_fd = -1
    file_fd = -1
    name = destination.name
    try:
        parent_fd = _open_parent_directory(destination.parent)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NONBLOCK", 0)
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        if parent_fd >= 0:
            file_fd = os.open(name, flags, 0o600, dir_fd=parent_fd)
        else:
            file_fd = os.open(str(destination), flags, 0o600)
        payload = content.encode("utf-8")
        offset = 0
        while offset < len(payload):
            count = os.write(file_fd, payload[offset:])
            if count <= 0:
                raise OSError("short report write")
            offset += count
    except (OSError, ValueError):
        if file_fd >= 0:
            _remove_partial_report(name, destination, parent_fd, file_fd)
        raise ReportWriteError("report could not be created safely") from None
    finally:
        if file_fd >= 0:
            try:
                os.close(file_fd)
            except OSError:
                pass
        if parent_fd >= 0:
            try:
                os.close(parent_fd)
            except OSError:
                pass


def _open_parent_directory(parent: Path) -> int:
    """Open an absolute parent by descriptor without following symlinks."""
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    if nofollow and directory_flag and os.open in getattr(os, "supports_dir_fd", set()):
        parts = parent.parts
        descriptor = os.open(parent.anchor, os.O_RDONLY | directory_flag | nofollow)
        try:
            for component in parts[1:]:
                next_descriptor = os.open(
                    component,
                    os.O_RDONLY | directory_flag | nofollow,
                    dir_fd=descriptor,
                )
                try:
                    os.close(descriptor)
                except OSError:
                    pass
                descriptor = next_descriptor
            return descriptor
        except Exception:
            try:
                os.close(descriptor)
            except OSError:
                pass
            raise
    return -1


def _remove_partial_report(name: str, destination: Path, parent_fd: int, file_fd: int) -> None:
    """Remove only the file this call created, when its identity still matches."""
    try:
        original = os.fstat(file_fd)
        if parent_fd >= 0:
            current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            if (current.st_dev, current.st_ino) == (original.st_dev, original.st_ino):
                os.unlink(name, dir_fd=parent_fd)
        else:
            current = os.lstat(destination)
            if (current.st_dev, current.st_ino) == (original.st_dev, original.st_ino):
                os.unlink(destination)
    except OSError:
        pass

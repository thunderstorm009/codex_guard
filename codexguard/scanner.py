"""Bounded, offline discovery and auditing for Codex project files."""

import os
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from . import __version__
from .config_parser import ConfigInputError, ConfigParseError, parse_toml_bytes
from .constants import (
    APP_NAME,
    DEFAULT_MAX_DIRECTORIES,
    DEFAULT_MAX_DEPTH,
    DEFAULT_MAX_ENTRIES,
    DEFAULT_MAX_FILE_BYTES,
    DEFAULT_MAX_FILES,
    DEFAULT_MAX_OPEN_DIRECTORIES,
)
from .rules import Rule, evaluate_config, evaluate_text, load_rules, redact


@dataclass
class ScanError:
    file: str
    code: str
    message: str


@dataclass
class ScanResult:
    scan_root: str
    scan_root_path: Optional[str] = None
    files_scanned: int = 0
    files_skipped: int = 0
    entries_visited: int = 0
    directories_visited: int = 0
    limits_reached: List[str] = field(default_factory=list)
    findings: List[Dict[str, str]] = field(default_factory=list)
    errors: List[ScanError] = field(default_factory=list)
    version: str = __version__

    def to_dict(self) -> Dict[str, object]:
        safe_findings = [
            {key: redact(str(value)) for key, value in finding.items()}
            for finding in self.findings
        ]
        safe_errors = [
            {"file": redact(error.file), "code": error.code, "message": redact(error.message)}
            for error in self.errors
        ]
        return {
            "tool": APP_NAME,
            "version": self.version,
            "scan_root": redact(self.scan_root),
            "summary": {
                "files_scanned": self.files_scanned,
                "files_skipped": self.files_skipped,
                "entries_visited": self.entries_visited,
                "directories_visited": self.directories_visited,
                "findings": len(safe_findings),
                "errors": len(safe_errors),
                "limits_reached": self.limits_reached,
            },
            "findings": safe_findings,
            "errors": safe_errors,
        }


def _is_relevant(path: Path) -> Optional[str]:
    name = path.name
    if name == "AGENTS.md":
        return "instructions"
    if name == "config.toml" and path.parent.name == ".codex":
        return "toml"
    if name == ".env.example" or (name.startswith(".env.") and name.endswith(".example")):
        return "environment"
    return None


def _close_quietly(descriptor: int) -> None:
    try:
        os.close(descriptor)
    except OSError:
        pass


def _open_root_directory(root: Path) -> int:
    """Pin every root component without following symlinks."""
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    if not nofollow or not directory_flag:
        raise ConfigInputError("unsupported_platform", "safe descriptor-based scanning is unavailable")
    descriptor = os.open(root.anchor, os.O_RDONLY | directory_flag | nofollow)
    try:
        for component in root.parts[1:]:
            next_descriptor = os.open(
                component, os.O_RDONLY | directory_flag | nofollow, dir_fd=descriptor
            )
            _close_quietly(descriptor)
            descriptor = next_descriptor
        return descriptor
    except Exception:
        _close_quietly(descriptor)
        raise


def _read_entry(descriptor: int, name: str, max_bytes: int) -> bytes:
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    nonblock = getattr(os, "O_NONBLOCK", 0)
    file_descriptor = os.open(name, os.O_RDONLY | nofollow | nonblock, dir_fd=descriptor)
    try:
        info = os.fstat(file_descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise ConfigParseError("not_regular_file", "input is not a regular file")
        if info.st_size > max_bytes:
            raise ConfigInputError("file_too_large", "input file exceeds the size limit")
        chunks = []
        remaining = max_bytes + 1
        while remaining:
            chunk = os.read(file_descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        if len(data) > max_bytes:
            raise ConfigInputError("file_too_large", "input file exceeds the size limit")
        return data
    finally:
        _close_quietly(file_descriptor)


def _inspect_entry(
    result: ScanResult,
    relative: Path,
    name: str,
    kind: str,
    directory_fd: int,
    max_file_bytes: int,
    rules: List[Rule],
) -> None:
    label = relative.as_posix()
    try:
        content = _read_entry(directory_fd, name, max_file_bytes)
        if kind == "toml":
            config = parse_toml_bytes(content, max_bytes=max_file_bytes)
            result.findings.extend(evaluate_config(config, label, rules))
        else:
            text = content.decode("utf-8", errors="replace")
            result.findings.extend(evaluate_text(text, label, kind, rules))
        result.files_scanned += 1
    except ConfigInputError as exc:
        result.files_skipped += 1
        result.errors.append(ScanError(redact(label), exc.code, redact(exc.message)))
    except OSError:
        result.files_skipped += 1
        result.errors.append(ScanError(redact(label), "file_read_error", "input file could not be read safely"))
    except Exception:
        result.files_skipped += 1
        result.errors.append(ScanError(redact(label), "scan_error", "file could not be safely inspected"))


def _walk_and_inspect(
    root: Path,
    result: ScanResult,
    max_file_bytes: int,
    max_files: int,
    max_entries: int,
    max_directories: int,
    max_depth: int,
    max_open_directories: int,
    rules: List[Rule],
) -> None:
    if os.scandir not in getattr(os, "supports_fd", set()):
        raise ConfigInputError("unsupported_platform", "safe descriptor-based scanning is unavailable")
    root_fd = _open_root_directory(root)
    try:
        root_info = os.stat(str(root), follow_symlinks=False)
        pinned_info = os.fstat(root_fd)
        if (root_info.st_dev, root_info.st_ino) != (pinned_info.st_dev, pinned_info.st_ino):
            raise ConfigInputError("scan_root_changed", "scan root changed during validation")
    except Exception:
        _close_quietly(root_fd)
        raise

    pending = [(root_fd, Path("."), 0)]
    relevant_count = 0
    stop = False
    try:
        while pending and not stop:
            directory_fd, relative_dir, depth = pending.pop()
            if result.directories_visited >= max_directories:
                result.limits_reached.append("max_directories")
                _close_quietly(directory_fd)
                break
            result.directories_visited += 1
            children = []
            try:
                with os.scandir(directory_fd) as iterator:
                    while True:
                        if result.entries_visited >= max_entries:
                            result.limits_reached.append("max_entries")
                            stop = True
                            break
                        try:
                            entry = next(iterator)
                        except StopIteration:
                            break
                        result.entries_visited += 1
                        relative = relative_dir / entry.name
                        try:
                            if entry.is_symlink():
                                if _is_relevant(relative) is not None:
                                    result.files_skipped += 1
                                continue
                            if entry.is_dir(follow_symlinks=False):
                                if depth >= max_depth:
                                    if "max_depth" not in result.limits_reached:
                                        result.limits_reached.append("max_depth")
                                    continue
                                if result.directories_visited + len(pending) + len(children) >= max_directories:
                                    if "max_directories" not in result.limits_reached:
                                        result.limits_reached.append("max_directories")
                                    continue
                                if len(pending) + len(children) >= max_open_directories - 1:
                                    if "max_open_directories" not in result.limits_reached:
                                        result.limits_reached.append("max_open_directories")
                                    continue
                                dir_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
                                try:
                                    child_fd = os.open(entry.name, dir_flags, dir_fd=directory_fd)
                                except OSError:
                                    result.errors.append(ScanError(
                                        redact(relative.as_posix()), "directory_read_error",
                                        "a directory could not be safely inspected",
                                    ))
                                    continue
                                children.append((child_fd, relative, depth + 1))
                                continue
                            kind = _is_relevant(relative)
                            if kind is None:
                                continue
                            if relevant_count >= max_files:
                                if "max_relevant_files" not in result.limits_reached:
                                    result.limits_reached.append("max_relevant_files")
                                result.files_skipped += 1
                                stop = True
                                break
                            relevant_count += 1
                            _inspect_entry(result, relative, entry.name, kind, directory_fd, max_file_bytes, rules)
                        except OSError:
                            if _is_relevant(relative) is not None:
                                result.files_skipped += 1
                                result.errors.append(ScanError(redact(relative.as_posix()), "file_read_error", "input file could not be safely inspected"))
                        if result.entries_visited >= max_entries:
                            result.limits_reached.append("max_entries")
                            stop = True
                            break
            except OSError:
                result.errors.append(ScanError(redact(relative_dir.as_posix()), "directory_read_error", "a directory could not be inspected"))
            finally:
                _close_quietly(directory_fd)
            if stop:
                for child_fd, _, _ in children:
                    _close_quietly(child_fd)
                break
            pending.extend(reversed(children))
    finally:
        for descriptor, _, _ in pending:
            _close_quietly(descriptor)


def scan(
    scan_root: Path,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_files: int = DEFAULT_MAX_FILES,
    max_entries: int = DEFAULT_MAX_ENTRIES,
    max_directories: int = DEFAULT_MAX_DIRECTORIES,
    max_depth: int = DEFAULT_MAX_DEPTH,
    max_open_directories: int = DEFAULT_MAX_OPEN_DIRECTORIES,
    rules: Optional[List[Rule]] = None,
) -> ScanResult:
    """Audit only the explicitly selected directory; never execute its contents."""
    try:
        root = Path(scan_root).resolve(strict=True)
        if not root.is_dir():
            raise ValueError("invalid root")
    except (OSError, RuntimeError, TypeError, ValueError):
        raise ConfigInputError("invalid_scan_root", "scan root is unavailable or invalid") from None

    result = ScanResult(scan_root=redact(str(root)), scan_root_path=str(root))
    active_rules = rules if rules is not None else load_rules()
    try:
        _walk_and_inspect(
            root, result, max_file_bytes, max_files, max_entries, max_directories,
            max_depth, max_open_directories, active_rules,
        )
    except ConfigInputError:
        raise
    except (OSError, RuntimeError, TypeError):
        raise ConfigInputError("scan_failed", "scan could not safely inspect the selected directory") from None

    # Defensively sanitize every user-derived field before serialization.
    for finding in result.findings:
        for key in ("file", "location", "evidence", "description", "why_it_matters", "recommendation", "title", "rule_name"):
            finding[key] = redact(str(finding[key]))
    return result


def filter_findings(findings: List[Dict[str, str]], minimum_severity: Optional[str]) -> List[Dict[str, str]]:
    if minimum_severity is None:
        return findings
    from .rules import SEVERITY_RANK

    threshold = SEVERITY_RANK[minimum_severity.upper()]
    return [finding for finding in findings if SEVERITY_RANK[finding["severity"]] <= threshold]

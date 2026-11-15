"""Read and parse TOML files inside an explicitly selected scan directory."""

import os
import stat
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .constants import DEFAULT_MAX_FILE_BYTES


def _default_parser() -> Any:
    """Return tomllib on modern Python and tomli on Python 3.9/3.10."""
    try:
        import tomllib

        return tomllib
    except ImportError:  # Python 3.9 and 3.10
        import tomli

        return tomli


class ConfigInputError(ValueError):
    """Sanitized, structured error raised for unusable configuration input."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)

    def as_dict(self) -> Dict[str, str]:
        """Return a stable, safe representation suitable for CLI/report output."""
        return {"code": self.code, "message": self.message}


class ConfigParseError(ConfigInputError):
    """Raised when an in-scope TOML file cannot be read or parsed."""


class UnsafePathError(ConfigInputError):
    """Raised when a requested file is outside the selected scan root."""


def _close_quietly(file_descriptor: int) -> None:
    """Close a descriptor without allowing OS details into user-facing errors."""
    try:
        os.close(file_descriptor)
    except OSError:
        pass


def parse_toml_bytes(
    data: bytes,
    parser: Optional[Any] = None,
    max_bytes: int = DEFAULT_MAX_FILE_BYTES,
) -> Dict[str, Any]:
    """Parse bounded TOML bytes, sanitizing every parser exception."""
    if len(data) > max_bytes:
        raise ConfigInputError("file_too_large", "configuration file exceeds the size limit")
    active_parser = parser or _default_parser()
    try:
        return active_parser.load(BytesIO(data))
    except Exception as exc:
        if isinstance(exc, OSError):
            raise ConfigParseError("file_read_error", "configuration file could not be read") from None
        parse_error = getattr(active_parser, "TOMLDecodeError", ())
        if parse_error and isinstance(exc, parse_error):
            raise ConfigParseError("invalid_toml", "configuration file contains invalid TOML") from None
        raise ConfigParseError("parse_error", "configuration file could not be parsed safely") from None


def _open_canonical_file(root: Path, relative_path: Path) -> int:
    """Open a canonical in-root path by walking directory descriptors.

    O_NOFOLLOW blocks a resolved path component from being replaced by a
    symlink after validation. On platforms without dir_fd/O_NOFOLLOW support,
    this falls back to opening the canonical absolute path; that fallback has a
    wider race window and is not a complete race-prevention guarantee.
    """
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    cloexec = getattr(os, "O_CLOEXEC", 0)
    nonblock = getattr(os, "O_NONBLOCK", 0)

    if not nofollow or not directory_flag or os.open not in getattr(os, "supports_dir_fd", set()):
        return os.open(str(root / relative_path), os.O_RDONLY | cloexec | nonblock)

    directory_fd = os.open(str(root), os.O_RDONLY | directory_flag | nofollow | cloexec)
    try:
        parts = relative_path.parts
        for component in parts[:-1]:
            next_fd = os.open(
                component,
                os.O_RDONLY | directory_flag | nofollow | cloexec,
                dir_fd=directory_fd,
            )
            _close_quietly(directory_fd)
            directory_fd = next_fd
        return os.open(
            parts[-1], os.O_RDONLY | nofollow | cloexec | nonblock,
            dir_fd=directory_fd,
        )
    finally:
        _close_quietly(directory_fd)


def load_toml(
    scan_root: Union[str, Path],
    config_path: Union[str, Path],
    parser: Optional[Any] = None,
    max_bytes: int = DEFAULT_MAX_FILE_BYTES,
) -> Dict[str, Any]:
    """Load TOML without executing configuration-defined behavior.

    The resolved file must be inside the explicitly selected scan root. An
    internal symlink is accepted after resolution; its canonical target path is
    opened read-only. Errors expose stable codes and generic messages only.
    """
    try:
        root = Path(scan_root).resolve(strict=True)
        if not root.is_dir():
            raise ConfigInputError("invalid_scan_root", "scan root is not a directory")
    except ConfigInputError:
        raise
    except (OSError, RuntimeError, TypeError, ValueError):
        raise ConfigInputError("invalid_scan_root", "scan root is unavailable or invalid") from None

    try:
        requested = Path(config_path)
        candidate = requested if requested.is_absolute() else root / requested
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        code = "missing_config" if isinstance(exc, FileNotFoundError) else "invalid_config_path"
        message = "configuration file does not exist" if code == "missing_config" else "configuration path is unavailable or invalid"
        raise UnsafePathError(code, message) from None

    try:
        relative_path = resolved.relative_to(root)
    except ValueError:
        raise UnsafePathError("path_outside_scan_root", "configuration path is outside scan root") from None

    if not relative_path.parts:
        raise ConfigParseError("not_regular_file", "configuration input is not a regular file")

    try:
        file_fd = _open_canonical_file(root, relative_path)
    except (OSError, ValueError):
        raise ConfigParseError("file_read_error", "configuration file could not be opened") from None

    try:
        if not stat.S_ISREG(os.fstat(file_fd).st_mode):
            raise ConfigParseError("not_regular_file", "configuration input is not a regular file")
        if os.fstat(file_fd).st_size > max_bytes:
            raise ConfigInputError("file_too_large", "configuration file exceeds the size limit")
        chunks = []
        remaining = max_bytes + 1
        while remaining:
            chunk = os.read(file_fd, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        if len(data) > max_bytes:
            raise ConfigInputError("file_too_large", "configuration file exceeds the size limit")
        return parse_toml_bytes(data, parser=parser, max_bytes=max_bytes)
    except ConfigInputError:
        raise
    except OSError:
        raise ConfigParseError("file_read_error", "configuration file could not be read") from None
    finally:
        if file_fd >= 0:
            _close_quietly(file_fd)


def read_bytes(
    scan_root: Union[str, Path], config_path: Union[str, Path], max_bytes: int = DEFAULT_MAX_FILE_BYTES
) -> bytes:
    """Read a bounded regular file inside the scan root without following escapes."""
    try:
        root = Path(scan_root).resolve(strict=True)
        if not root.is_dir():
            raise ConfigInputError("invalid_scan_root", "scan root is not a directory")
    except ConfigInputError:
        raise
    except (OSError, RuntimeError, TypeError, ValueError):
        raise ConfigInputError("invalid_scan_root", "scan root is unavailable or invalid") from None
    try:
        requested = Path(config_path)
        candidate = requested if requested.is_absolute() else root / requested
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        code = "missing_config" if isinstance(exc, FileNotFoundError) else "invalid_config_path"
        message = "configuration file does not exist" if code == "missing_config" else "configuration path is unavailable or invalid"
        raise UnsafePathError(code, message) from None
    try:
        relative_path = resolved.relative_to(root)
    except ValueError:
        raise UnsafePathError("path_outside_scan_root", "input path is outside scan root") from None
    if not relative_path.parts:
        raise ConfigParseError("not_regular_file", "input is not a regular file")
    try:
        fd = _open_canonical_file(root, relative_path)
    except (OSError, ValueError):
        raise ConfigParseError("file_read_error", "input file could not be opened") from None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ConfigParseError("not_regular_file", "input is not a regular file")
        if info.st_size > max_bytes:
            raise ConfigInputError("file_too_large", "input file exceeds the size limit")
        chunks = []
        remaining = max_bytes + 1
        while remaining:
            chunk = os.read(fd, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        if len(data) > max_bytes:
            raise ConfigInputError("file_too_large", "input file exceeds the size limit")
        return data
    except ConfigInputError:
        raise
    except OSError:
        raise ConfigParseError("file_read_error", "input file could not be read") from None
    finally:
        _close_quietly(fd)


def read_text(
    scan_root: Union[str, Path], config_path: Union[str, Path], max_bytes: int = DEFAULT_MAX_FILE_BYTES
) -> str:
    """Read UTF-8 text safely; invalid byte sequences are replaced."""
    return read_bytes(scan_root, config_path, max_bytes).decode("utf-8", errors="replace")

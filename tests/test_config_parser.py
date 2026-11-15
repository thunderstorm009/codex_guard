import builtins
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace

import pytest

from codexguard import config_parser
from codexguard.config_parser import (
    ConfigInputError,
    ConfigParseError,
    UnsafePathError,
    load_toml,
)


def test_loads_valid_toml(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text('[sandbox]\nmode = "workspace-write"\n', encoding="utf-8")

    assert load_toml(tmp_path, "config.toml") == {"sandbox": {"mode": "workspace-write"}}


def test_rejects_malformed_toml_without_parser_details(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text('secret = "do-not-leak"\ninvalid', encoding="utf-8")

    with pytest.raises(ConfigParseError) as exc_info:
        load_toml(tmp_path, "config.toml")

    assert exc_info.value.as_dict() == {
        "code": "invalid_toml",
        "message": "configuration file contains invalid TOML",
    }
    assert exc_info.value.__cause__ is None
    assert "do-not-leak" not in "".join(
        traceback.format_exception(type(exc_info.value), exc_info.value, exc_info.value.__traceback__)
    )


def test_rejects_external_absolute_path(tmp_path: Path) -> None:
    root = tmp_path / "scan"
    root.mkdir()
    outside = tmp_path / "outside.toml"
    outside.write_text("enabled = true\n", encoding="utf-8")

    with pytest.raises(UnsafePathError) as exc_info:
        load_toml(root, outside)
    assert exc_info.value.code == "path_outside_scan_root"


def test_rejects_directory_traversal(tmp_path: Path) -> None:
    root = tmp_path / "scan"
    root.mkdir()
    outside = tmp_path / "outside.toml"
    outside.write_text("enabled = true\n", encoding="utf-8")

    with pytest.raises(UnsafePathError):
        load_toml(root, "../outside.toml")


def test_rejects_external_symlink(tmp_path: Path) -> None:
    root = tmp_path / "scan"
    root.mkdir()
    outside = tmp_path / "outside.toml"
    outside.write_text("enabled = true\n", encoding="utf-8")
    link = root / "external.toml"
    try:
        link.symlink_to(outside)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks unavailable")

    with pytest.raises(UnsafePathError):
        load_toml(root, link)


def test_loads_internal_symlink_target(tmp_path: Path) -> None:
    target = tmp_path / "real.toml"
    target.write_text("enabled = true\n", encoding="utf-8")
    link = tmp_path / "config.toml"
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks unavailable")

    assert load_toml(tmp_path, link) == {"enabled": True}


def test_missing_scan_root_is_structured_and_sanitized(tmp_path: Path) -> None:
    with pytest.raises(ConfigInputError) as exc_info:
        load_toml(tmp_path / "missing", "config.toml")

    assert exc_info.value.as_dict() == {
        "code": "invalid_scan_root",
        "message": "scan root is unavailable or invalid",
    }
    assert exc_info.value.__cause__ is None


def test_permission_denied_scan_root_is_structured_and_sanitized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "restricted"
    real_resolve = Path.resolve

    def deny_root_access(path: Path, strict: bool = False) -> Path:
        if path == root:
            raise PermissionError("private permission detail")
        return real_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", deny_root_access)
    with pytest.raises(ConfigInputError) as exc_info:
        load_toml(root, "config.toml")

    assert exc_info.value.as_dict() == {
        "code": "invalid_scan_root",
        "message": "scan root is unavailable or invalid",
    }
    assert exc_info.value.__cause__ is None
    assert "private permission detail" not in str(exc_info.value)


def test_file_as_scan_root_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "not-a-directory"
    root.write_text("", encoding="utf-8")

    with pytest.raises(ConfigInputError) as exc_info:
        load_toml(root, "config.toml")
    assert exc_info.value.code == "invalid_scan_root"


def test_missing_config_file_is_structured(tmp_path: Path) -> None:
    with pytest.raises(UnsafePathError) as exc_info:
        load_toml(tmp_path, "missing.toml")
    assert exc_info.value.as_dict() == {
        "code": "missing_config",
        "message": "configuration file does not exist",
    }


def test_directory_input_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ConfigParseError) as exc_info:
        load_toml(tmp_path, ".")
    assert exc_info.value.code == "not_regular_file"


def test_file_open_failure_is_sanitized(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "config.toml").write_text("valid = true\n", encoding="utf-8")

    def fail_open(root: Path, relative_path: Path) -> int:
        raise PermissionError("private filesystem detail")

    monkeypatch.setattr(config_parser, "_open_canonical_file", fail_open)
    with pytest.raises(ConfigParseError) as exc_info:
        load_toml(tmp_path, "config.toml")
    assert exc_info.value.as_dict() == {
        "code": "file_read_error",
        "message": "configuration file could not be opened",
    }
    assert "private filesystem detail" not in str(exc_info.value)
    assert exc_info.value.__cause__ is None


def test_file_read_failure_is_sanitized(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text("valid = true\n", encoding="utf-8")

    def fail_read(handle: object) -> None:
        raise OSError("private read detail")

    parser = SimpleNamespace(load=fail_read, TOMLDecodeError=ValueError)
    with pytest.raises(ConfigParseError) as exc_info:
        load_toml(tmp_path, "config.toml", parser=parser)
    assert exc_info.value.as_dict() == {
        "code": "file_read_error",
        "message": "configuration file could not be read",
    }
    assert exc_info.value.__cause__ is None
    assert "private read detail" not in str(exc_info.value)


def test_uses_injected_parser_and_sanitizes_its_decode_error(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text("not important", encoding="utf-8")

    class FakeDecodeError(Exception):
        pass

    def reject(handle: object) -> None:
        raise FakeDecodeError("sensitive parser detail")

    parser = SimpleNamespace(load=reject, TOMLDecodeError=FakeDecodeError)
    with pytest.raises(ConfigParseError) as exc_info:
        load_toml(tmp_path, "config.toml", parser=parser)
    assert exc_info.value.code == "invalid_toml"
    assert exc_info.value.__cause__ is None
    assert "sensitive parser detail" not in "".join(
        traceback.format_exception(type(exc_info.value), exc_info.value, exc_info.value.__traceback__)
    )


def test_parser_compatibility_prefers_tomllib_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    modern_parser = SimpleNamespace(load=lambda handle: {}, TOMLDecodeError=ValueError)
    monkeypatch.setitem(sys.modules, "tomllib", modern_parser)

    assert config_parser._default_parser() is modern_parser


def test_parser_compatibility_falls_back_to_tomli(monkeypatch: pytest.MonkeyPatch) -> None:
    import tomli

    real_import = builtins.__import__

    def import_without_tomllib(name: str, *args: object, **kwargs: object) -> object:
        if name == "tomllib":
            raise ImportError("simulated Python 3.9")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_tomllib)
    assert config_parser._default_parser() is tomli

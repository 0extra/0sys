from __future__ import annotations

from pathlib import Path

import pytest

from zerosys.core.config.parser import (
    build_config,
    dump_config,
    load_config,
    parse_config,
    write_config,
)
from zerosys.core.errors import (
    ConfigNotFoundError,
    ConfigParseError,
    ConfigValidationError,
)

pytestmark = pytest.mark.unit


def test_parse_minimal_config(minimal_yaml: str) -> None:
    config = parse_config(minimal_yaml)

    assert config.version == 1
    assert config.server is not None
    assert config.server.hostname == "test-server"
    assert config.firewall is not None
    assert config.firewall.allow == [22]


def test_parse_web_config(web_yaml: str) -> None:
    config = parse_config(web_yaml)

    assert config.server is not None
    assert config.server.hostname == "web-01"
    assert config.packages is not None
    assert "nginx" in config.packages.install
    assert "nginx" in config.services


def test_parse_empty_string_raises() -> None:
    with pytest.raises(ConfigParseError, match="empty"):
        parse_config("")


def test_parse_whitespace_only_raises() -> None:
    with pytest.raises(ConfigParseError, match="empty"):
        parse_config("   \n\t  ")


def test_parse_invalid_yaml_raises() -> None:
    with pytest.raises(ConfigParseError, match="invalid YAML"):
        parse_config("version: 1\nserver: [unclosed")


def test_parse_non_mapping_root_raises() -> None:
    with pytest.raises(ConfigParseError, match="must be a mapping"):
        parse_config("- just\n- a\n- list")


def test_parse_null_document_raises() -> None:
    with pytest.raises(ConfigParseError, match="empty"):
        parse_config("null")


def test_parse_invalid_version_raises() -> None:
    with pytest.raises(ConfigValidationError, match="version"):
        parse_config("version: 99\n")


def test_parse_unknown_field_raises() -> None:
    payload = "version: 1\nunknown_field: value\n"

    with pytest.raises(ConfigValidationError, match="unknown_field"):
        parse_config(payload)


def test_load_config_rejects_package_conflict(tmp_path: Path) -> None:
    payload = "version: 1\npackages:\n  install: [nginx]\n  remove: [nginx]\n"
    path = tmp_path / "conflict.yaml"
    path.write_text(payload, encoding="utf-8")

    with pytest.raises(ConfigValidationError, match="PKG001"):
        load_config(path)


def test_load_config_rejects_firewall_lockout(tmp_path: Path) -> None:
    payload = "version: 1\nfirewall:\n  default: deny\n  allow: [80]\n"
    path = tmp_path / "lockout.yaml"
    path.write_text(payload, encoding="utf-8")

    with pytest.raises(ConfigValidationError, match="FW001"):
        load_config(path)


def test_load_config_missing_file_raises(tmp_path: Path) -> None:
    missing = tmp_path / "nope.yaml"

    with pytest.raises(ConfigNotFoundError):
        load_config(missing)


def test_load_config_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigParseError, match="not a file"):
        load_config(tmp_path)


def test_load_config_reads_from_disk(
    tmp_config_path: Path,
    minimal_yaml: str,
) -> None:
    tmp_config_path.write_text(minimal_yaml, encoding="utf-8")

    config = load_config(tmp_config_path)

    assert config.server is not None
    assert config.server.hostname == "test-server"


def test_dump_then_parse_roundtrip(sample_config) -> None:
    text = dump_config(sample_config)
    reloaded = parse_config(text)

    assert reloaded.version == sample_config.version
    assert reloaded.server is not None
    assert sample_config.server is not None
    assert reloaded.server.hostname == sample_config.server.hostname


def test_dump_omits_unset_fields(sample_config) -> None:
    text = dump_config(sample_config)

    assert "files:" not in text
    assert "commands:" not in text
    assert "services:" not in text
    assert "users:" not in text


def test_write_config_creates_parent_dirs(tmp_path: Path, sample_config) -> None:
    target = tmp_path / "nested" / "deep" / "0sys.yaml"

    path = write_config(sample_config, target)

    assert path == target.resolve()
    assert path.exists()


def test_build_config_from_dict() -> None:
    data = {
        "version": 1,
        "server": {"hostname": "custom"},
        "firewall": {"default": "deny", "allow": [22]},
    }

    config = build_config(data)

    assert config.server is not None
    assert config.server.hostname == "custom"

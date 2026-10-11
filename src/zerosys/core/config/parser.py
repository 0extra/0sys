from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from zerosys.core.config.schema import Config
from zerosys.core.errors import (
    ConfigNotFoundError,
    ConfigParseError,
    ConfigValidationError,
)


def load_config(path: Path | str) -> Config:
    config_path = Path(path).expanduser().resolve()
    if not config_path.exists():
        raise ConfigNotFoundError(f"config file not found: {config_path}")
    if not config_path.is_file():
        raise ConfigParseError(f"config path is not a file: {config_path}")

    try:
        raw_text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigParseError(f"cannot read config file: {exc}") from exc

    return parse_config(raw_text)


def parse_config(raw_text: str) -> Config:
    if not raw_text.strip():
        raise ConfigParseError("config is empty")

    try:
        data = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise ConfigParseError(f"invalid YAML: {exc}") from exc

    if data is None:
        raise ConfigParseError("config is empty after YAML parsing")

    if not isinstance(data, dict):
        raise ConfigParseError(f"config root must be a mapping, got {type(data).__name__}")

    return build_config(data)


def build_config(data: dict[str, Any]) -> Config:
    try:
        return Config.model_validate(data)
    except ValidationError as exc:
        raise ConfigValidationError(_format_validation_error(exc)) from exc


def _format_validation_error(exc: ValidationError) -> str:
    lines = ["config validation failed:"]
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"]) or "<root>"
        message = error["msg"]
        lines.append(f"  - {location}: {message}")
    return "\n".join(lines)


def dump_config(config: Config) -> str:
    data = config.model_dump(exclude_none=True, exclude_defaults=False)
    result = yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    if not isinstance(result, str):
        raise ConfigParseError("yaml.safe_dump returned a non-string result")
    return result


def write_config(config: Config, path: Path | str) -> Path:
    config_path = Path(path).expanduser().resolve()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(dump_config(config), encoding="utf-8")
    return config_path

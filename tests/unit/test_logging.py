from __future__ import annotations

import logging
from pathlib import Path

import pytest

from zerosys.core.logging import (
    AuditLog,
    configure_logging,
    current_level,
    disable_logging,
    get_logger,
    list_audit_logs,
    log_file_path,
    set_level,
)

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _reset_logging() -> None:
    yield
    disable_logging()


def test_get_logger_root() -> None:
    logger = get_logger()

    assert logger.name == "zerosys"


def test_get_logger_child() -> None:
    logger = get_logger("planner")

    assert logger.name == "zerosys.planner"


def test_configure_logging_writes_to_file(tmp_path: Path) -> None:
    log_file = tmp_path / "0sys.log"
    configure_logging(log_file=log_file)

    logger = get_logger("test")
    logger.info("hello world")

    for handler in logging.getLogger("zerosys").handlers:
        handler.flush()

    assert log_file.exists()
    assert "hello world" in log_file.read_text(encoding="utf-8")


def test_configure_logging_creates_parent_dirs(tmp_path: Path) -> None:
    log_file = tmp_path / "deep" / "nested" / "0sys.log"
    configure_logging(log_file=log_file)

    get_logger("test").info("x")

    for handler in logging.getLogger("zerosys").handlers:
        handler.flush()

    assert log_file.exists()


def test_disable_logging_uses_null_handler() -> None:
    disable_logging()

    handlers = logging.getLogger("zerosys").handlers
    assert len(handlers) == 1
    assert isinstance(handlers[0], logging.NullHandler)


def test_set_level_updates_root(tmp_path: Path) -> None:
    configure_logging(level=logging.INFO, log_file=tmp_path / "x.log")
    set_level(logging.DEBUG)

    assert current_level() == logging.DEBUG


def test_log_file_path_returns_path() -> None:
    assert isinstance(log_file_path(), Path)


def test_audit_log_records_event(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    log = AuditLog(path=path, run_id="run-1")

    event = log.record(action="apply", target="localhost", status="ok")

    assert event.action == "apply"
    assert event.run_id == "run-1"
    assert path.exists()


def test_audit_log_reads_events(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    log = AuditLog(path=path, run_id="run-2")
    log.record(action="a")
    log.record(action="b")
    log.record(action="c")

    events = log.read()

    assert [e.action for e in events] == ["a", "b", "c"]


def test_audit_log_read_limit(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    log = AuditLog(path=path, run_id="run-3")
    for i in range(5):
        log.record(action=f"action-{i}")

    events = log.read(limit=2)

    assert [e.action for e in events] == ["action-3", "action-4"]


def test_audit_log_count(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    log = AuditLog(path=path, run_id="run-4")
    log.record(action="x")
    log.record(action="y")

    assert log.count() == 2


def test_audit_log_empty_when_file_missing(tmp_path: Path) -> None:
    log = AuditLog(path=tmp_path / "missing.jsonl", run_id="run-5")

    assert log.read() == []


def test_audit_log_details_serialized(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    log = AuditLog(path=path, run_id="run-6")
    log.record(action="apply", details={"packages": 3, "host": "web-01"})

    events = log.read()

    assert events[0].details["packages"] == 3
    assert events[0].details["host"] == "web-01"


def test_list_audit_logs_returns_list() -> None:
    result = list_audit_logs()

    assert isinstance(result, list)

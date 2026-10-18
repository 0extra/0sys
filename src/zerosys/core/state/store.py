from __future__ import annotations

import contextlib
import sqlite3
from collections.abc import Iterable
from pathlib import Path

from zerosys.core.errors import StateError
from zerosys.core.state.models import RunRecord, TaskRecord

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"

RUN_COLUMNS = (
    "id, config_path, config_hash, target_host, target_user, target_port, "
    "ssh_key_path, started_at, finished_at, status, total_tasks, successful_tasks, "
    "failed_tasks, skipped_tasks, dry_run"
)

TASK_COLUMNS = (
    "id, run_id, task_id, kind, name, target, backend, status, message, "
    "stdout, stderr, changed, duration_ms, started_at, finished_at, params"
)

_RUN_PLACEHOLDERS = ", ".join(["?"] * 15)
_RUN_INSERT_SQL = f"INSERT INTO runs ({RUN_COLUMNS}) VALUES ({_RUN_PLACEHOLDERS})"

_TASK_PLACEHOLDERS = ", ".join(["?"] * 16)
_TASK_INSERT_SQL = (
    f"INSERT INTO tasks ({TASK_COLUMNS}) VALUES ({_TASK_PLACEHOLDERS}) "
    "ON CONFLICT(run_id, task_id) DO UPDATE SET "
    "status=excluded.status, message=excluded.message, "
    "stdout=excluded.stdout, stderr=excluded.stderr, "
    "changed=excluded.changed, duration_ms=excluded.duration_ms, "
    "started_at=excluded.started_at, finished_at=excluded.finished_at"
)


class StateStore:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.path), isolation_level=None)
            self._conn.row_factory = sqlite3.Row
            with contextlib.suppress(OSError):
                self.path.chmod(0o600)
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._migrate()
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _migrate(self) -> None:
        assert self._conn is not None
        current = self._current_version()
        pending = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for migration in pending:
            version = self._version_from_filename(migration.name)
            if version is None or version <= current:
                continue
            sql = migration.read_text(encoding="utf-8")

            statements: list[str] = []
            buffer = ""
            for line in sql.splitlines():
                buffer += line + "\n"
                if sqlite3.complete_statement(buffer):
                    statements.append(buffer)
                    buffer = ""
            if buffer.strip():
                statements.append(buffer)

            try:
                self._conn.execute("BEGIN")
                for stmt in statements:
                    self._conn.execute(stmt)
                self._conn.execute("COMMIT")
            except sqlite3.Error as exc:
                with contextlib.suppress(sqlite3.Error):
                    self._conn.execute("ROLLBACK")
                raise StateError(f"migration {migration.name} failed: {exc}") from exc

    def _current_version(self) -> int:
        assert self._conn is not None
        try:
            cursor = self._conn.execute("SELECT MAX(version) FROM schema_version")
        except sqlite3.OperationalError:
            return 0
        row = cursor.fetchone()
        if row is None or row[0] is None:
            return 0
        return int(row[0])

    def _version_from_filename(self, name: str) -> int | None:
        stem = name.split("_", 1)[0]
        try:
            return int(stem)
        except ValueError:
            return None

    def save_run(self, run: RunRecord) -> None:
        conn = self.connect()
        try:
            conn.execute(_RUN_INSERT_SQL, run.to_row())
        except sqlite3.Error as exc:
            raise StateError(f"failed to save run: {exc}") from exc

    def update_run(self, run: RunRecord) -> None:
        conn = self.connect()
        try:
            conn.execute(
                "UPDATE runs SET finished_at = ?, status = ?, total_tasks = ?, "
                "successful_tasks = ?, failed_tasks = ?, skipped_tasks = ? "
                "WHERE id = ?",
                (
                    run.finished_at,
                    run.status.value,
                    run.total_tasks,
                    run.successful_tasks,
                    run.failed_tasks,
                    run.skipped_tasks,
                    run.id,
                ),
            )
        except sqlite3.Error as exc:
            raise StateError(f"failed to update run: {exc}") from exc

    def save_task(self, task: TaskRecord) -> None:
        conn = self.connect()
        try:
            conn.execute(_TASK_INSERT_SQL, task.to_row())
        except sqlite3.Error as exc:
            raise StateError(f"failed to save task: {exc}") from exc

    def save_tasks(self, tasks: Iterable[TaskRecord]) -> None:
        conn = self.connect()
        try:
            conn.executemany(_TASK_INSERT_SQL, [t.to_row() for t in tasks])
        except sqlite3.Error as exc:
            raise StateError(f"failed to save tasks: {exc}") from exc

    def get_run(self, run_id: str) -> RunRecord | None:
        conn = self.connect()
        cursor = conn.execute(f"SELECT {RUN_COLUMNS} FROM runs WHERE id = ?", (run_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return RunRecord.from_row(tuple(row))

    def latest_run(self) -> RunRecord | None:
        conn = self.connect()
        cursor = conn.execute(f"SELECT {RUN_COLUMNS} FROM runs ORDER BY started_at DESC LIMIT 1")
        row = cursor.fetchone()
        if row is None:
            return None
        return RunRecord.from_row(tuple(row))

    def list_runs(self, limit: int = 20) -> list[RunRecord]:
        conn = self.connect()
        cursor = conn.execute(
            f"SELECT {RUN_COLUMNS} FROM runs ORDER BY started_at DESC LIMIT ?",
            (limit,),
        )
        return [RunRecord.from_row(tuple(row)) for row in cursor.fetchall()]

    def get_tasks(self, run_id: str) -> list[TaskRecord]:
        conn = self.connect()
        cursor = conn.execute(
            f"SELECT {TASK_COLUMNS} FROM tasks WHERE run_id = ? ORDER BY started_at ASC",
            (run_id,),
        )
        return [TaskRecord.from_row(tuple(row)) for row in cursor.fetchall()]

    def count_runs(self) -> int:
        conn = self.connect()
        cursor = conn.execute("SELECT COUNT(*) FROM runs")
        row = cursor.fetchone()
        return int(row[0]) if row else 0

    def clean_old_runs(self, keep_last: int = 50) -> int:
        conn = self.connect()
        try:
            cursor = conn.execute(
                "DELETE FROM runs WHERE id NOT IN ("
                "  SELECT id FROM runs ORDER BY started_at DESC LIMIT ?"
                ")",
                (keep_last,),
            )
            return cursor.rowcount
        except sqlite3.Error as exc:
            raise StateError(f"failed to clean old runs: {exc}") from exc

    def __enter__(self) -> StateStore:
        self.connect()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

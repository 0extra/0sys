ALTER TABLE runs ADD COLUMN target_port INTEGER DEFAULT 22;
ALTER TABLE runs ADD COLUMN ssh_key_path TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_run_task ON tasks(run_id, task_id);

INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (2, datetime('now'));
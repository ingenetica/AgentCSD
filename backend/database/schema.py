SCHEMA_SQL = """\
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  persona_core_path TEXT NOT NULL,
  model_config TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  summary_frequency INTEGER NOT NULL DEFAULT 10,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL REFERENCES sessions(id),
  layer TEXT NOT NULL,
  tag TEXT NOT NULL,
  content TEXT NOT NULL,
  cycle_number INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS mood_and_criteria (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL REFERENCES sessions(id),
  mood TEXT NOT NULL,
  criteria TEXT NOT NULL,
  cycle_number INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS context_summaries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL REFERENCES sessions(id),
  layer TEXT NOT NULL,
  summary TEXT NOT NULL,
  cycle_from INTEGER NOT NULL,
  cycle_to INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, layer, created_at);
CREATE INDEX IF NOT EXISTS idx_mc_session ON mood_and_criteria(session_id, created_at);
"""

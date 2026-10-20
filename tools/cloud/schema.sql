CREATE TABLE IF NOT EXISTS docs (
  kind TEXT NOT NULL,          -- queue | queue_meta | crosspost | job | upload | broll | talking_point | stat | health | token
  id   TEXT NOT NULL,
  data TEXT NOT NULL,          -- JSON object
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  PRIMARY KEY (kind, id)
);
CREATE INDEX IF NOT EXISTS docs_kind_updated ON docs(kind, updated_at);

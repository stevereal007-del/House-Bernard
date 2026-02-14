-- House Bernard Platform — Initial Schema
-- SQLite, WAL mode, strict types

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- Citizens
CREATE TABLE IF NOT EXISTS citizens (
    id          TEXT PRIMARY KEY,          -- e.g. "HB-CIT-0001"
    alias       TEXT NOT NULL,
    wallet_address TEXT,
    tier        TEXT NOT NULL DEFAULT 'visitor',  -- visitor/spark/flame/furnace/invariant
    joined_at   TEXT NOT NULL,
    total_earned REAL NOT NULL DEFAULT 0
);

-- Forum topics
CREATE TABLE IF NOT EXISTS forum_topics (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,             -- e.g. "General", "Guild: Entropy Hunters"
    guild_id    TEXT,                      -- NULL = public, guild_id = guild-only
    created_at  TEXT NOT NULL
);

-- Forum threads
CREATE TABLE IF NOT EXISTS forum_threads (
    id          INTEGER PRIMARY KEY,
    topic_id    INTEGER NOT NULL REFERENCES forum_topics(id),
    title       TEXT NOT NULL,
    author_id   TEXT NOT NULL REFERENCES citizens(id),
    created_at  TEXT NOT NULL,
    pinned      INTEGER NOT NULL DEFAULT 0,
    locked      INTEGER NOT NULL DEFAULT 0
);

-- Forum posts
CREATE TABLE IF NOT EXISTS forum_posts (
    id          INTEGER PRIMARY KEY,
    thread_id   INTEGER NOT NULL REFERENCES forum_threads(id),
    author_id   TEXT NOT NULL REFERENCES citizens(id),
    body        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    edited_at   TEXT,
    is_agent    INTEGER NOT NULL DEFAULT 0
);

-- Briefs
CREATE TABLE IF NOT EXISTS briefs (
    id          TEXT PRIMARY KEY,          -- e.g. "HB-BRIEF-0001"
    title       TEXT NOT NULL,
    description TEXT NOT NULL,
    lab         TEXT,                      -- lab_a, lab_b, etc.
    status      TEXT NOT NULL DEFAULT 'open',  -- open/claimed/closed
    claimed_by  TEXT REFERENCES citizens(id),
    reward_tier INTEGER,
    created_at  TEXT NOT NULL,
    deadline    TEXT
);

-- Submissions
CREATE TABLE IF NOT EXISTS submissions (
    id          INTEGER PRIMARY KEY,
    brief_id    TEXT REFERENCES briefs(id),
    citizen_id  TEXT NOT NULL REFERENCES citizens(id),
    artifact_hash TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'queued',  -- queued/testing/survived/culled
    submitted_at TEXT NOT NULL,
    verdict_at  TEXT,
    tier_reached TEXT                       -- T0/T1/T2/T3/T4
);

-- Agent message bus
CREATE TABLE IF NOT EXISTS agent_messages (
    id          INTEGER PRIMARY KEY,
    from_agent  TEXT NOT NULL,             -- achillesrun/warden/treasurer/magistrate
    to_agent    TEXT NOT NULL,
    message_type TEXT NOT NULL,            -- task/response/alert/heartbeat
    payload     TEXT NOT NULL,             -- JSON
    priority    TEXT NOT NULL DEFAULT 'normal',  -- low/normal/high/emergency
    status      TEXT NOT NULL DEFAULT 'pending', -- pending/processing/completed/failed
    created_at  TEXT NOT NULL,
    processed_at TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_threads_topic ON forum_threads(topic_id);
CREATE INDEX IF NOT EXISTS idx_posts_thread ON forum_posts(thread_id);
CREATE INDEX IF NOT EXISTS idx_submissions_citizen ON submissions(citizen_id);
CREATE INDEX IF NOT EXISTS idx_submissions_brief ON submissions(brief_id);
CREATE INDEX IF NOT EXISTS idx_messages_to ON agent_messages(to_agent, status);
CREATE INDEX IF NOT EXISTS idx_messages_created ON agent_messages(created_at);

-- Seed default forum topics
INSERT OR IGNORE INTO forum_topics (id, name, guild_id, created_at)
VALUES
    (1, 'General',        NULL, datetime('now')),
    (2, 'Announcements',  NULL, datetime('now')),
    (3, 'Research',       NULL, datetime('now')),
    (4, 'Bug Reports',    NULL, datetime('now'));

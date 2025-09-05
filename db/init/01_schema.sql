CREATE SCHEMA IF NOT EXISTS security_system;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

SET search_path = security_system, public;

CREATE TABLE IF NOT EXISTS users (
    id             SERIAL PRIMARY KEY,
    username       TEXT        NOT NULL UNIQUE,
    password_hash  TEXT        NOT NULL,
    role           TEXT        NOT NULL CHECK (role IN ('user', 'admin')),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

CREATE TABLE IF NOT EXISTS agents (
    id           SERIAL PRIMARY KEY,
    agent_uuid   TEXT        NOT NULL UNIQUE,
    hostname     TEXT,
    ip_address   TEXT,
    os           TEXT,
    version      TEXT,
    owner_id     INT         REFERENCES users(id) ON DELETE SET NULL,
    status       TEXT        NOT NULL DEFAULT 'offline' CHECK (status IN ('offline', 'online', 'unknown')),
    last_seen    TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agents_owner_id ON agents(owner_id);
CREATE INDEX IF NOT EXISTS idx_agents_status    ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_last_seen ON agents(last_seen);

CREATE TABLE IF NOT EXISTS events (
    id          SERIAL PRIMARY KEY,
    agent_id    INT         REFERENCES agents(id) ON DELETE SET NULL,
    host_id     TEXT,
    ts          TIMESTAMPTZ NOT NULL,
    event_type  TEXT        NOT NULL,
    severity    TEXT,
    src_ip      TEXT,
    dst_ip      TEXT,
    src_port    INT,
    dst_port    INT,
    protocol    TEXT,
    packet_size INT,
    flags       TEXT,
    details     JSONB       DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_events_agent_id ON events(agent_id);
CREATE INDEX IF NOT EXISTS idx_events_ts       ON events(ts DESC);
CREATE INDEX IF NOT EXISTS idx_events_severity ON events(severity);
CREATE INDEX IF NOT EXISTS idx_events_type     ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_host_id  ON events(host_id);
CREATE INDEX IF NOT EXISTS idx_events_details_gin ON events USING GIN (details);
CREATE INDEX IF NOT EXISTS idx_events_type_severity ON events(event_type, severity);
CREATE INDEX IF NOT EXISTS idx_events_ts_type ON events(ts DESC, event_type);

CREATE TABLE IF NOT EXISTS alert_types (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS alerts (
    id             SERIAL PRIMARY KEY,
    event_id       INT         REFERENCES events(id)  ON DELETE SET NULL,
    agent_id       INT         REFERENCES agents(id) ON DELETE SET NULL,
    alert_type_id  INT         REFERENCES alert_types(id) ON DELETE SET NULL,
    ts             TIMESTAMPTZ NOT NULL,
    title          TEXT,
    severity       TEXT,
    source         TEXT,
    description    TEXT,
    acknowledged   BOOLEAN     NOT NULL DEFAULT FALSE,
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by TEXT,
    metadata       JSONB       DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_alerts_event_id       ON alerts(event_id);
CREATE INDEX IF NOT EXISTS idx_alerts_agent_id       ON alerts(agent_id);
CREATE INDEX IF NOT EXISTS idx_alerts_alert_type_id  ON alerts(alert_type_id);
CREATE INDEX IF NOT EXISTS idx_alerts_ts             ON alerts(ts DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_ack            ON alerts(acknowledged);
CREATE INDEX IF NOT EXISTS idx_alerts_metadata_gin   ON alerts USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_alerts_severity_ack   ON alerts(severity, acknowledged);
CREATE INDEX IF NOT EXISTS idx_alerts_ts_severity    ON alerts(ts DESC, severity);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged_at ON alerts(acknowledged_at);

CREATE TABLE IF NOT EXISTS actions (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS alert_type_actions (
    id            SERIAL PRIMARY KEY,
    alert_type_id INT NOT NULL REFERENCES alert_types(id) ON DELETE CASCADE,
    action_id     INT NOT NULL REFERENCES actions(id)      ON DELETE CASCADE,
    UNIQUE (alert_type_id, action_id)
);

CREATE INDEX IF NOT EXISTS idx_alert_type_actions_type ON alert_type_actions(alert_type_id);
CREATE INDEX IF NOT EXISTS idx_alert_type_actions_act  ON alert_type_actions(action_id);

CREATE TABLE IF NOT EXISTS alert_action_history (
    id          SERIAL PRIMARY KEY,
    alert_id    INT REFERENCES alerts(id)  ON DELETE CASCADE,
    action_id   INT REFERENCES actions(id) ON DELETE SET NULL,
    status      TEXT        NOT NULL CHECK (status IN ('pending', 'done', 'failed')),
    executed_at TIMESTAMPTZ,
    message     TEXT
);

CREATE INDEX IF NOT EXISTS idx_alert_action_history_alert  ON alert_action_history(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_action_history_status ON alert_action_history(status);
CREATE INDEX IF NOT EXISTS idx_alert_action_history_time   ON alert_action_history(executed_at DESC);

CREATE TABLE IF NOT EXISTS notifications (
    id       SERIAL PRIMARY KEY,
    user_id  INT  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    method   TEXT NOT NULL CHECK (method IN ('email', 'push', 'telegram')),
    target   TEXT NOT NULL,
    enabled  BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_notifications_user   ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_method ON notifications(method);
CREATE INDEX IF NOT EXISTS idx_notifications_enabled ON notifications(enabled);

-- Хранилище API-ключей пользователей (храним в открытом виде для простоты)
CREATE TABLE IF NOT EXISTS api_keys (
    id          SERIAL PRIMARY KEY,
    user_id     INT  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT,
    token       TEXT NOT NULL UNIQUE,  -- API ключ в открытом виде
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_api_keys_user      ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_token     ON api_keys(token);
CREATE INDEX IF NOT EXISTS idx_api_keys_revoked   ON api_keys(revoked_at);

-- Ограничение: один пользователь может иметь только один активный API ключ
CREATE UNIQUE INDEX IF NOT EXISTS idx_api_keys_user_active 
    ON api_keys(user_id) WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS notification_history (
    id       SERIAL PRIMARY KEY,
    alert_id INT REFERENCES alerts(id) ON DELETE SET NULL,
    user_id  INT REFERENCES users(id)  ON DELETE SET NULL,
    method   TEXT NOT NULL CHECK (method IN ('email', 'push', 'telegram')),
    status   TEXT NOT NULL CHECK (status IN ('sent', 'failed')),
    ts       TIMESTAMPTZ NOT NULL,
    message  TEXT
);

CREATE INDEX IF NOT EXISTS idx_notification_history_user   ON notification_history(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_history_alert  ON notification_history(alert_id);
CREATE INDEX IF NOT EXISTS idx_notification_history_ts     ON notification_history(ts DESC);
CREATE INDEX IF NOT EXISTS idx_notification_history_status ON notification_history(status);

-- Функция для обновления updated_at
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $f$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$f$ LANGUAGE plpgsql;

-- Триггеры для обновления updated_at
DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_agents_updated_at ON agents;
CREATE TRIGGER trg_agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
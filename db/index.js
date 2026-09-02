const path = require("path");
const Database = require("better-sqlite3");
const bcrypt = require("bcryptjs");

const dbPath = path.join(__dirname, "..", "data", "tms.db");
const db = new Database(dbPath);
db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");

db.exec(`
CREATE TABLE IF NOT EXISTS admin (
  admin_id  INTEGER PRIMARY KEY AUTOINCREMENT,
  name      TEXT NOT NULL,
  email     TEXT NOT NULL UNIQUE,
  password  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tournament (
  tournament_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name          TEXT NOT NULL,
  sport         TEXT NOT NULL,
  start_date    TEXT,
  end_date      TEXT,
  status        TEXT NOT NULL DEFAULT 'upcoming'  -- upcoming | ongoing | completed
);

CREATE TABLE IF NOT EXISTS team (
  team_id       INTEGER PRIMARY KEY AUTOINCREMENT,
  tournament_id INTEGER NOT NULL REFERENCES tournament(tournament_id) ON DELETE CASCADE,
  team_name     TEXT NOT NULL,
  captain       TEXT
);

CREATE TABLE IF NOT EXISTS player (
  player_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  team_id     INTEGER NOT NULL REFERENCES team(team_id) ON DELETE CASCADE,
  player_name TEXT NOT NULL,
  age         INTEGER
);

CREATE TABLE IF NOT EXISTS match (
  match_id      INTEGER PRIMARY KEY AUTOINCREMENT,
  tournament_id INTEGER NOT NULL REFERENCES tournament(tournament_id) ON DELETE CASCADE,
  team1_id      INTEGER NOT NULL REFERENCES team(team_id) ON DELETE CASCADE,
  team2_id      INTEGER NOT NULL REFERENCES team(team_id) ON DELETE CASCADE,
  match_date    TEXT,
  venue         TEXT,
  round         TEXT NOT NULL DEFAULT 'league', -- league | semi | final
  status        TEXT NOT NULL DEFAULT 'scheduled' -- scheduled | completed
);

CREATE TABLE IF NOT EXISTS result (
  result_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  match_id    INTEGER NOT NULL UNIQUE REFERENCES match(match_id) ON DELETE CASCADE,
  team1_score TEXT,
  team2_score TEXT,
  winner_id   INTEGER REFERENCES team(team_id) -- NULL allowed for a draw
);

CREATE TABLE IF NOT EXISTS points (
  team_id       INTEGER NOT NULL REFERENCES team(team_id) ON DELETE CASCADE,
  tournament_id INTEGER NOT NULL REFERENCES tournament(tournament_id) ON DELETE CASCADE,
  played        INTEGER NOT NULL DEFAULT 0,
  won           INTEGER NOT NULL DEFAULT 0,
  lost          INTEGER NOT NULL DEFAULT 0,
  draw          INTEGER NOT NULL DEFAULT 0,
  points        INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (team_id, tournament_id)
);
`);

// Seed a default admin account if none exists yet
const adminCount = db.prepare("SELECT COUNT(*) AS c FROM admin").get().c;
if (adminCount === 0) {
  const hash = bcrypt.hashSync("admin123", 10);
  db.prepare(
    "INSERT INTO admin (name, email, password) VALUES (?, ?, ?)"
  ).run("Tournament Admin", "admin@tms.local", hash);
  console.log("Seeded default admin -> email: admin@tms.local  password: admin123");
}

module.exports = db;

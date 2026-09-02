const express = require("express");
const db = require("../db");
const { requireAdmin } = require("./middleware");

const router = express.Router();

// Public: list teams (optionally filtered by tournament_id)
router.get("/", (req, res) => {
  const { tournament_id } = req.query;
  const rows = tournament_id
    ? db.prepare("SELECT * FROM team WHERE tournament_id = ? ORDER BY team_name").all(tournament_id)
    : db.prepare("SELECT * FROM team ORDER BY team_name").all();
  res.json(rows);
});

router.get("/:id", (req, res) => {
  const row = db.prepare("SELECT * FROM team WHERE team_id = ?").get(req.params.id);
  if (!row) return res.status(404).json({ error: "Team not found." });
  res.json(row);
});

// Admin: add a team, and seed its points row
router.post("/", requireAdmin, (req, res) => {
  const { tournament_id, team_name, captain } = req.body || {};
  if (!tournament_id || !team_name) {
    return res.status(400).json({ error: "tournament_id and team_name are required." });
  }
  const tourn = db.prepare("SELECT * FROM tournament WHERE tournament_id = ?").get(tournament_id);
  if (!tourn) return res.status(404).json({ error: "Tournament not found." });

  const info = db
    .prepare("INSERT INTO team (tournament_id, team_name, captain) VALUES (?, ?, ?)")
    .run(tournament_id, team_name, captain || null);

  db.prepare(
    "INSERT INTO points (team_id, tournament_id, played, won, lost, draw, points) VALUES (?, ?, 0,0,0,0,0)"
  ).run(info.lastInsertRowid, tournament_id);

  res.status(201).json(db.prepare("SELECT * FROM team WHERE team_id = ?").get(info.lastInsertRowid));
});

router.put("/:id", requireAdmin, (req, res) => {
  const existing = db.prepare("SELECT * FROM team WHERE team_id = ?").get(req.params.id);
  if (!existing) return res.status(404).json({ error: "Team not found." });
  const { team_name, captain } = req.body || {};
  db.prepare("UPDATE team SET team_name = ?, captain = ? WHERE team_id = ?").run(
    team_name ?? existing.team_name,
    captain ?? existing.captain,
    req.params.id
  );
  res.json(db.prepare("SELECT * FROM team WHERE team_id = ?").get(req.params.id));
});

router.delete("/:id", requireAdmin, (req, res) => {
  const info = db.prepare("DELETE FROM team WHERE team_id = ?").run(req.params.id);
  if (info.changes === 0) return res.status(404).json({ error: "Team not found." });
  res.json({ ok: true });
});

module.exports = router;

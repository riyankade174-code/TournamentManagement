const express = require("express");
const db = require("../db");
const { requireAdmin } = require("./middleware");

const router = express.Router();

router.get("/", (req, res) => {
  const { team_id } = req.query;
  const rows = team_id
    ? db.prepare("SELECT * FROM player WHERE team_id = ? ORDER BY player_name").all(team_id)
    : db.prepare("SELECT * FROM player ORDER BY player_name").all();
  res.json(rows);
});

router.post("/", requireAdmin, (req, res) => {
  const { team_id, player_name, age } = req.body || {};
  if (!team_id || !player_name) {
    return res.status(400).json({ error: "team_id and player_name are required." });
  }
  const team = db.prepare("SELECT * FROM team WHERE team_id = ?").get(team_id);
  if (!team) return res.status(404).json({ error: "Team not found." });

  const info = db
    .prepare("INSERT INTO player (team_id, player_name, age) VALUES (?, ?, ?)")
    .run(team_id, player_name, age || null);
  res.status(201).json(db.prepare("SELECT * FROM player WHERE player_id = ?").get(info.lastInsertRowid));
});

router.put("/:id", requireAdmin, (req, res) => {
  const existing = db.prepare("SELECT * FROM player WHERE player_id = ?").get(req.params.id);
  if (!existing) return res.status(404).json({ error: "Player not found." });
  const { player_name, age } = req.body || {};
  db.prepare("UPDATE player SET player_name = ?, age = ? WHERE player_id = ?").run(
    player_name ?? existing.player_name,
    age ?? existing.age,
    req.params.id
  );
  res.json(db.prepare("SELECT * FROM player WHERE player_id = ?").get(req.params.id));
});

router.delete("/:id", requireAdmin, (req, res) => {
  const info = db.prepare("DELETE FROM player WHERE player_id = ?").run(req.params.id);
  if (info.changes === 0) return res.status(404).json({ error: "Player not found." });
  res.json({ ok: true });
});

module.exports = router;

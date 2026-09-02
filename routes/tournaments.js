const express = require("express");
const db = require("../db");
const { requireAdmin } = require("./middleware");

const router = express.Router();

// Public: list all tournaments
router.get("/", (req, res) => {
  const rows = db.prepare("SELECT * FROM tournament ORDER BY tournament_id DESC").all();
  res.json(rows);
});

// Public: single tournament detail
router.get("/:id", (req, res) => {
  const row = db.prepare("SELECT * FROM tournament WHERE tournament_id = ?").get(req.params.id);
  if (!row) return res.status(404).json({ error: "Tournament not found." });
  res.json(row);
});

// Admin: create tournament
router.post("/", requireAdmin, (req, res) => {
  const { name, sport, start_date, end_date } = req.body || {};
  if (!name || !sport) return res.status(400).json({ error: "Name and sport are required." });
  const info = db
    .prepare(
      "INSERT INTO tournament (name, sport, start_date, end_date, status) VALUES (?, ?, ?, ?, 'upcoming')"
    )
    .run(name, sport, start_date || null, end_date || null);
  const row = db.prepare("SELECT * FROM tournament WHERE tournament_id = ?").get(info.lastInsertRowid);
  res.status(201).json(row);
});

// Admin: edit tournament
router.put("/:id", requireAdmin, (req, res) => {
  const existing = db.prepare("SELECT * FROM tournament WHERE tournament_id = ?").get(req.params.id);
  if (!existing) return res.status(404).json({ error: "Tournament not found." });
  const { name, sport, start_date, end_date, status } = req.body || {};
  db.prepare(
    `UPDATE tournament SET name = ?, sport = ?, start_date = ?, end_date = ?, status = ?
     WHERE tournament_id = ?`
  ).run(
    name ?? existing.name,
    sport ?? existing.sport,
    start_date ?? existing.start_date,
    end_date ?? existing.end_date,
    status ?? existing.status,
    req.params.id
  );
  res.json(db.prepare("SELECT * FROM tournament WHERE tournament_id = ?").get(req.params.id));
});

// Admin: delete tournament (cascades to teams/players/matches/results/points)
router.delete("/:id", requireAdmin, (req, res) => {
  const info = db.prepare("DELETE FROM tournament WHERE tournament_id = ?").run(req.params.id);
  if (info.changes === 0) return res.status(404).json({ error: "Tournament not found." });
  res.json({ ok: true });
});

module.exports = router;

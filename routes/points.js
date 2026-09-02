const express = require("express");
const db = require("../db");

const router = express.Router();

router.get("/", (req, res) => {
  const { tournament_id } = req.query;
  if (!tournament_id) return res.status(400).json({ error: "tournament_id is required." });
  const rows = db
    .prepare(
      `SELECT p.*, t.team_name FROM points p
       JOIN team t ON t.team_id = p.team_id
       WHERE p.tournament_id = ?
       ORDER BY p.points DESC, p.won DESC, t.team_name ASC`
    )
    .all(tournament_id);
  res.json(rows);
});

module.exports = router;

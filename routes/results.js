const express = require("express");
const db = require("../db");
const { requireAdmin } = require("./middleware");

const router = express.Router();

router.get("/", (req, res) => {
  const { match_id, tournament_id } = req.query;
  if (match_id) {
    const row = db.prepare("SELECT * FROM result WHERE match_id = ?").get(match_id);
    return res.json(row || null);
  }
  if (tournament_id) {
    const rows = db
      .prepare(
        `SELECT r.*, m.tournament_id, m.round, m.team1_id AS m_team1_id, m.team2_id AS m_team2_id
         FROM result r JOIN match m ON m.match_id = r.match_id
         WHERE m.tournament_id = ?`
      )
      .all(tournament_id);
    return res.json(rows);
  }
  res.json(db.prepare("SELECT * FROM result").all());
});

// Admin: enter or update a match result. Recalculates the points table for league matches.
router.post("/", requireAdmin, (req, res) => {
  const { match_id, team1_score, team2_score, winner_id } = req.body || {};
  if (!match_id) return res.status(400).json({ error: "match_id is required." });

  const match = db.prepare("SELECT * FROM match WHERE match_id = ?").get(match_id);
  if (!match) return res.status(404).json({ error: "Match not found." });

  if (winner_id && String(winner_id) !== String(match.team1_id) && String(winner_id) !== String(match.team2_id)) {
    return res.status(400).json({ error: "winner_id must be one of the two teams in this match." });
  }

  const runAll = db.transaction(() => {
    const existing = db.prepare("SELECT * FROM result WHERE match_id = ?").get(match_id);
    const previousWinner = existing ? existing.winner_id : undefined;

    if (existing) {
      db.prepare("UPDATE result SET team1_score = ?, team2_score = ?, winner_id = ? WHERE match_id = ?").run(
        team1_score ?? existing.team1_score,
        team2_score ?? existing.team2_score,
        winner_id ?? existing.winner_id,
        match_id
      );
    } else {
      db.prepare(
        "INSERT INTO result (match_id, team1_score, team2_score, winner_id) VALUES (?, ?, ?, ?)"
      ).run(match_id, team1_score || null, team2_score || null, winner_id || null);
    }

    db.prepare("UPDATE match SET status = 'completed' WHERE match_id = ?").run(match_id);

    // Only league-stage matches feed the points table
    if (match.round === "league") {
      // Undo the previous contribution of this match, if any, before reapplying
      if (existing && previousWinner !== undefined) {
        undoPoints(match, previousWinner);
      }
      applyPoints(match, winner_id ?? null);
    }
  });
  runAll();

  res.status(201).json(db.prepare("SELECT * FROM result WHERE match_id = ?").get(match_id));
});

function ensurePointsRow(team_id, tournament_id) {
  const row = db.prepare("SELECT * FROM points WHERE team_id = ? AND tournament_id = ?").get(team_id, tournament_id);
  if (!row) {
    db.prepare(
      "INSERT INTO points (team_id, tournament_id, played, won, lost, draw, points) VALUES (?, ?, 0,0,0,0,0)"
    ).run(team_id, tournament_id);
  }
}

function applyPoints(match, winner_id) {
  const { tournament_id, team1_id, team2_id } = match;
  ensurePointsRow(team1_id, tournament_id);
  ensurePointsRow(team2_id, tournament_id);

  const bump = (team_id, field) => {
    db.prepare(
      `UPDATE points SET played = played + 1, ${field} = ${field} + 1,
       points = points + ? WHERE team_id = ? AND tournament_id = ?`
    ).run(field === "won" ? 2 : field === "draw" ? 1 : 0, team_id, tournament_id);
  };

  if (!winner_id) {
    bump(team1_id, "draw");
    bump(team2_id, "draw");
  } else if (String(winner_id) === String(team1_id)) {
    bump(team1_id, "won");
    bump(team2_id, "lost");
  } else {
    bump(team2_id, "won");
    bump(team1_id, "lost");
  }
}

function undoPoints(match, winner_id) {
  const { tournament_id, team1_id, team2_id } = match;
  const unbump = (team_id, field) => {
    db.prepare(
      `UPDATE points SET played = played - 1, ${field} = ${field} - 1,
       points = points - ? WHERE team_id = ? AND tournament_id = ?`
    ).run(field === "won" ? 2 : field === "draw" ? 1 : 0, team_id, tournament_id);
  };
  if (!winner_id) {
    unbump(team1_id, "draw");
    unbump(team2_id, "draw");
  } else if (String(winner_id) === String(team1_id)) {
    unbump(team1_id, "won");
    unbump(team2_id, "lost");
  } else {
    unbump(team2_id, "won");
    unbump(team1_id, "lost");
  }
}

// Public: tournament winner (result of the 'final' round match, if completed)
router.get("/winner/:tournament_id", (req, res) => {
  const final = db
    .prepare("SELECT * FROM match WHERE tournament_id = ? AND round = 'final'")
    .get(req.params.tournament_id);
  if (!final) return res.json({ declared: false });
  const result = db.prepare("SELECT * FROM result WHERE match_id = ?").get(final.match_id);
  if (!result || !result.winner_id) return res.json({ declared: false });
  const team = db.prepare("SELECT * FROM team WHERE team_id = ?").get(result.winner_id);
  res.json({ declared: true, team, match: final, result });
});

module.exports = router;

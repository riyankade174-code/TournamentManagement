const express = require("express");
const db = require("../db");
const { requireAdmin } = require("./middleware");

const router = express.Router();

function matchWithNames(row) {
  const t1 = db.prepare("SELECT team_name FROM team WHERE team_id = ?").get(row.team1_id);
  const t2 = db.prepare("SELECT team_name FROM team WHERE team_id = ?").get(row.team2_id);
  return { ...row, team1_name: t1 ? t1.team_name : null, team2_name: t2 ? t2.team_name : null };
}

// Public: list matches (optionally filtered by tournament_id / round)
router.get("/", (req, res) => {
  const { tournament_id, round } = req.query;
  let rows;
  if (tournament_id && round) {
    rows = db
      .prepare("SELECT * FROM match WHERE tournament_id = ? AND round = ? ORDER BY match_date, match_id")
      .all(tournament_id, round);
  } else if (tournament_id) {
    rows = db
      .prepare("SELECT * FROM match WHERE tournament_id = ? ORDER BY match_date, match_id")
      .all(tournament_id);
  } else {
    rows = db.prepare("SELECT * FROM match ORDER BY match_date, match_id").all();
  }
  res.json(rows.map(matchWithNames));
});

router.get("/:id", (req, res) => {
  const row = db.prepare("SELECT * FROM match WHERE match_id = ?").get(req.params.id);
  if (!row) return res.status(404).json({ error: "Match not found." });
  res.json(matchWithNames(row));
});

// Admin: add a single match manually
router.post("/", requireAdmin, (req, res) => {
  const { tournament_id, team1_id, team2_id, match_date, venue, round } = req.body || {};
  if (!tournament_id || !team1_id || !team2_id) {
    return res.status(400).json({ error: "tournament_id, team1_id and team2_id are required." });
  }
  if (String(team1_id) === String(team2_id)) {
    return res.status(400).json({ error: "A team cannot play itself." });
  }
  const info = db
    .prepare(
      `INSERT INTO match (tournament_id, team1_id, team2_id, match_date, venue, round, status)
       VALUES (?, ?, ?, ?, ?, ?, 'scheduled')`
    )
    .run(tournament_id, team1_id, team2_id, match_date || null, venue || null, round || "league");
  res.status(201).json(matchWithNames(db.prepare("SELECT * FROM match WHERE match_id = ?").get(info.lastInsertRowid)));
});

// Admin: auto-generate a full round-robin league schedule for a tournament
router.post("/generate-schedule", requireAdmin, (req, res) => {
  const { tournament_id, venue } = req.body || {};
  if (!tournament_id) return res.status(400).json({ error: "tournament_id is required." });

  const teams = db.prepare("SELECT * FROM team WHERE tournament_id = ?").all(tournament_id);
  if (teams.length < 2) {
    return res.status(400).json({ error: "At least 2 teams are needed to generate a schedule." });
  }

  const insert = db.prepare(
    `INSERT INTO match (tournament_id, team1_id, team2_id, venue, round, status)
     VALUES (?, ?, ?, ?, 'league', 'scheduled')`
  );

  const created = [];
  const runAll = db.transaction(() => {
    for (let i = 0; i < teams.length; i++) {
      for (let j = i + 1; j < teams.length; j++) {
        const info = insert.run(tournament_id, teams[i].team_id, teams[j].team_id, venue || null);
        created.push(info.lastInsertRowid);
      }
    }
    db.prepare("UPDATE tournament SET status = 'ongoing' WHERE tournament_id = ? AND status = 'upcoming'").run(
      tournament_id
    );
  });
  runAll();

  const rows = created.map((id) => matchWithNames(db.prepare("SELECT * FROM match WHERE match_id = ?").get(id)));
  res.status(201).json(rows);
});

// Admin: create the semi-final or final pairing from the current points-table standings
router.post("/generate-knockout", requireAdmin, (req, res) => {
  const { tournament_id, round, venue, match_date } = req.body || {};
  if (!tournament_id || !["semi", "final"].includes(round)) {
    return res.status(400).json({ error: "tournament_id and round ('semi' or 'final') are required." });
  }

  if (round === "semi") {
    const standings = db
      .prepare(
        `SELECT * FROM points WHERE tournament_id = ? ORDER BY points DESC, won DESC LIMIT 4`
      )
      .all(tournament_id);
    if (standings.length < 4) {
      return res.status(400).json({ error: "Need at least 4 teams in the points table to set up semi-finals." });
    }
    const insert = db.prepare(
      `INSERT INTO match (tournament_id, team1_id, team2_id, match_date, venue, round, status)
       VALUES (?, ?, ?, ?, ?, 'semi', 'scheduled')`
    );
    const created = [];
    const runAll = db.transaction(() => {
      // 1st vs 4th, 2nd vs 3rd
      created.push(insert.run(tournament_id, standings[0].team_id, standings[3].team_id, match_date || null, venue || null).lastInsertRowid);
      created.push(insert.run(tournament_id, standings[1].team_id, standings[2].team_id, match_date || null, venue || null).lastInsertRowid);
    });
    runAll();
    return res
      .status(201)
      .json(created.map((id) => matchWithNames(db.prepare("SELECT * FROM match WHERE match_id = ?").get(id))));
  }

  // Final: pull the two semi-final winners
  const semis = db
    .prepare("SELECT m.*, r.winner_id FROM match m LEFT JOIN result r ON r.match_id = m.match_id WHERE m.tournament_id = ? AND m.round = 'semi'")
    .all(tournament_id);
  if (semis.length !== 2 || semis.some((m) => !m.winner_id)) {
    return res.status(400).json({ error: "Both semi-final results must be entered before generating the final." });
  }
  const info = db
    .prepare(
      `INSERT INTO match (tournament_id, team1_id, team2_id, match_date, venue, round, status)
       VALUES (?, ?, ?, ?, ?, 'final', 'scheduled')`
    )
    .run(tournament_id, semis[0].winner_id, semis[1].winner_id, match_date || null, venue || null);
  res.status(201).json(matchWithNames(db.prepare("SELECT * FROM match WHERE match_id = ?").get(info.lastInsertRowid)));
});

router.put("/:id", requireAdmin, (req, res) => {
  const existing = db.prepare("SELECT * FROM match WHERE match_id = ?").get(req.params.id);
  if (!existing) return res.status(404).json({ error: "Match not found." });
  const { match_date, venue, status } = req.body || {};
  db.prepare("UPDATE match SET match_date = ?, venue = ?, status = ? WHERE match_id = ?").run(
    match_date ?? existing.match_date,
    venue ?? existing.venue,
    status ?? existing.status,
    req.params.id
  );
  res.json(matchWithNames(db.prepare("SELECT * FROM match WHERE match_id = ?").get(req.params.id)));
});

router.delete("/:id", requireAdmin, (req, res) => {
  const info = db.prepare("DELETE FROM match WHERE match_id = ?").run(req.params.id);
  if (info.changes === 0) return res.status(404).json({ error: "Match not found." });
  res.json({ ok: true });
});

module.exports = router;

/* ---------------- API helper ---------------- */
async function api(path, opts = {}) {
  const res = await fetch("/api" + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error((data && data.error) || "Request failed");
  return data;
}

function toast(msg, isError) {
  const root = document.getElementById("toast-root");
  const el = document.createElement("div");
  el.className = "toast" + (isError ? " error" : "");
  el.textContent = msg;
  root.appendChild(el);
  setTimeout(() => el.remove(), 3200);
}

function escapeHtml(str) {
  return String(str ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function fmtDate(d) {
  if (!d) return "TBD";
  const dt = new Date(d);
  return isNaN(dt) ? d : dt.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

/* ---------------- Auth ---------------- */
const loginScreen = document.getElementById("login-screen");
const adminShell = document.getElementById("admin-shell");
const adminMain = document.getElementById("admin-main");

async function checkAuth() {
  try {
    await api("/auth/me");
    loginScreen.style.display = "none";
    adminShell.style.display = "grid";
    initNav();
    routeSection();
  } catch {
    loginScreen.style.display = "flex";
    adminShell.style.display = "none";
  }
}

document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;
  const errBox = document.getElementById("login-error");
  errBox.textContent = "";
  try {
    await api("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
    checkAuth();
  } catch (err) {
    errBox.textContent = err.message;
  }
});

document.getElementById("logout-btn").addEventListener("click", async () => {
  await api("/auth/logout", { method: "POST" });
  checkAuth();
});

/* ---------------- Nav / routing ---------------- */
function initNav() {
  window.addEventListener("hashchange", routeSection);
}

const SECTIONS = ["tournaments", "teams", "matches", "results", "points", "knockout"];

function routeSection() {
  let section = (location.hash || "#tournaments").replace("#", "");
  if (!SECTIONS.includes(section)) section = "tournaments";
  document.querySelectorAll("#admin-nav a").forEach((a) => {
    a.classList.toggle("active", a.dataset.section === section);
  });
  const renderers = {
    tournaments: renderTournaments,
    teams: renderTeams,
    matches: renderMatches,
    results: renderResults,
    points: renderPoints,
    knockout: renderKnockout,
  };
  renderers[section]();
}

/* App-wide state: which tournament is currently selected across sections */
const state = {
  tournamentId: localStorage.getItem("tms_selected_tournament") || null,
  teamId: null,
};

function setSelectedTournament(id) {
  state.tournamentId = id;
  localStorage.setItem("tms_selected_tournament", id);
}

async function tournamentPicker(onChange) {
  const tournaments = await api("/tournaments");
  if (!state.tournamentId && tournaments.length) state.tournamentId = String(tournaments[0].tournament_id);
  const options = tournaments
    .map((t) => `<option value="${t.tournament_id}" ${String(t.tournament_id) === String(state.tournamentId) ? "selected" : ""}>${escapeHtml(t.name)} (${t.sport})</option>`)
    .join("");
  return `
    <div class="field" style="max-width:340px;">
      <label>Tournament</label>
      <select id="tournament-picker">${options || "<option value=''>No tournaments yet</option>"}</select>
    </div>
  `;
}

function bindTournamentPicker(callback) {
  const sel = document.getElementById("tournament-picker");
  if (!sel) return;
  sel.addEventListener("change", () => {
    setSelectedTournament(sel.value);
    callback();
  });
}

/* ================= TOURNAMENTS ================= */
async function renderTournaments() {
  adminMain.innerHTML = `
    <h1>Tournaments</h1>
    <div class="panel">
      <h3>Create tournament</h3>
      <form id="t-form" class="form-grid">
        <div class="field"><label>Name</label><input name="name" required placeholder="College Cricket Tournament 2026" /></div>
        <div class="field"><label>Sport</label>
          <select name="sport">
            <option>Cricket</option><option>Football</option><option>Volleyball</option>
            <option>Basketball</option><option>Badminton</option>
          </select>
        </div>
        <div class="field"><label>Start date</label><input name="start_date" type="date" /></div>
        <div class="field"><label>End date</label><input name="end_date" type="date" /></div>
        <div class="field" style="align-self:end;"><button class="btn" type="submit">Add tournament</button></div>
      </form>
    </div>
    <div class="panel">
      <h3>All tournaments</h3>
      <div id="t-list"></div>
    </div>
  `;

  document.getElementById("t-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await api("/tournaments", { method: "POST", body: JSON.stringify(Object.fromEntries(fd)) });
      toast("Tournament created.");
      e.target.reset();
      renderTournaments();
    } catch (err) {
      toast(err.message, true);
    }
  });

  const list = document.getElementById("t-list");
  const tournaments = await api("/tournaments");
  if (!tournaments.length) {
    list.innerHTML = `<div class="empty-state">No tournaments yet. Create one above.</div>`;
    return;
  }
  list.innerHTML = `
    <table class="scoreboard">
      <thead><tr><th>Name</th><th>Sport</th><th>Dates</th><th>Status</th><th></th></tr></thead>
      <tbody>
        ${tournaments.map((t) => `
          <tr>
            <td>${escapeHtml(t.name)}</td>
            <td>${escapeHtml(t.sport)}</td>
            <td>${fmtDate(t.start_date)} – ${fmtDate(t.end_date)}</td>
            <td>
              <select data-status-id="${t.tournament_id}">
                ${["upcoming", "ongoing", "completed"].map((s) => `<option value="${s}" ${s === t.status ? "selected" : ""}>${s}</option>`).join("")}
              </select>
            </td>
            <td class="row-actions">
              <button class="btn subtle" data-select="${t.tournament_id}">Select</button>
              <button class="btn danger" data-delete="${t.tournament_id}">Delete</button>
            </td>
          </tr>`).join("")}
      </tbody>
    </table>
  `;

  list.querySelectorAll("[data-status-id]").forEach((sel) => {
    sel.addEventListener("change", async () => {
      try {
        await api(`/tournaments/${sel.dataset.statusId}`, { method: "PUT", body: JSON.stringify({ status: sel.value }) });
        toast("Status updated.");
      } catch (err) {
        toast(err.message, true);
      }
    });
  });
  list.querySelectorAll("[data-select]").forEach((btn) => {
    btn.addEventListener("click", () => {
      setSelectedTournament(btn.dataset.select);
      toast("Tournament selected for other sections.");
    });
  });
  list.querySelectorAll("[data-delete]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("Delete this tournament and all its teams, matches, and results?")) return;
      try {
        await api(`/tournaments/${btn.dataset.delete}`, { method: "DELETE" });
        toast("Tournament deleted.");
        renderTournaments();
      } catch (err) {
        toast(err.message, true);
      }
    });
  });
}

/* ================= TEAMS & PLAYERS ================= */
async function renderTeams() {
  const picker = await tournamentPicker(renderTeams);
  adminMain.innerHTML = `
    <h1>Teams &amp; Players</h1>
    ${picker}
    <div class="panel">
      <h3>Add team</h3>
      <form id="team-form" class="form-grid">
        <div class="field"><label>Team name</label><input name="team_name" required /></div>
        <div class="field"><label>Captain</label><input name="captain" /></div>
        <div class="field" style="align-self:end;"><button class="btn" type="submit">Add team</button></div>
      </form>
    </div>
    <div class="panel"><h3>Teams</h3><div id="team-list"></div></div>
    <div class="panel" id="player-panel" style="display:none;">
      <h3 id="player-panel-title">Players</h3>
      <form id="player-form" class="form-grid">
        <div class="field"><label>Player name</label><input name="player_name" required /></div>
        <div class="field"><label>Age</label><input name="age" type="number" min="1" /></div>
        <div class="field" style="align-self:end;"><button class="btn" type="submit">Add player</button></div>
      </form>
      <div id="player-list" style="margin-top:14px;"></div>
    </div>
  `;
  bindTournamentPicker(renderTeams);
  if (!state.tournamentId) return;

  document.getElementById("team-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = Object.fromEntries(new FormData(e.target));
    try {
      await api("/teams", { method: "POST", body: JSON.stringify({ ...fd, tournament_id: state.tournamentId }) });
      toast("Team added.");
      e.target.reset();
      renderTeams();
    } catch (err) {
      toast(err.message, true);
    }
  });

  const teamList = document.getElementById("team-list");
  const teams = await api(`/teams?tournament_id=${state.tournamentId}`);
  if (!teams.length) {
    teamList.innerHTML = `<div class="empty-state">No teams yet. Add one above.</div>`;
  } else {
    teamList.innerHTML = `
      <table class="scoreboard">
        <thead><tr><th>Team</th><th>Captain</th><th></th></tr></thead>
        <tbody>
          ${teams.map((tm) => `
            <tr>
              <td>${escapeHtml(tm.team_name)}</td>
              <td>${escapeHtml(tm.captain || "—")}</td>
              <td class="row-actions">
                <button class="btn subtle" data-players="${tm.team_id}">Players</button>
                <button class="btn danger" data-delete-team="${tm.team_id}">Delete</button>
              </td>
            </tr>`).join("")}
        </tbody>
      </table>
    `;
    teamList.querySelectorAll("[data-delete-team]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm("Delete this team and its players?")) return;
        try {
          await api(`/teams/${btn.dataset.deleteTeam}`, { method: "DELETE" });
          toast("Team deleted.");
          renderTeams();
        } catch (err) {
          toast(err.message, true);
        }
      });
    });
    teamList.querySelectorAll("[data-players]").forEach((btn) => {
      btn.addEventListener("click", () => openPlayerPanel(Number(btn.dataset.players), teams));
    });
  }
}

async function openPlayerPanel(teamId, teams) {
  state.teamId = teamId;
  const team = teams.find((t) => t.team_id === teamId);
  const panel = document.getElementById("player-panel");
  panel.style.display = "block";
  document.getElementById("player-panel-title").textContent = `Players — ${team.team_name}`;
  panel.scrollIntoView({ behavior: "smooth" });

  const form = document.getElementById("player-form");
  form.onsubmit = async (e) => {
    e.preventDefault();
    const fd = Object.fromEntries(new FormData(e.target));
    try {
      await api("/players", { method: "POST", body: JSON.stringify({ ...fd, team_id: teamId }) });
      toast("Player added.");
      e.target.reset();
      loadPlayers(teamId);
    } catch (err) {
      toast(err.message, true);
    }
  };
  loadPlayers(teamId);
}

async function loadPlayers(teamId) {
  const players = await api(`/players?team_id=${teamId}`);
  const list = document.getElementById("player-list");
  if (!players.length) {
    list.innerHTML = `<div class="empty-state">No players yet.</div>`;
    return;
  }
  list.innerHTML = `
    <table class="scoreboard">
      <thead><tr><th>Player</th><th class="num">Age</th><th></th></tr></thead>
      <tbody>
        ${players.map((p) => `
          <tr>
            <td>${escapeHtml(p.player_name)}</td>
            <td class="num">${p.age ?? "—"}</td>
            <td class="row-actions"><button class="btn danger" data-del-player="${p.player_id}">Delete</button></td>
          </tr>`).join("")}
      </tbody>
    </table>
  `;
  list.querySelectorAll("[data-del-player]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await api(`/players/${btn.dataset.delPlayer}`, { method: "DELETE" });
        toast("Player removed.");
        loadPlayers(teamId);
      } catch (err) {
        toast(err.message, true);
      }
    });
  });
}

/* ================= MATCHES ================= */
async function renderMatches() {
  const picker = await tournamentPicker(renderMatches);
  adminMain.innerHTML = `
    <h1>Match Schedule</h1>
    ${picker}
    <div class="panel">
      <h3>Generate league schedule</h3>
      <p style="color:var(--mist); font-size:0.85rem; margin-top:-6px;">Creates a round-robin fixture — every team plays every other team once.</p>
      <div class="form-grid">
        <div class="field"><label>Venue (applied to all matches)</label><input id="sched-venue" placeholder="Main Ground" /></div>
        <div class="field" style="align-self:end;"><button class="btn" id="gen-schedule-btn">Generate schedule</button></div>
      </div>
    </div>
    <div class="panel">
      <h3>Add a single match</h3>
      <form id="match-form" class="form-grid">
        <div class="field"><label>Team 1</label><select name="team1_id" id="m-team1"></select></div>
        <div class="field"><label>Team 2</label><select name="team2_id" id="m-team2"></select></div>
        <div class="field"><label>Date</label><input name="match_date" type="date" /></div>
        <div class="field"><label>Venue</label><input name="venue" /></div>
        <div class="field" style="align-self:end;"><button class="btn" type="submit">Add match</button></div>
      </form>
    </div>
    <div class="panel"><h3>League fixtures</h3><div id="match-list"></div></div>
  `;
  bindTournamentPicker(renderMatches);
  if (!state.tournamentId) return;

  const teams = await api(`/teams?tournament_id=${state.tournamentId}`);
  const teamOptions = teams.map((t) => `<option value="${t.team_id}">${escapeHtml(t.team_name)}</option>`).join("");
  document.getElementById("m-team1").innerHTML = teamOptions;
  document.getElementById("m-team2").innerHTML = teamOptions;

  document.getElementById("gen-schedule-btn").addEventListener("click", async () => {
    const venue = document.getElementById("sched-venue").value;
    try {
      await api("/matches/generate-schedule", { method: "POST", body: JSON.stringify({ tournament_id: state.tournamentId, venue }) });
      toast("Schedule generated.");
      renderMatches();
    } catch (err) {
      toast(err.message, true);
    }
  });

  document.getElementById("match-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = Object.fromEntries(new FormData(e.target));
    try {
      await api("/matches", { method: "POST", body: JSON.stringify({ ...fd, tournament_id: state.tournamentId, round: "league" }) });
      toast("Match added.");
      renderMatches();
    } catch (err) {
      toast(err.message, true);
    }
  });

  const matches = await api(`/matches?tournament_id=${state.tournamentId}&round=league`);
  const list = document.getElementById("match-list");
  if (!matches.length) {
    list.innerHTML = `<div class="empty-state">No matches scheduled yet.</div>`;
    return;
  }
  list.innerHTML = `
    <table class="scoreboard">
      <thead><tr><th>Match</th><th>Date</th><th>Venue</th><th>Status</th><th></th></tr></thead>
      <tbody>
        ${matches.map((m) => `
          <tr>
            <td>${escapeHtml(m.team1_name)} vs ${escapeHtml(m.team2_name)}</td>
            <td>${fmtDate(m.match_date)}</td>
            <td>${escapeHtml(m.venue || "—")}</td>
            <td>${m.status}</td>
            <td class="row-actions"><button class="btn danger" data-del-match="${m.match_id}">Delete</button></td>
          </tr>`).join("")}
      </tbody>
    </table>
  `;
  list.querySelectorAll("[data-del-match]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await api(`/matches/${btn.dataset.delMatch}`, { method: "DELETE" });
        toast("Match deleted.");
        renderMatches();
      } catch (err) {
        toast(err.message, true);
      }
    });
  });
}

/* ================= RESULTS ================= */
async function renderResults() {
  const picker = await tournamentPicker(renderResults);
  adminMain.innerHTML = `
    <h1>Scores &amp; Results</h1>
    ${picker}
    <div class="panel"><h3>Enter results — league matches</h3><div id="results-list"></div></div>
  `;
  bindTournamentPicker(renderResults);
  if (!state.tournamentId) return;

  const [matches, results] = await Promise.all([
    api(`/matches?tournament_id=${state.tournamentId}&round=league`),
    api(`/results?tournament_id=${state.tournamentId}`),
  ]);
  const resultByMatch = {};
  results.forEach((r) => (resultByMatch[r.match_id] = r));

  const list = document.getElementById("results-list");
  if (!matches.length) {
    list.innerHTML = `<div class="empty-state">Generate a schedule first, on the Match Schedule tab.</div>`;
    return;
  }
  list.innerHTML = matches
    .map((m) => {
      const r = resultByMatch[m.match_id];
      return `
      <div class="panel" style="margin-bottom:12px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
          <strong>${escapeHtml(m.team1_name)} vs ${escapeHtml(m.team2_name)}</strong>
          <span class="status-pill status-${m.status === "completed" ? "completed" : "upcoming"}">${m.status}</span>
        </div>
        <form class="form-grid result-form" data-match="${m.match_id}" data-t1="${m.team1_id}" data-t2="${m.team2_id}">
          <div class="field"><label>${escapeHtml(m.team1_name)} score</label><input name="team1_score" value="${r ? escapeHtml(r.team1_score) : ""}" placeholder="e.g. 165/6" /></div>
          <div class="field"><label>${escapeHtml(m.team2_name)} score</label><input name="team2_score" value="${r ? escapeHtml(r.team2_score) : ""}" placeholder="e.g. 150/8" /></div>
          <div class="field"><label>Winner</label>
            <select name="winner_id">
              <option value="">Draw / tie</option>
              <option value="${m.team1_id}" ${r && String(r.winner_id) === String(m.team1_id) ? "selected" : ""}>${escapeHtml(m.team1_name)}</option>
              <option value="${m.team2_id}" ${r && String(r.winner_id) === String(m.team2_id) ? "selected" : ""}>${escapeHtml(m.team2_name)}</option>
            </select>
          </div>
          <div class="field" style="align-self:end;"><button class="btn" type="submit">${r ? "Update result" : "Save result"}</button></div>
        </form>
      </div>`;
    })
    .join("");

  list.querySelectorAll(".result-form").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = Object.fromEntries(new FormData(e.target));
      try {
        await api("/results", {
          method: "POST",
          body: JSON.stringify({
            match_id: form.dataset.match,
            team1_score: fd.team1_score,
            team2_score: fd.team2_score,
            winner_id: fd.winner_id || null,
          }),
        });
        toast("Result saved — points table updated.");
        renderResults();
      } catch (err) {
        toast(err.message, true);
      }
    });
  });
}

/* ================= POINTS ================= */
async function renderPoints() {
  const picker = await tournamentPicker(renderPoints);
  adminMain.innerHTML = `
    <h1>Points Table</h1>
    ${picker}
    <div class="panel"><div id="points-table"></div></div>
  `;
  bindTournamentPicker(renderPoints);
  if (!state.tournamentId) return;

  const points = await api(`/points?tournament_id=${state.tournamentId}`);
  const box = document.getElementById("points-table");
  if (!points.length) {
    box.innerHTML = `<div class="empty-state">No teams yet.</div>`;
    return;
  }
  box.innerHTML = `
    <table class="scoreboard">
      <thead><tr><th>Team</th><th class="num">P</th><th class="num">W</th><th class="num">L</th><th class="num">D</th><th class="num">Pts</th></tr></thead>
      <tbody>
        ${points.map((p, i) => `
          <tr class="${i < 4 ? "qualify" : ""}">
            <td>${escapeHtml(p.team_name)}</td>
            <td class="num">${p.played}</td><td class="num">${p.won}</td><td class="num">${p.lost}</td><td class="num">${p.draw}</td>
            <td class="num"><span class="digit-chip">${p.points}</span></td>
          </tr>`).join("")}
      </tbody>
    </table>
    <p style="color:var(--mist); font-size:0.8rem; margin-top:10px;">Highlighted rows mark the top 4 teams, who qualify for the semi-finals.</p>
  `;
}

/* ================= KNOCKOUT ================= */
async function renderKnockout() {
  const picker = await tournamentPicker(renderKnockout);
  adminMain.innerHTML = `
    <h1>Knockout Stage &amp; Winner</h1>
    ${picker}
    <div class="panel">
      <h3>Semi-finals</h3>
      <p style="color:var(--mist); font-size:0.85rem; margin-top:-6px;">Pairs the top 4 teams from the points table: 1st vs 4th, 2nd vs 3rd.</p>
      <button class="btn" id="gen-semi-btn">Generate semi-finals</button>
      <div id="semi-list" style="margin-top:16px;"></div>
    </div>
    <div class="panel">
      <h3>Final</h3>
      <p style="color:var(--mist); font-size:0.85rem; margin-top:-6px;">Available once both semi-final results are entered.</p>
      <button class="btn" id="gen-final-btn">Generate final</button>
      <div id="final-box" style="margin-top:16px;"></div>
    </div>
    <div class="panel" id="winner-box"></div>
  `;
  bindTournamentPicker(renderKnockout);
  if (!state.tournamentId) return;

  document.getElementById("gen-semi-btn").addEventListener("click", async () => {
    try {
      await api("/matches/generate-knockout", { method: "POST", body: JSON.stringify({ tournament_id: state.tournamentId, round: "semi" }) });
      toast("Semi-finals created.");
      renderKnockout();
    } catch (err) {
      toast(err.message, true);
    }
  });
  document.getElementById("gen-final-btn").addEventListener("click", async () => {
    try {
      await api("/matches/generate-knockout", { method: "POST", body: JSON.stringify({ tournament_id: state.tournamentId, round: "final" }) });
      toast("Final created.");
      renderKnockout();
    } catch (err) {
      toast(err.message, true);
    }
  });

  await renderKnockoutRound("semi", "semi-list");
  await renderKnockoutRound("final", "final-box");

  const winner = await api(`/results/winner/${state.tournamentId}`);
  const winBox = document.getElementById("winner-box");
  winBox.innerHTML = winner.declared
    ? `<div class="winner-banner"><span class="eyebrow">Winner declared</span><h2>🏆 ${escapeHtml(winner.team.team_name)}</h2></div>`
    : `<div class="empty-state">Winner will appear here once the final result is entered.</div>`;
}

async function renderKnockoutRound(round, elementId) {
  const box = document.getElementById(elementId);
  const matches = await api(`/matches?tournament_id=${state.tournamentId}&round=${round}`);
  if (!matches.length) {
    box.innerHTML = `<div class="empty-state">Not generated yet.</div>`;
    return;
  }
  const results = await api(`/results?tournament_id=${state.tournamentId}`);
  const resultByMatch = {};
  results.forEach((r) => (resultByMatch[r.match_id] = r));

  box.innerHTML = matches
    .map((m) => {
      const r = resultByMatch[m.match_id];
      return `
      <form class="form-grid result-form-ko" data-match="${m.match_id}" style="margin-bottom:12px; border-bottom:1px solid var(--line); padding-bottom:12px;">
        <div class="field" style="grid-column: span 2;"><label>${escapeHtml(m.team1_name)} vs ${escapeHtml(m.team2_name)}</label></div>
        <div class="field"><label>${escapeHtml(m.team1_name)} score</label><input name="team1_score" value="${r ? escapeHtml(r.team1_score) : ""}" /></div>
        <div class="field"><label>${escapeHtml(m.team2_name)} score</label><input name="team2_score" value="${r ? escapeHtml(r.team2_score) : ""}" /></div>
        <div class="field"><label>Winner</label>
          <select name="winner_id">
            <option value="">—</option>
            <option value="${m.team1_id}" ${r && String(r.winner_id) === String(m.team1_id) ? "selected" : ""}>${escapeHtml(m.team1_name)}</option>
            <option value="${m.team2_id}" ${r && String(r.winner_id) === String(m.team2_id) ? "selected" : ""}>${escapeHtml(m.team2_name)}</option>
          </select>
        </div>
        <div class="field" style="align-self:end;"><button class="btn" type="submit">${r ? "Update" : "Save"}</button></div>
      </form>`;
    })
    .join("");

  box.querySelectorAll(".result-form-ko").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = Object.fromEntries(new FormData(e.target));
      try {
        await api("/results", {
          method: "POST",
          body: JSON.stringify({
            match_id: form.dataset.match,
            team1_score: fd.team1_score,
            team2_score: fd.team2_score,
            winner_id: fd.winner_id || null,
          }),
        });
        toast("Result saved.");
        renderKnockout();
      } catch (err) {
        toast(err.message, true);
      }
    });
  });
}

checkAuth();

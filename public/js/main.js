const app = document.getElementById("app");
const ticker = document.getElementById("ticker");

async function api(path, opts) {
  const res = await fetch("/api" + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error((data && data.error) || "Request failed");
  return data;
}

function fmtDate(d) {
  if (!d) return "TBD";
  const dt = new Date(d);
  if (isNaN(dt)) return d;
  return dt.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

function statusPill(status) {
  return `<span class="status-pill status-${status}">${status}</span>`;
}

/* ---------------- Router ---------------- */
window.addEventListener("hashchange", render);
window.addEventListener("DOMContentLoaded", () => {
  render();
  loadTicker();
});

function render() {
  const hash = location.hash || "#/";
  const detailMatch = hash.match(/^#\/tournament\/(\d+)/);
  if (detailMatch) {
    renderTournamentDetail(Number(detailMatch[1]));
  } else {
    renderTournamentList();
  }
}

/* ---------------- Ticker ---------------- */
async function loadTicker() {
  try {
    const tournaments = await api("/tournaments");
    let items = [];
    for (const t of tournaments) {
      const results = await api(`/results?tournament_id=${t.tournament_id}`);
      for (const r of results) {
        const t1 = await teamName(r.m_team1_id);
        const t2 = await teamName(r.m_team2_id);
        items.push(
          `<span class="ticker-item">${escapeHtml(t.name)}: <b>${t1}</b> ${r.team1_score ?? ""} vs <b>${t2}</b> ${r.team2_score ?? ""}${r.winner_id ? ` — <span class="w">W: ${await teamName(r.winner_id)}</span>` : " — Draw"}</span>`
        );
      }
    }
    if (items.length === 0) {
      ticker.innerHTML = `<span class="ticker-item">No results yet — check back once matches are played.</span>`;
    } else {
      const html = items.join('<span class="ticker-item">•</span>');
      ticker.innerHTML = html + html; // duplicate for seamless scroll loop
    }
  } catch (e) {
    ticker.innerHTML = `<span class="ticker-item">Live ticker unavailable.</span>`;
  }
}

const teamCache = {};
async function teamName(id) {
  if (!id) return "—";
  if (teamCache[id]) return teamCache[id];
  try {
    const t = await api(`/teams/${id}`);
    teamCache[id] = t.team_name;
    return t.team_name;
  } catch {
    return "Unknown";
  }
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

/* ---------------- Tournament list ---------------- */
async function renderTournamentList() {
  app.innerHTML = `
    <section class="hero wrap">
      <span class="eyebrow">College &middot; Multi-sport &middot; Live standings</span>
      <h1>Every tournament,<br/>one scoreboard.</h1>
      <p class="lead">Browse active tournaments, follow the match schedule, and track the points table as teams push toward the final.</p>
    </section>
    <section class="wrap" style="padding-bottom:48px;">
      <div id="tlist" class="grid"></div>
    </section>
  `;
  const list = document.getElementById("tlist");
  try {
    const tournaments = await api("/tournaments");
    if (tournaments.length === 0) {
      list.innerHTML = `<div class="empty-state">No tournaments have been created yet. Check back soon.</div>`;
      return;
    }
    list.innerHTML = tournaments
      .map(
        (t) => `
      <a class="card" href="#/tournament/${t.tournament_id}">
        <span class="sport-tag">${escapeHtml(t.sport)}</span>
        ${statusPill(t.status)}
        <h3 style="margin-top:10px;">${escapeHtml(t.name)}</h3>
        <div class="meta">${fmtDate(t.start_date)} — ${fmtDate(t.end_date)}</div>
      </a>`
      )
      .join("");
  } catch (e) {
    list.innerHTML = `<div class="empty-state">Could not load tournaments.</div>`;
  }
}

/* ---------------- Tournament detail ---------------- */
async function renderTournamentDetail(id) {
  app.innerHTML = `<div class="wrap" style="padding:48px 0;">Loading…</div>`;
  try {
    const [t, teams, points, winner] = await Promise.all([
      api(`/tournaments/${id}`),
      api(`/teams?tournament_id=${id}`),
      api(`/points?tournament_id=${id}`),
      api(`/results/winner/${id}`),
    ]);
    const leagueMatches = await api(`/matches?tournament_id=${id}&round=league`);
    const semiMatches = await api(`/matches?tournament_id=${id}&round=semi`);
    const finalMatches = await api(`/matches?tournament_id=${id}&round=final`);
    const results = await api(`/results?tournament_id=${id}`);
    const resultByMatch = {};
    results.forEach((r) => (resultByMatch[r.match_id] = r));

    app.innerHTML = `
      <section class="wrap" style="padding-top:36px;">
        <a href="#/" style="color:var(--mist); font-size:0.85rem;">&larr; All tournaments</a>
        <div style="margin-top:14px;">
          <span class="sport-tag">${escapeHtml(t.sport)}</span> ${statusPill(t.status)}
          <h1 style="margin-top:8px;">${escapeHtml(t.name)}</h1>
          <div class="meta" style="color:var(--mist); margin-top:6px;">${fmtDate(t.start_date)} — ${fmtDate(t.end_date)}</div>
        </div>

        ${winner.declared ? `
        <div class="winner-banner" style="margin-top:28px;">
          <span class="eyebrow">Tournament Winner</span>
          <h2>🏆 ${escapeHtml(winner.team.team_name)}</h2>
        </div>` : ""}

        <section class="block">
          <div class="block-head"><h2>Teams</h2></div>
          <div class="grid">
            ${teams.length ? teams.map((tm) => `
              <div class="card">
                <h3>${escapeHtml(tm.team_name)}</h3>
                <div class="meta">Captain: ${escapeHtml(tm.captain || "—")}</div>
              </div>`).join("") : `<div class="empty-state">No teams registered yet.</div>`}
          </div>
        </section>

        <section class="block">
          <div class="block-head"><h2>Points Table</h2></div>
          ${renderPointsTable(points)}
        </section>

        ${renderMatchSection("League Schedule &amp; Results", leagueMatches, resultByMatch)}
        ${semiMatches.length ? renderMatchSection("Semi-Finals", semiMatches, resultByMatch) : ""}
        ${finalMatches.length ? renderMatchSection("Final", finalMatches, resultByMatch) : ""}
      </section>
    `;
  } catch (e) {
    app.innerHTML = `<div class="wrap"><div class="empty-state">Tournament not found.</div></div>`;
  }
}

function renderPointsTable(points) {
  if (!points.length) return `<div class="empty-state">Points table will appear once teams are added.</div>`;
  return `
    <table class="scoreboard">
      <thead><tr>
        <th>Team</th><th class="num">P</th><th class="num">W</th><th class="num">L</th><th class="num">D</th><th class="num">Pts</th>
      </tr></thead>
      <tbody>
        ${points.map((p, i) => `
          <tr class="${i < 4 ? "qualify" : ""}">
            <td>${escapeHtml(p.team_name)}</td>
            <td class="num">${p.played}</td>
            <td class="num">${p.won}</td>
            <td class="num">${p.lost}</td>
            <td class="num">${p.draw}</td>
            <td class="num"><span class="digit-chip">${p.points}</span></td>
          </tr>`).join("")}
      </tbody>
    </table>
  `;
}

function renderMatchSection(title, matches, resultByMatch) {
  return `
    <section class="block">
      <div class="block-head"><h2>${title}</h2></div>
      ${matches.length ? matches.map((m) => {
        const r = resultByMatch[m.match_id];
        const w1 = r && r.winner_id && String(r.winner_id) === String(m.team1_id);
        const w2 = r && r.winner_id && String(r.winner_id) === String(m.team2_id);
        return `
        <div class="match-row ${w1 ? "winner-team1" : ""} ${w2 ? "winner-team2" : ""}">
          <div class="team left">${escapeHtml(m.team1_name || "TBD")}</div>
          <div class="score">${r ? `${r.team1_score ?? "-"}` : ""}<div class="vs">vs</div>${r ? `${r.team2_score ?? "-"}` : (m.status === "completed" ? "" : fmtDate(m.match_date))}</div>
          <div class="team right">${escapeHtml(m.team2_name || "TBD")}</div>
          <div class="meta-col">${m.venue ? escapeHtml(m.venue) : ""}${m.status === "completed" ? " · Final" : " · " + fmtDate(m.match_date)}</div>
        </div>`;
      }).join("") : `<div class="empty-state">No matches scheduled yet.</div>`}
    </section>
  `;
}

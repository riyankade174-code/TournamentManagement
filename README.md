# Web-Based Sports Tournament Management System

A full working implementation of the Tournament Management System spec: tournaments,
teams, players, round-robin scheduling, score entry, an auto-calculated points table,
and a semi-final → final knockout stage with automatic winner declaration.

Built with **Node.js + Express + SQLite** instead of PHP/MySQL so it runs anywhere with
just Node installed — the database schema mirrors the tables from the spec 1:1 (admin,
tournament, team, player, match, result, points), just in SQLite instead of MySQL. If you
need MySQL specifically for a college submission, the schema in `db/index.js` translates
directly (see the "Switching to MySQL" note below).

## Requirements
- Node.js 18+ (tested on Node 22)

## Setup

```bash
npm install
npm start
```

Then open:
- **Public site:** http://localhost:3000
- **Admin dashboard:** http://localhost:3000/admin

A default admin account is created automatically the first time you run it:
- **Email:** `admin@tms.local`
- **Password:** `admin123`

(Change the seeded password in `db/index.js`, or add a new admin row directly and delete
the seed block, before deploying anywhere public.)

## How to use it

1. **Log in** to `/admin`.
2. **Tournaments** tab → create a tournament (name, sport, dates).
3. **Teams & Players** tab → pick the tournament, add teams (and players under each team).
4. **Match Schedule** tab → click **Generate schedule** to auto-create a round-robin
   league fixture (every team plays every other team once — matches the doc's 4-team,
   6-match example exactly).
5. **Scores & Results** tab → enter each match's score and winner (or leave winner blank
   for a draw). The **points table updates automatically** the moment you save a result.
6. **Points Table** tab → view live standings; the top 4 rows are highlighted as the
   knockout qualification zone.
7. **Knockout & Winner** tab →
   - **Generate semi-finals** pairs the current top 4 teams (1st vs 4th, 2nd vs 3rd).
   - Enter both semi-final results.
   - **Generate final** becomes available once both semis are decided.
   - Enter the final's result — the **winner is declared automatically** and shown both
     here and on the public tournament page.

The **public site** (`/`) is read-only: anyone can browse tournaments, teams, the match
schedule, live results, the points table, and the winner banner once declared, without
logging in. A scrolling ticker on the homepage shows recent results across all
tournaments.

## Project structure

```
server.js            Express app entry point
db/index.js           SQLite schema + connection (mirrors the spec's ER diagram)
routes/               REST API: auth, tournaments, teams, players, matches, results, points
public/index.html     Public viewer (single-page, hash-routed)
public/admin.html     Admin dashboard shell
public/js/main.js     Public viewer logic
public/js/admin.js    Admin dashboard logic
public/css/style.css  Shared styling
```

## API overview

All endpoints are under `/api`. Reads (GET) are public; writes (POST/PUT/DELETE) require
an authenticated admin session (`/api/auth/login`).

| Endpoint | Purpose |
|---|---|
| `POST /api/auth/login` / `/logout` / `GET /me` | Admin auth |
| `GET/POST/PUT/DELETE /api/tournaments` | Tournament CRUD |
| `GET/POST/PUT/DELETE /api/teams?tournament_id=` | Team CRUD |
| `GET/POST/PUT/DELETE /api/players?team_id=` | Player CRUD |
| `GET/POST /api/matches`, `POST /api/matches/generate-schedule`, `POST /api/matches/generate-knockout` | Match scheduling |
| `GET/POST /api/results` | Score entry (auto-updates points table) |
| `GET /api/results/winner/:tournament_id` | Declared tournament winner |
| `GET /api/points?tournament_id=` | Points table |

## Switching to MySQL

The schema in `db/index.js` is plain SQL and maps directly onto the MySQL tables from
the original spec (same column names/types). To port it: swap `better-sqlite3` for
`mysql2`, change `AUTOINCREMENT` → `AUTO_INCREMENT`, and rewrite the prepared-statement
calls (`db.prepare(...).get/.run/.all`) to `mysql2` query calls. Everything else — routes,
frontend, business logic — stays the same.

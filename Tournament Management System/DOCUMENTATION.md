# Tournament Management System - Technical Architecture & Developer Guide

> **System Architecture & Developer Reference Manual**
> **Tech Stack**: 100% Pure Python (Streamlit Web UI + SQLite Database + External CSS Design System)

---

## 1. Executive Summary & Architecture Overview

The **Tournament Management System (TMS)** is an enterprise application designed to manage competitive tournaments in two core formats:
1. **Single Elimination (Knockout)**
2. **Round Robin (League)**

### System Architecture Diagram

```
+-----------------------------------------------------------------------+
|                      Streamlit Web Interface (app.py)                 |
|  [Admin Dashboard]    |    [Captain Portal]    |   [Public Viewer]    |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                       Design & Logic Layer                            |
|    - External Design System    (style.css)                            |
|    - Single Elimination Engine (engine_knockout.py)                   |
|    - Round Robin Engine        (engine_round_robin.py)                |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                     Database Abstraction Layer (database.py)          |
|    - Connection Context Manager, SQLite foreign keys, SQL schema      |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                      SQLite File (tournament.db)                      |
+-----------------------------------------------------------------------+
```

---

## 2. File Organization & Separation of Concerns (SoC)

| File Name | Role / Purpose | Architectural Concept |
| :--- | :--- | :--- |
| **[`app.py`](file:///c:/Users/Joydip%20Maiti/Desktop/Tournament%20Management%20System/app.py)** | Application Entry Point & Web UI | Renders multi-role dashboards, tabs, and interactive Streamlit components. |
| **[`style.css`](file:///c:/Users/Joydip%20Maiti/Desktop/Tournament%20Management%20System/style.css)** | External Design System | Implements Glassmorphism, Google Fonts (`Plus Jakarta Sans`), and custom card hover effects. |
| **[`database.py`](file:///c:/Users/Joydip%20Maiti/Desktop/Tournament%20Management%20System/database.py)** | Database Layer | Encapsulates SQLite connection management, table schemas, and SQL queries. |
| **[`engine_knockout.py`](file:///c:/Users/Joydip%20Maiti/Desktop/Tournament%20Management%20System/engine_knockout.py)** | Knockout Bracket Engine | Handles power-of-two padding (BYEs), seed alignment, and winner advancement logic. |
| **[`engine_round_robin.py`](file:///c:/Users/Joydip%20Maiti/Desktop/Tournament%20Management%20System/engine_round_robin.py)** | Round Robin Engine | Computes all-vs-all match fixtures and dynamic standings tables. |

---

## 3. Database Schema (`database.py`)

The system uses a relational **SQLite** database (`tournament.db`). The key tables are:

1. **`tournaments`**: Stores tournament metadata (Format: Knockout/Round Robin, Sport Type, Max Teams, Duration, Status).
2. **`teams`**: Stores Team Name, Captain Name, and Player Roster (stored as a JSON string).
3. **`tournament_participants`**: Junction table mapping teams to tournaments with Seed Numbers.
4. **`matches`**: Fixtures table with scores, team IDs (`team_a_id`, `team_b_id`), `winner_id`, and linked progression pointers (`next_match_id`, `next_match_slot`).
5. **`users`**: Role-based access table for Admin, Captain, and Public Viewer users.

---

## 4. Algorithm & Logic Walkthrough

### A. Single Elimination Knockout Engine (`engine_knockout.py`)

#### 1. Power-of-Two Padding & BYE Allocation
Knockout brackets require a team count equal to a power of $2$ ($2, 4, 8, 16, 32$).
- If $N$ teams register, the engine calculates $P = 2^{\lceil \log_2(N) \rceil}$.
- Number of BYEs = $P - N$.
- Teams with BYEs auto-advance to Round 2 without playing a Round 1 match.

#### 2. Winner Advancement Mathematics
- Match $m$ (0-indexed) in Round $r$ advances to Match $\lfloor m/2 \rfloor$ in Round $r+1$.
- If $m \% 2 == 0$ (Even Index) $\rightarrow$ Winner fills `team_a` slot in next match.
- If $m \% 2 == 1$ (Odd Index) $\rightarrow$ Winner fills `team_b` slot in next match.

```
Round 1 Match 0 (Winner) ---> team_a slot of Round 2 Match 0
Round 1 Match 1 (Winner) ---> team_b slot of Round 2 Match 0
```

---

### B. Round Robin Engine (`engine_round_robin.py`)

#### 1. All-vs-All Fixture Generator
For $N$ teams, total matches generated = $\frac{N(N - 1)}{2}$.
Nested loops pair `team[i]` with `team[j]` where $j > i$ to prevent duplicate reverse fixtures.

#### 2. Standings & Points Calculation Rules
- **Win**: 2 Points
- **Draw / Tie**: 1 Point each
- **Loss**: 0 Points
- **Goal / Score Difference (GD)** = Points Scored - Points Conceded

#### 3. Standings Tie-Breaker Sorting Order
```python
sorted_standings = sorted(
    standings_list,
    key=lambda x: (x['points'], x['gd'], x['scored']),
    reverse=True
)
```
1. Total Points (Highest first)
2. Goal Difference (Tie-breaker 1)
3. Total Points Scored (Tie-breaker 2)

---

## 5. System Implementation Architecture

### File 1: `app.py` & `style.css`
- `load_css("style.css")`: Reads external stylesheet rules and injects them into Streamlit's DOM safely using `st.markdown(..., unsafe_allow_html=True)`.
- `st.set_page_config()`: Sets wide browser layout and tab title.
- `st.session_state`: Stores persistent state across widget reruns.
- `st.tabs()` & `st.columns()`: Renders side-by-side bracket round cards and tabbed navigation.

### File 2: `database.py`
- `get_connection()`: Connects to SQLite and enables `PRAGMA foreign_keys = ON` to enforce relational rules between matches and teams.
- `row_factory = sqlite3.Row`: Allows accessing SQL rows by column name (e.g. `row['name']`) rather than tuple indices.
- `init_db()`: Executes `CREATE TABLE IF NOT EXISTS` statements to construct the schema on startup.

### File 3: `engine_knockout.py`
- `generate_knockout_bracket()`: Builds match placeholders backwards from the Final round to Round 1 so parent match IDs (`next_match_id`) exist when inserting child matches.
- `record_knockout_match_result()`: Saves match score, declares `winner_id`, and immediately executes `update_match_team_slot()` to fill the next round slot.

### File 4: `engine_round_robin.py`
- `calculate_round_robin_standings()`: Queries completed matches, computes `won`, `lost`, `drawn`, `gd`, `points` dynamically, and returns a sorted rank list.

---

## 6. Technical Architecture FAQ

**Q1: Why separate CSS into a dedicated `style.css` file instead of writing inline strings?**
> *Answer*: Moving styles into `style.css` enforces the **Separation of Concerns (SoC)** software engineering design principle. It keeps `app.py` clean and focused strictly on Python backend logic and Streamlit UI layout.

**Q2: Why choose Streamlit instead of React + Node.js?**
> *Answer*: Streamlit allows rapid application development using 100% Python, providing instant interactive UI widgets, live state management, and custom CSS styling without needing an asynchronous JS frontend layer.

**Q3: How does the system handle an odd number of teams in a knockout tournament?**
> *Answer*: The `calculate_next_power_of_two()` function pads the bracket with `None` values (BYEs) to reach the nearest power of 2 (e.g., 5 teams padded to 8). Teams paired against a BYE automatically advance to Round 2.

**Q4: How are knockout match progression links created?**
> *Answer*: When creating matches in `generate_knockout_bracket()`, parent matches in Round $r+1$ are created first. Child matches in Round $r$ store a pointer (`next_match_id`) and slot designation (`team_a` or `team_b`). Updating a score automatically pushes the winner ID into that pointer slot.

**Q5: How does the database prevent orphaned matches if a tournament is deleted?**
> *Answer*: Foreign key constraints are defined with `ON DELETE CASCADE`. Deleting a tournament automatically removes all associated match records and participant entries.

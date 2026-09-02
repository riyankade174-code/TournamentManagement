# ==============================================================================
# DATABASE MODULE (database.py)
# ==============================================================================
# Purpose: Manages all database interactions using Python's built-in SQLite3 library.
# This module handles database creation, table initialization, and CRUD (Create,
# Read, Update, Delete) operations for Tournaments, Teams, Players, and Matches.
#
# Key System Architecture Concepts:
# 1. SQLite: A lightweight, serverless relational database engine stored in a single file.
# 2. Context Manager (`with sqlite3.connect(...)`): Automatically opens and closes 
#    database connections safely, preventing memory leaks or locked databases.
# 3. Foreign Keys: Enforces relational integrity (e.g. a match must belong to a valid tournament).
# ==============================================================================

import sqlite3  # Built-in Python library for SQL relational database management
import json     # Used for storing player list arrays as JSON strings in the database
import os       # Operating system utility to resolve file paths

# Name of the database file stored locally in the project directory
DB_FILE = "tournament.db"

# ------------------------------------------------------------------------------
# CONNECTION HELPER FUNCTION
# ------------------------------------------------------------------------------
def get_connection():
    """
    Establishes and returns a connection to the SQLite database.
    Enables Row factory so query results can be accessed like dictionaries (e.g. row['name']).
    Enables Foreign Key constraint enforcement.
    """
    # Connect to the SQLite database file (creates the file if it does not exist yet)
    conn = sqlite3.connect(DB_FILE)
    
    # Configure row_factory to return Dictionary-like objects instead of raw tuples
    # Example: row['name'] instead of row[1]
    conn.row_factory = sqlite3.Row
    
    # SQLite has foreign key constraints disabled by default for backward compatibility;
    # PRAGMA foreign_keys = ON explicitly enables integrity checks between tables.
    conn.execute("PRAGMA foreign_keys = ON;")
    
    return conn

# ------------------------------------------------------------------------------
# DATABASE INITIALIZATION FUNCTION
# ------------------------------------------------------------------------------
def init_db():
    """
    Creates all required SQL tables if they do not already exist.
    This function is called when the application starts up.
    """
    # Using 'with get_connection()' ensures the connection is automatically committed and closed
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. TOURNAMENTS TABLE
        # Stores tournament configuration parameters
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tournaments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sport_type TEXT NOT NULL,
                format TEXT NOT NULL CHECK(format IN ('Knockout', 'Round Robin')),
                max_teams INTEGER NOT NULL,
                match_duration INTEGER NOT NULL DEFAULT 60, -- duration in minutes
                venue TEXT DEFAULT 'Main Campus Arena',
                start_date TEXT DEFAULT '2026-09-15',
                status TEXT NOT NULL DEFAULT 'Upcoming' CHECK(status IN ('Upcoming', 'Ongoing', 'Completed')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Schema migration fallback for existing SQLite database files
        try:
            cursor.execute("ALTER TABLE tournaments ADD COLUMN venue TEXT DEFAULT 'Main Campus Arena'")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE tournaments ADD COLUMN start_date TEXT DEFAULT '2026-09-15'")
        except sqlite3.OperationalError:
            pass
        
        # 2. TEAMS TABLE
        # Stores team details and roster array (as JSON text)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                captain_name TEXT NOT NULL,
                roster TEXT NOT NULL -- Stored as JSON string list of player names, e.g. ["John", "Alex"]
            );
        """)
        
        # 3. TOURNAMENT PARTICIPANTS TABLE
        # Junction table mapping Teams to Tournaments with Seeding order
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tournament_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,
                seed_number INTEGER NOT NULL,
                FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE,
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
                UNIQUE(tournament_id, team_id)
            );
        """)
        
        # 4. MATCHES TABLE
        # Stores all fixture details, scores, statuses, and progression pointers for knockout brackets
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,      -- e.g., Round 1, Round 2 (Semi-Final), Round 3 (Final)
                match_number INTEGER NOT NULL,      -- Match order within the round
                team_a_id INTEGER,                  -- ID of first team (nullable before round proceeds)
                team_b_id INTEGER,                  -- ID of second team (nullable before round proceeds)
                score_a INTEGER DEFAULT 0,          -- Score scored by Team A
                score_b INTEGER DEFAULT 0,          -- Score scored by Team B
                winner_id INTEGER,                  -- Winner team ID once match completes
                next_match_id INTEGER,              -- Pointer to parent match in next round for Knockout
                next_match_slot TEXT CHECK(next_match_slot IN ('team_a', 'team_b')), -- Slot filled in next match
                status TEXT NOT NULL DEFAULT 'Scheduled' CHECK(status IN ('Scheduled', 'Ongoing', 'Completed')),
                FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE,
                FOREIGN KEY (team_a_id) REFERENCES teams(id),
                FOREIGN KEY (team_b_id) REFERENCES teams(id),
                FOREIGN KEY (winner_id) REFERENCES teams(id),
                FOREIGN KEY (next_match_id) REFERENCES matches(id)
            );
        """)
        
        # 5. USERS TABLE
        # Simple authentication table supporting Admin, Captain, and Viewer roles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('Admin', 'Captain', 'Viewer')),
                team_id INTEGER,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            );
        """)
        
        # Create a default Admin user if none exists
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            # Insert default admin account (Username: admin | Password: admin123)
            cursor.execute("""
                INSERT INTO users (username, password, role) 
                VALUES ('admin', 'admin123', 'Admin');
            """)

# ------------------------------------------------------------------------------
# TOURNAMENT CRUD OPERATIONS
# ------------------------------------------------------------------------------
def create_tournament(name, sport_type, format_type, max_teams, match_duration, venue="Main Campus Arena", start_date="2026-09-15"):
    """Inserts a new tournament entry into the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tournaments (name, sport_type, format, max_teams, match_duration, venue, start_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, sport_type, format_type, max_teams, match_duration, venue, start_date))
        return cursor.lastrowid # Returns the newly created auto-incremented tournament ID

def get_all_tournaments():
    """Retrieves all tournaments ordered by creation date descending as plain dicts."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tournaments ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]

def get_tournament_by_id(tournament_id):
    """Retrieves a single tournament by its primary key ID as a plain dict."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tournaments WHERE id = ?", (tournament_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_tournament_status(tournament_id, status):
    """Updates status ('Upcoming', 'Ongoing', 'Completed') of a tournament."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tournaments SET status = ? WHERE id = ?", (status, tournament_id))

# ------------------------------------------------------------------------------
# TEAM & PARTICIPANT CRUD OPERATIONS
# ------------------------------------------------------------------------------
def create_team(name, captain_name, roster_list):
    """
    Creates a new team record or returns existing team ID if team name already exists.
    Converts roster Python list to JSON string.
    """
    roster_json = json.dumps(roster_list) # Convert list e.g. ["P1", "P2"] -> '["P1", "P2"]'
    with get_connection() as conn:
        cursor = conn.cursor()
        # Check if team with this name already exists in database
        cursor.execute("SELECT id FROM teams WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return row['id']
            
        try:
            cursor.execute("""
                INSERT INTO teams (name, captain_name, roster)
                VALUES (?, ?, ?)
            """, (name, captain_name, roster_json))
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            cursor.execute("SELECT id FROM teams WHERE name = ?", (name,))
            existing = cursor.fetchone()
            if existing:
                return existing['id']
            raise

def get_all_teams():
    """Retrieves all registered teams as plain dicts."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM teams ORDER BY name ASC")
        return [dict(row) for row in cursor.fetchall()]

def register_team_for_tournament(tournament_id, team_id, seed_number):
    """Links a team to a tournament with a designated seed number (ignores duplicates)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO tournament_participants (tournament_id, team_id, seed_number)
            VALUES (?, ?, ?)
        """, (tournament_id, team_id, seed_number))

def get_tournament_teams(tournament_id):
    """Retrieves all registered teams for a specific tournament sorted by seed as plain dicts."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.name, t.captain_name, t.roster, tp.seed_number
            FROM teams t
            JOIN tournament_participants tp ON t.id = tp.team_id
            WHERE tp.tournament_id = ?
            ORDER BY tp.seed_number ASC
        """, (tournament_id,))
        return [dict(row) for row in cursor.fetchall()]

# ------------------------------------------------------------------------------
# MATCH CRUD OPERATIONS
# ------------------------------------------------------------------------------
def get_tournament_matches(tournament_id):
    """Retrieves all matches for a tournament enriched with team names as plain dicts."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.*, 
                   ta.name AS team_a_name, 
                   tb.name AS team_b_name,
                   tw.name AS winner_name
            FROM matches m
            LEFT JOIN teams ta ON m.team_a_id = ta.id
            LEFT JOIN teams tb ON m.team_b_id = tb.id
            LEFT JOIN teams tw ON m.winner_id = tw.id
            WHERE m.tournament_id = ?
            ORDER BY m.round_number ASC, m.match_number ASC
        """, (tournament_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_match_by_id(match_id):
    """Retrieves details of a specific match as a plain dict."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM matches WHERE id = ?", (match_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_match_score(match_id, score_a, score_b, winner_id, status='Completed'):
    """Updates match score, sets winner, and marks status as Completed."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE matches 
            SET score_a = ?, score_b = ?, winner_id = ?, status = ?
            WHERE id = ?
        """, (score_a, score_b, winner_id, status, match_id))

def update_match_team_slot(match_id, slot, team_id):
    """Dynamically fills team_a_id or team_b_id for a match in subsequent knockout rounds."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if slot == 'team_a':
            cursor.execute("UPDATE matches SET team_a_id = ? WHERE id = ?", (team_id, match_id))
        elif slot == 'team_b':
            cursor.execute("UPDATE matches SET team_b_id = ? WHERE id = ?", (team_id, match_id))

# ------------------------------------------------------------------------------
# TOURNAMENT DELETION & RESET OPERATIONS
# ------------------------------------------------------------------------------
def delete_tournament(tournament_id):
    """Deletes a tournament and cascades deletion to all matches and participant entries."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tournaments WHERE id = ?", (tournament_id,))
        cursor.execute("SELECT COUNT(*) FROM tournaments")
        cnt = cursor.fetchone()[0]
        if cnt == 0:
            cursor.execute("DELETE FROM teams")
            cursor.execute("DELETE FROM sqlite_sequence")

def reset_tournament_matches(tournament_id):
    """Resets all scores, winners, and match statuses back to Scheduled."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE matches 
            SET score_a = 0, score_b = 0, winner_id = NULL, status = 'Scheduled'
            WHERE tournament_id = ?
        """, (tournament_id,))
        # Reset parent match slots for Round > 1 in knockout brackets
        cursor.execute("""
            UPDATE matches 
            SET team_a_id = NULL, team_b_id = NULL
            WHERE tournament_id = ? AND round_number > 1
        """, (tournament_id,))
        cursor.execute("UPDATE tournaments SET status = 'Ongoing' WHERE id = ?", (tournament_id,))

def delete_all_tournaments():
    """Wipes all tournaments and resets SQLite AUTOINCREMENT ID sequence back to 1."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tournaments")
        cursor.execute("DELETE FROM teams")
        cursor.execute("DELETE FROM sqlite_sequence")

# Initialize database tables immediately when database.py is loaded/imported
if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")

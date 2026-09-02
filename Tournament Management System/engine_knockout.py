# ==============================================================================
# KNOCKOUT BRACKET ENGINE (engine_knockout.py)
# ==============================================================================
# Purpose: Handles Single Elimination (Knockout) tournament logic:
# 1. Automated binary tree bracket generation based on registered teams and seeding.
# 2. Power-of-Two bracket padding & Bye allocation.
# 3. Winner Advancement Engine: when a match score is recorded, the winning team
#    is automatically pushed into the correct team slot of the next round's match.
#
# Algorithmic & Mathematical Architecture:
# - Binary Tree Structure: A knockout tournament with P teams (where P is a power of 2)
#   requires P - 1 total matches across log2(P) rounds.
# - Parent Node Indexing: Match m (0-indexed) in Round r advances to Match floor(m/2) in Round r+1.
#   - Even index (0, 2, 4...) -> Fills 'team_a' slot in parent match.
#   - Odd index  (1, 3, 5...) -> Fills 'team_b' slot in parent match.
# ==============================================================================

import math
from database import get_connection, update_match_score, update_match_team_slot, get_match_by_id

def calculate_next_power_of_two(n):
    """
    Calculates the smallest power of 2 that is greater than or equal to n.
    Example:
      If n = 5 -> next power of 2 is 8 (byes = 3)
      If n = 8 -> next power of 2 is 8 (byes = 0)
    """
    if n <= 1:
        return 2
    return 2 ** math.ceil(math.log2(n))

def generate_knockout_bracket(tournament_id, teams_list):
    """
    Generates all round fixtures and links parent-child matches for knockout progression.
    
    Parameters:
      - tournament_id: ID of the tournament being started.
      - teams_list: List of team dictionary objects sorted by seed number.
    """
    num_teams = len(teams_list)
    if num_teams < 2:
        raise ValueError("At least 2 teams are required to generate a knockout bracket.")

    # 1. Determine Bracket Size & Total Rounds
    bracket_size = calculate_next_power_of_two(num_teams)  # e.g., 8 for 5 to 8 teams
    total_rounds = int(math.log2(bracket_size))             # e.g., log2(8) = 3 rounds

    # 2. Prepare Seeding with BYEs
    # Byes are added to fill the bracket to the nearest power of 2
    # Standard seeding pairs top seeds against lowest seeds: (Seed 1 vs Bye/Lowest Seed)
    seeded_teams = list(teams_list)
    byes_needed = bracket_size - num_teams
    for _ in range(byes_needed):
        seeded_teams.append(None)  # None represents a BYE (auto-advancement)

    with get_connection() as conn:
        cursor = conn.cursor()
        
        # We will keep a dictionary mapping (round_number, match_number) -> match_id
        # to connect round r matches to round r+1 parent matches.
        round_matches_map = {}

        # ----------------------------------------------------------------------
        # STEP A: Create Match Placeholders for ALL Rounds (From Final back to Round 1)
        # ----------------------------------------------------------------------
        # Creating matches backwards allows us to establish next_match_id pointers!
        for r in range(total_rounds, 0, -1):
            matches_in_round = 2 ** (total_rounds - r) # Round 3 (Final): 1 match, Round 2: 2, Round 1: 4
            
            for m in range(matches_in_round):
                next_match_id = None
                next_match_slot = None
                
                # If not the Final round, link to the parent match in round r+1
                if r < total_rounds:
                    parent_match_number = m // 2
                    next_match_id = round_matches_map[(r + 1, parent_match_number)]
                    next_match_slot = 'team_a' if (m % 2 == 0) else 'team_b'

                cursor.execute("""
                    INSERT INTO matches (tournament_id, round_number, match_number, next_match_id, next_match_slot, status)
                    VALUES (?, ?, ?, ?, ?, 'Scheduled')
                """, (tournament_id, r, m, next_match_id, next_match_slot))
                
                match_id = cursor.lastrowid
                round_matches_map[(r, m)] = match_id

        # ----------------------------------------------------------------------
        # STEP B: Assign Seeded Teams to Round 1 Matches
        # ----------------------------------------------------------------------
        num_round1_matches = bracket_size // 2
        for m in range(num_round1_matches):
            team_a = seeded_teams[m]
            team_b = seeded_teams[bracket_size - 1 - m] # Classic 1 vs 8, 2 vs 7 seeding rule

            team_a_id = team_a['id'] if team_a else None
            team_b_id = team_b['id'] if team_b else None
            
            match_id = round_matches_map[(1, m)]

            # Check for BYE scenario: If one team is None, the other team auto-advances
            if team_a_id is not None and team_b_id is None:
                # Team A auto-advances because Team B is BYE
                cursor.execute("""
                    UPDATE matches 
                    SET team_a_id = ?, team_b_id = NULL, winner_id = ?, status = 'Completed'
                    WHERE id = ?
                """, (team_a_id, team_a_id, match_id))
                
                # Instantly advance winner to next match if pointer exists
                _advance_winner_to_next_round(cursor, match_id, team_a_id)

            elif team_a_id is None and team_b_id is not None:
                # Team B auto-advances because Team A is BYE
                cursor.execute("""
                    UPDATE matches 
                    SET team_a_id = NULL, team_b_id = ?, winner_id = ?, status = 'Completed'
                    WHERE id = ?
                """, (team_b_id, team_b_id, match_id))
                
                _advance_winner_to_next_round(cursor, match_id, team_b_id)

            else:
                # Normal match between two real teams
                cursor.execute("""
                    UPDATE matches 
                    SET team_a_id = ?, team_b_id = ?
                    WHERE id = ?
                """, (team_a_id, team_b_id, match_id))

        # Update tournament status to 'Ongoing'
        cursor.execute("UPDATE tournaments SET status = 'Ongoing' WHERE id = ?", (tournament_id,))

def record_knockout_match_result(match_id, score_a, score_b, winner_id=None):
    """
    Records score for a match, declares the winner, and advances winner to next round slot.
    If score_a == score_b, an explicit winner_id (Overtime/Shootout winner) must be specified.
    """
    match = get_match_by_id(match_id)
    if not match:
        raise ValueError("Match not found.")
    
    if not match['team_a_id'] or not match['team_b_id']:
        raise ValueError("Both teams must be assigned before recording a result.")

    if score_a == score_b:
        if not winner_id:
            raise ValueError("Knockout matches ending in a draw require selecting an Overtime/Shootout Winner.")
    else:
        # Determine winner team ID based on points
        winner_id = match['team_a_id'] if score_a > score_b else match['team_b_id']

    # Update database record for current match
    update_match_score(match_id, score_a, score_b, winner_id, status='Completed')

    # Automatically push winner into next match if next_match_id exists
    if match['next_match_id'] and match['next_match_slot']:
        update_match_team_slot(match['next_match_id'], match['next_match_slot'], winner_id)

    # Check if this was the Final match (Round with highest number or no next_match_id)
    if not match['next_match_id']:
        with get_connection() as conn:
            conn.execute("UPDATE tournaments SET status = 'Completed' WHERE id = ?", (match['tournament_id'],))

def _advance_winner_to_next_round(cursor, match_id, winner_id):
    """Internal helper to push winner into parent match during bracket initialization BYE auto-advancement."""
    cursor.execute("SELECT next_match_id, next_match_slot FROM matches WHERE id = ?", (match_id,))
    row = cursor.fetchone()
    if row and row['next_match_id'] and row['next_match_slot']:
        if row['next_match_slot'] == 'team_a':
            cursor.execute("UPDATE matches SET team_a_id = ? WHERE id = ?", (winner_id, row['next_match_id']))
        else:
            cursor.execute("UPDATE matches SET team_b_id = ? WHERE id = ?", (winner_id, row['next_match_id']))

def simulate_random_match(match_id):
    """Simulates realistic non-tied scores for a single knockout match and advances the winner."""
    import random
    match = get_match_by_id(match_id)
    if not match or not match['team_a_id'] or not match['team_b_id'] or match['status'] == 'Completed':
        return
    
    score_a = random.randint(1, 13)
    score_b = random.randint(1, 13)
    while score_a == score_b:
        score_b = random.randint(1, 13)
        
    record_knockout_match_result(match_id, score_a, score_b)

def simulate_entire_round(tournament_id, round_number):
    """Simulates all playable matches in a specific round of a knockout tournament."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM matches 
            WHERE tournament_id = ? AND round_number = ? AND status != 'Completed'
            AND team_a_id IS NOT NULL AND team_b_id IS NOT NULL
        """, (tournament_id, round_number))
        rows = cursor.fetchall()
        for r in rows:
            simulate_random_match(r['id'])

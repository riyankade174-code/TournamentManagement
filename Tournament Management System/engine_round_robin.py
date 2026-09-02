# ==============================================================================
# ROUND ROBIN ENGINE (engine_round_robin.py)
# ==============================================================================
# Purpose: Handles League / Round Robin tournament operations:
# 1. Automated Schedule Generation: Every team plays against every other team once.
# 2. Dynamic Points Table / Standings Computation:
#    - Matches Played (P)
#    - Won (W), Lost (L), Drawn (D)
#    - Goal/Score Difference (GD = Scored - Conceded)
#    - Total Points (Win = 2 pts, Draw = 1 pt, Loss = 0 pts)
# 3. Automatic Ranking & Qualification for top teams entering knockout playoffs.
# ==============================================================================

from database import get_connection, update_match_score, get_tournament_teams

def generate_round_robin_schedule(tournament_id, teams_list):
    """
    Generates round robin fixtures so every team plays every other team exactly once.
    
    Formula for Total Matches in Round Robin:
      Total Matches = N * (N - 1) / 2
      For example: 4 teams -> 4 * 3 / 2 = 6 matches total.
    """
    num_teams = len(teams_list)
    if num_teams < 2:
        raise ValueError("At least 2 teams are required for a Round Robin tournament.")

    with get_connection() as conn:
        cursor = conn.cursor()
        
        match_no = 1
        # Double nested loop pairing team_i with team_j (where j > i to avoid duplicate reverse fixtures)
        for i in range(num_teams):
            for j in range(i + 1, num_teams):
                team_a = teams_list[i]
                team_b = teams_list[j]
                
                # Round number can be assigned chronologically or sequentially
                cursor.execute("""
                    INSERT INTO matches (tournament_id, round_number, match_number, team_a_id, team_b_id, status)
                    VALUES (?, ?, ?, ?, ?, 'Scheduled')
                """, (tournament_id, 1, match_no, team_a['id'], team_b['id']))
                
                match_no += 1

        # Mark tournament status as Ongoing
        cursor.execute("UPDATE tournaments SET status = 'Ongoing' WHERE id = ?", (tournament_id,))

def record_round_robin_match_result(match_id, score_a, score_b):
    """
    Records score for a Round Robin match. Draws are allowed in league format!
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM matches WHERE id = ?", (match_id,))
        match = cursor.fetchone()
        
        if not match:
            raise ValueError("Match not found.")

        # Determine winner ID (None if drawn/tied)
        winner_id = None
        if score_a > score_b:
            winner_id = match['team_a_id']
        elif score_b > score_a:
            winner_id = match['team_b_id']
            
        update_match_score(match_id, score_a, score_b, winner_id, status='Completed')

def calculate_round_robin_standings(tournament_id):
    """
    Calculates dynamic points table for a Round Robin tournament.
    
    Returns a sorted list of dictionaries with stats for each team:
    - rank, team_id, team_name, played, won, lost, drawn, scored, conceded, gd, points
    """
    teams = get_tournament_teams(tournament_id)
    
    # Initialize standings dictionary for every team
    standings_dict = {}
    for team in teams:
        standings_dict[team['id']] = {
            'team_id': team['id'],
            'team_name': team['name'],
            'played': 0,
            'won': 0,
            'lost': 0,
            'drawn': 0,
            'scored': 0,
            'conceded': 0,
            'gd': 0,
            'points': 0
        }
        
    # Fetch all completed matches for this tournament
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM matches 
            WHERE tournament_id = ? AND status = 'Completed'
        """, (tournament_id,))
        completed_matches = cursor.fetchall()

    # Iterate over completed matches and accumulate statistics
    for match in completed_matches:
        t_a = match['team_a_id']
        t_b = match['team_b_id']
        s_a = match['score_a']
        s_b = match['score_b']

        # Skip if either team is invalid (e.g. BYE match)
        if not t_a or not t_b or t_a not in standings_dict or t_b not in standings_dict:
            continue

        # Increment Played count
        standings_dict[t_a]['played'] += 1
        standings_dict[t_b]['played'] += 1

        # Accumulate scored and conceded points/goals
        standings_dict[t_a]['scored'] += s_a
        standings_dict[t_a]['conceded'] += s_b
        
        standings_dict[t_b]['scored'] += s_b
        standings_dict[t_b]['conceded'] += s_a

        # Evaluate match outcome
        if s_a > s_b:
            # Team A Win (2 Points), Team B Loss (0 Points)
            standings_dict[t_a]['won'] += 1
            standings_dict[t_a]['points'] += 2
            standings_dict[t_b]['lost'] += 1
        elif s_b > s_a:
            # Team B Win (2 Points), Team A Loss (0 Points)
            standings_dict[t_b]['won'] += 1
            standings_dict[t_b]['points'] += 2
            standings_dict[t_a]['lost'] += 1
        else:
            # Draw / Tie (1 Point each)
            standings_dict[t_a]['drawn'] += 1
            standings_dict[t_a]['points'] += 1
            standings_dict[t_b]['drawn'] += 1
            standings_dict[t_b]['points'] += 1

    # Calculate Goal Difference (GD = Scored - Conceded)
    standings_list = list(standings_dict.values())
    for item in standings_list:
        item['gd'] = item['scored'] - item['conceded']

    # Sort teams by:
    # 1. Total Points descending
    # 2. Goal Difference descending (tie-breaker 1)
    # 3. Scored Points descending (tie-breaker 2)
    sorted_standings = sorted(
        standings_list,
        key=lambda x: (x['points'], x['gd'], x['scored']),
        reverse=True
    )

    # Assign 1-indexed Ranks
    for idx, item in enumerate(sorted_standings):
        item['rank'] = idx + 1

    return sorted_standings

def simulate_random_match(match_id):
    """Simulates realistic scores for a single Round Robin match (allows draws)."""
    import random
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM matches WHERE id = ?", (match_id,))
        match = cursor.fetchone()
        if not match or match['status'] == 'Completed':
            return
        
        score_a = random.randint(0, 5)
        score_b = random.randint(0, 5)
        record_round_robin_match_result(match_id, score_a, score_b)

def simulate_all_matches(tournament_id):
    """Simulates all remaining scheduled matches in a Round Robin tournament."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM matches 
            WHERE tournament_id = ? AND status != 'Completed'
        """, (tournament_id,))
        rows = cursor.fetchall()
        for r in rows:
            simulate_random_match(r['id'])

# ==============================================================================
# MAIN STREAMLIT APPLICATION (app.py) - ENTERPRISE EDITION
# ==============================================================================
# Purpose: State-of-the-Art Tournament Management System built entirely in 100% Pure Python!
# Features a crisp Light Premium Design System, Top Role Quick-Switcher Pills Bar,
# 1-Click Team Captain Quick-Join Portal, Preset Tournament Generators, and Report Exporter.
# ==============================================================================

import streamlit as st  # Core web application framework for Python
import os               # Operating system module to handle file loading
import json
import database as db
import engine_knockout as knockout
import engine_round_robin as round_robin

# ------------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & METADATA
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Tournament Hub Pro | Management System",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database schema on app startup
db.init_db()

# Pre-populate default global teams if database has none
def ensure_default_global_teams():
    existing = db.get_all_teams()
    if not existing:
        sample_teams = [
            ("Shadow Strikers", "John Doe", ["Player A", "Player B", "Player C"]),
            ("Cyber Knights", "Sarah Jenkins", ["Sarah J.", "Emma W.", "Lucas G."]),
            ("Apex Predators", "Alex Mercer", ["Alex M.", "Ryan K.", "David L."]),
            ("Titan Warriors", "James Wilson", ["James W.", "Chris B.", "Ethan H."]),
            ("Phoenix Rising", "Elena Rostova", ["Elena R.", "Sasha N.", "Viktor V."]),
            ("Vanguard Esports", "Michael Chen", ["Michael C.", "Daniel R.", "Kevin P."]),
            ("Quantum XI", "Liam O'Connor", ["Liam O.", "Noah S.", "Oliver T."]),
            ("Thunderbolts", "Marcus Vance", ["Marcus V.", "Leo D.", "Gabriel F."])
        ]
        for t_name, c_name, roster in sample_teams:
            db.create_team(t_name, c_name, roster)

ensure_default_global_teams()

# ------------------------------------------------------------------------------
# 2. EXTERNAL LIGHT CSS DESIGN SYSTEM LOADER
# ------------------------------------------------------------------------------
def load_css(css_file="style.css"):
    """Reads and injects external CSS stylesheet into Streamlit DOM."""
    if os.path.exists(css_file):
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ------------------------------------------------------------------------------
# 3. SESSION STATE INITIALIZATION
# ------------------------------------------------------------------------------
if "current_role" not in st.session_state:
    st.session_state["current_role"] = "Public Viewer"

# Preset 1: 8-Team Esports Knockout Championship
def seed_sample_esports_knockout():
    t_title = f"🎮 Valorant Champions Cup 2026"
    t_id = db.create_tournament(t_title, "Esports (Valorant)", "Knockout", 8, 45)
    sample_teams = [
        ("Apex Predators", "Alex Mercer", ["Alex M.", "Ryan K.", "David L."]),
        ("Cyber Knights", "Sarah Jenkins", ["Sarah J.", "Emma W.", "Lucas G."]),
        ("Vanguard Esports", "Michael Chen", ["Michael C.", "Daniel R.", "Kevin P."]),
        ("Shadow Ninjas", "Priya Sharma", ["Priya S.", "Rohan M.", "Anish K."]),
        ("Titan Warriors", "James Wilson", ["James W.", "Chris B.", "Ethan H."]),
        ("Phoenix Rising", "Elena Rostova", ["Elena R.", "Sasha N.", "Viktor V."]),
        ("Quantum XI", "Liam O'Connor", ["Liam O.", "Noah S.", "Oliver T."]),
        ("Thunderbolts", "Marcus Vance", ["Marcus V.", "Leo D.", "Gabriel F."])
    ]
    for seed, (t_name, cap_name, roster) in enumerate(sample_teams, 1):
        team_id = db.create_team(t_name, cap_name, roster)
        db.register_team_for_tournament(t_id, team_id, seed)
    teams = db.get_tournament_teams(t_id)
    knockout.generate_knockout_bracket(t_id, teams)

# Preset 2: 4-Team Premier Football League
def seed_sample_football_league():
    t_title = f"⚽ Premier Campus League 2026"
    t_id = db.create_tournament(t_title, "Football", "Round Robin", 4, 90)
    sample_teams = [
        ("Shadow Strikers", "John Doe", ["Player A", "Player B", "Player C"]),
        ("Cyber Knights", "Sarah Jenkins", ["Sarah J.", "Emma W.", "Lucas G."]),
        ("Apex Predators", "Alex Mercer", ["Alex M.", "Ryan K.", "David L."]),
        ("Titan Warriors", "James Wilson", ["James W.", "Chris B.", "Ethan H."])
    ]
    for seed, (t_name, cap_name, roster) in enumerate(sample_teams, 1):
        team_id = db.create_team(t_name, cap_name, roster)
        db.register_team_for_tournament(t_id, team_id, seed)
    teams = db.get_tournament_teams(t_id)
    round_robin.generate_round_robin_schedule(t_id, teams)

# Preset 3: 4-Team Chess Masters Knockout
def seed_sample_chess_knockout():
    t_title = f"♟️ Grandmaster Chess Masters 2026"
    t_id = db.create_tournament(t_title, "Chess", "Knockout", 4, 30)
    sample_teams = [
        ("Grandmaster Knights", "Magnus C.", ["Magnus C."]),
        ("Queen Gambit XI", "Beth Harmon", ["Beth H."]),
        ("Rook Tacticians", "Hikaru N.", ["Hikaru N."]),
        ("Bishop Strategists", "Fabiano C.", ["Fabiano C."])
    ]
    for seed, (t_name, cap_name, roster) in enumerate(sample_teams, 1):
        team_id = db.create_team(t_name, cap_name, roster)
        db.register_team_for_tournament(t_id, team_id, seed)
    teams = db.get_tournament_teams(t_id)
    knockout.generate_knockout_bracket(t_id, teams)

# Helper function to format downloadable text summary report
def generate_tournament_report(tournament, matches, teams):
    report = f"=====================================================\n"
    report += f" OFFICIAL TOURNAMENT REPORT: {tournament['name']}\n"
    report += f"=====================================================\n"
    report += f"Format: {tournament['format']} | Sport: {tournament['sport_type']}\n"
    report += f"Status: {tournament['status']} | Max Teams: {tournament['max_teams']}\n\n"
    report += f"--- REGISTERED TEAMS & SEEDS ---\n"
    for t in teams:
        report += f"Seed #{t['seed_number']}: {t['name']} (Captain: {t['captain_name']})\n"
    report += f"\n--- MATCH RESULTS & FIXTURES ---\n"
    for m in matches:
        t_a = m['team_a_name'] if m['team_a_name'] else "TBD"
        t_b = m['team_b_name'] if m['team_b_name'] else "TBD"
        winner = m['winner_name'] if m['winner_name'] else "N/A"
        report += f"Round {m['round_number']} Match #{m['id']}: {t_a} ({m['score_a']}) vs ({m['score_b']}) {t_b} => Winner: {winner} [{m['status']}]\n"
    return report

# ------------------------------------------------------------------------------
# 4. SIDEBAR - CONTROL CENTER & TOURNAMENT SELECTOR
# ------------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/isometric/120/trophy.png", width=75)
    st.title("TMS Control Hub")
    st.caption("Tournament Management System v2.0")
    st.markdown("---")

    # Tournament Selector
    tournaments = db.get_all_tournaments()
    selected_tournament = None
    
    if tournaments:
        tournament_names = [f"#{t['id']} - {t['name']}" for t in tournaments]
        selected_tourn_idx = st.selectbox(
            "🏟️ Select Active Tournament:", 
            range(len(tournaments)), 
            format_func=lambda i: tournament_names[i]
        )
        selected_tournament = tournaments[selected_tourn_idx]
    else:
        st.warning("No active tournaments.")
        
    st.markdown("---")
    
    # Active Role Sidebar Widget
    st.markdown(f"""
        <div class="sidebar-card">
            <div class="sidebar-card-label">Active Perspective</div>
            <div class="sidebar-card-value">{st.session_state['current_role']}</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Admin / Organizer Only Control Tools
    if st.session_state["current_role"] == "Admin / Organizer":
        st.subheader("⚡ Sample Tournament Generators")
        st.caption("Generate pre-configured tournament presets:")
        
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            if st.button("🎮 Valorant", use_container_width=True):
                seed_sample_esports_knockout()
                st.success("Generated Valorant Knockout!")
                st.rerun()
            if st.button("♟️ Chess", use_container_width=True):
                seed_sample_chess_knockout()
                st.success("Generated Chess Masters!")
                st.rerun()
                
        with p_col2:
            if st.button("⚽ Football", use_container_width=True):
                seed_sample_football_league()
                st.success("Generated Football League!")
                st.rerun()

        st.markdown("---")

        # Tournament Cleanup Controls
        with st.expander("⚙️ Tournament Cleanup Controls"):
            if selected_tournament:
                if st.button(f"🗑️ Delete #{selected_tournament['id']}", use_container_width=True):
                    db.delete_tournament(selected_tournament['id'])
                    st.success("Tournament deleted!")
                    st.rerun()

                if st.button("🔄 Reset Match Scores", use_container_width=True):
                    db.reset_tournament_matches(selected_tournament['id'])
                    st.success("Match scores reset back to Scheduled!")
                    st.rerun()

            if st.button("🧹 Clear ALL Tournaments", use_container_width=True):
                db.delete_all_tournaments()
                st.success("All tournaments cleared from database!")
                st.rerun()

    st.markdown("---")
    with st.expander("❓ System User Guide"):
        st.markdown("""
            **How the 3 Perspectives Work:**
            - **🌐 Public Spectator**: View live brackets, schedule, team rosters, top performer analytics, & download official summary reports.
            - **🛡️ Team Captain**: Select announced upcoming tournaments & register your team/roster in 1 click.
            - **🛠️ Organizer**: Create competitions, assign seeds, & enter live match scores with dynamic winner advancement.
        """)

# ------------------------------------------------------------------------------
# 5. MAIN CONTENT DASHBOARD & TOP ROLE QUICK-SWITCHER PILLS
# ------------------------------------------------------------------------------

# Top Header Banner - Light Premium Card
st.markdown("""
    <div class="header-banner">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 style="margin:0; font-size: 32px; font-weight: 800; background: linear-gradient(90deg, #1e40af, #6d28d9); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    TOURNAMENT MANAGEMENT SYSTEM
                </h1>
                <p style="margin: 4px 0 0 0; color: #475569; font-size: 14px; font-weight: 600;">
                    Automated Bracket Engine • Dynamic Standings • Multi-Role Access Control
                </p>
            </div>
            <div>
                <span class="badge badge-knockout" style="font-size: 12px; padding: 6px 14px;">ENTERPRISE SYSTEM</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Top Horizontal Role Switcher Pills Bar
st.markdown("#### 👤 Switch User Perspective / Mode:")
r_col1, r_col2, r_col3 = st.columns(3)

with r_col1:
    btn_type = "primary" if st.session_state["current_role"] == "Public Viewer" else "secondary"
    if st.button("🌐 Public Spectator View", type=btn_type, use_container_width=True):
        st.session_state["current_role"] = "Public Viewer"
        st.rerun()

with r_col2:
    btn_type = "primary" if st.session_state["current_role"] == "Admin / Organizer" else "secondary"
    if st.button("🛠️ Organizer Controller", type=btn_type, use_container_width=True):
        st.session_state["current_role"] = "Admin / Organizer"
        st.rerun()

with r_col3:
    btn_type = "primary" if st.session_state["current_role"] == "Team Captain" else "secondary"
    if st.button("🛡️ Team Captain Portal", type=btn_type, use_container_width=True):
        st.session_state["current_role"] = "Team Captain"
        st.rerun()

st.markdown("<hr style='margin: 15px 0 25px 0; border-color: #e2e8f0;'/>", unsafe_allow_html=True)

# ==============================================================================
# VIEW 1: PUBLIC VIEWER PORTAL
# ==============================================================================
if st.session_state["current_role"] == "Public Viewer":
    st.subheader("🌐 Public Spectator Dashboard")
    
    if not selected_tournament:
        st.info("No tournament selected. Use the sidebar or Admin panel to create a tournament.")
    else:
        # Key Metadata Metrics Banner
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        
        format_badge = "badge-knockout" if selected_tournament['format'] == "Knockout" else "badge-league"
        status_badge = "badge-ongoing" if selected_tournament['status'] == "Ongoing" else ("badge-completed" if selected_tournament['status'] == "Completed" else "badge-league")
        
        venue_str = selected_tournament.get('venue', 'Main Campus Arena')
        start_date_str = selected_tournament.get('start_date', '2026-09-15')
        
        with m_col1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Format & Sport</div>
                    <div class="metric-value" style="font-size: 16px; margin-top:5px;">
                        <strong>{selected_tournament['sport_type']}</strong><br/>
                        <span class="badge {format_badge}" style="font-size:11px;">{selected_tournament['format']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        with m_col2:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Status</div>
                    <div class="metric-value" style="font-size: 18px; margin-top:5px;">
                        <span class="badge {status_badge}">{selected_tournament['status']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        with m_col3:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Venue & Date</div>
                    <div class="metric-value" style="font-size: 13px; color:#1e293b; font-weight:700;">
                        📍 {venue_str}<br/>
                        📅 {start_date_str}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        with m_col4:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Max Capacity</div>
                    <div class="metric-value" style="color:#1e293b;">{selected_tournament['max_teams']} Teams</div>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br/>", unsafe_allow_html=True)
        
        # Tournament Competition Progress Gauge Bar
        matches_all = db.get_tournament_matches(selected_tournament['id'])
        if matches_all:
            completed_cnt = sum(1 for m in matches_all if m['status'] == 'Completed')
            total_cnt = len(matches_all)
            progress_pct = completed_cnt / total_cnt if total_cnt > 0 else 0
            
            p_col1, p_col2 = st.columns([4, 1])
            with p_col1:
                st.progress(progress_pct, text=f"🏆 Competition Progress: {completed_cnt} of {total_cnt} Matches Completed ({int(progress_pct * 100)}%)")
            with p_col2:
                # Downloadable Text Report Button
                teams_all = db.get_tournament_teams(selected_tournament['id'])
                report_txt = generate_tournament_report(selected_tournament, matches_all, teams_all)
                st.download_button(
                    label="📄 Download Summary Report",
                    data=report_txt,
                    file_name=f"{selected_tournament['name'].replace(' ', '_')}_Report.txt",
                    mime="text/plain",
                    use_container_width=True
                )

        st.markdown("<br/>", unsafe_allow_html=True)

        # Navigation Tabs
        tab_bracket, tab_matches, tab_teams, tab_analytics, tab_predictor = st.tabs([
            "🏆 Visual Brackets & Standings", 
            "📅 Fixture Schedule & Results", 
            "🛡️ Teams & Rosters",
            "🏅 Top Performers & Analytics",
            "📊 Match Predictor & H2H"
        ])
        
        # TAB 1: VISUAL BRACKET OR STANDINGS TABLE
        with tab_bracket:
            if selected_tournament['format'] == "Knockout":
                matches = db.get_tournament_matches(selected_tournament['id'])
                
                if not matches:
                    st.info("The tournament matches have not been generated yet.")
                else:
                    # Check if champion exists (Final match completed)
                    final_matches = [m for m in matches if m['next_match_id'] is None]
                    if final_matches and final_matches[0]['status'] == "Completed" and final_matches[0]['winner_name']:
                        st.markdown(f"""
                            <div class="champion-box">
                                <h3 style="color: #d97706; margin:0; font-weight:800;">🏆 TOURNAMENT CHAMPION 🏆</h3>
                                <h1 style="color: #92400e; font-size: 38px; margin: 8px 0; font-weight: 800;">
                                    {final_matches[0]['winner_name']}
                                </h1>
                                <p style="color: #b45309; margin:0; font-weight:600;">Congratulations on winning the {selected_tournament['name']}!</p>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    st.subheader("🌳 Knockout Stage Bracket")
                    
                    # Group matches by Round Number
                    rounds_dict = {}
                    for m in matches:
                        r = m['round_number']
                        if r not in rounds_dict:
                            rounds_dict[r] = []
                        rounds_dict[r].append(m)
                        
                    round_cols = st.columns(len(rounds_dict))
                    max_round = max(rounds_dict.keys())
                    
                    for r_idx, (r_num, r_matches) in enumerate(sorted(rounds_dict.items())):
                        with round_cols[r_idx]:
                            # Round Titles
                            if r_num == max_round:
                                st.markdown("<h4 style='color:#d97706; text-align:center; font-weight:800;'>🏆 Grand Final</h4>", unsafe_allow_html=True)
                            elif r_num == max_round - 1:
                                st.markdown("<h4 style='color:#2563eb; text-align:center; font-weight:800;'>🥇 Semi-Finals</h4>", unsafe_allow_html=True)
                            elif r_num == max_round - 2:
                                st.markdown("<h4 style='color:#7c3aed; text-align:center; font-weight:800;'>🥈 Quarter-Finals</h4>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<h4 style='color:#475569; text-align:center; font-weight:700;'>Round {r_num}</h4>", unsafe_allow_html=True)
                                
                            for m in r_matches:
                                team_a = m['team_a_name'] if m['team_a_name'] else "TBD"
                                team_b = m['team_b_name'] if m['team_b_name'] else "TBD"
                                
                                is_winner_a = (m['winner_id'] and m['winner_id'] == m['team_a_id'])
                                is_winner_b = (m['winner_id'] and m['winner_id'] == m['team_b_id'])
                                
                                class_a = "team-winner" if is_winner_a else ""
                                class_b = "team-winner" if is_winner_b else ""
                                card_border = "bracket-card-completed" if m['status'] == "Completed" else ("bracket-card-live" if m['team_a_id'] and m['team_b_id'] else "")
                                
                                crown_a = "👑 " if is_winner_a else ""
                                crown_b = "👑 " if is_winner_b else ""
                                
                                tie_note = ""
                                if m['status'] == 'Completed' and m['score_a'] == m['score_b'] and m['winner_name']:
                                    sport = selected_tournament['sport_type']
                                    rule = "Penalty Shootout" if "Football" in sport else ("Overtime" if "Esports" in sport else ("Super Over" if "Cricket" in sport else "Tie-Break"))
                                    tie_note = f"<div style='font-size: 11px; color: #2563eb; font-weight: 700; text-align: center; margin-top: 6px;'>👑 {m['winner_name']} won via {rule}</div>"
                                
                                st.markdown(f"""
                                    <div class="bracket-card {card_border}">
                                        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                                            <small style="color:#64748b; font-weight:600;">Match #{m['match_number'] + 1}</small>
                                            <small class="badge {'badge-completed' if m['status'] == 'Completed' else 'badge-ongoing'}">{m['status']}</small>
                                        </div>
                                        <div class="team-row {class_a}">
                                            <span>{crown_a}{team_a}</span>
                                            <span class="score-badge">{m['score_a']}</span>
                                        </div>
                                        <div class="team-row {class_b}">
                                            <span>{crown_b}{team_b}</span>
                                            <span class="score-badge">{m['score_b']}</span>
                                        </div>
                                        {tie_note}
                                    </div>
                                """, unsafe_allow_html=True)

            else:  # Round Robin Standings Table
                st.subheader("📈 League Points Table & Standings")
                standings = round_robin.calculate_round_robin_standings(selected_tournament['id'])
                
                if not standings:
                    st.info("No standings data computed yet.")
                else:
                    st.dataframe(
                        standings,
                        column_config={
                            "rank": st.column_config.NumberColumn("Rank", format="#%d"),
                            "team_name": "Team Name",
                            "played": "Played (P)",
                            "won": "Won (W)",
                            "lost": "Lost (L)",
                            "drawn": "Drawn (D)",
                            "scored": "Points Scored",
                            "conceded": "Points Conceded",
                            "gd": "Goal Diff (GD)",
                            "points": st.column_config.NumberColumn("Total Points 🏆", format="%d pts")
                        },
                        hide_index=True,
                        use_container_width=True
                    )

        # TAB 2: MATCH SCHEDULE WITH SEARCH FILTER
        with tab_matches:
            st.subheader("📅 Complete Fixture Schedule")
            matches = db.get_tournament_matches(selected_tournament['id'])
            if not matches:
                st.info("No matches scheduled.")
            else:
                search_query = st.text_input("🔍 Search Match by Team Name:", placeholder="e.g. Apex Predators")
                filtered_matches = matches
                if search_query.strip():
                    q = search_query.lower()
                    filtered_matches = [m for m in matches if (m['team_a_name'] and q in m['team_a_name'].lower()) or (m['team_b_name'] and q in m['team_b_name'].lower())]

                for m in filtered_matches:
                    team_a = m['team_a_name'] if m['team_a_name'] else "TBD"
                    team_b = m['team_b_name'] if m['team_b_name'] else "TBD"
                    
                    is_winner_a = (m['winner_id'] and m['winner_id'] == m['team_a_id'])
                    is_winner_b = (m['winner_id'] and m['winner_id'] == m['team_b_id'])
                    
                    crown_a = "👑 " if is_winner_a else ""
                    crown_b = "👑 " if is_winner_b else ""
                    
                    color_a = "#2563eb" if is_winner_a else "#0f172a"
                    color_b = "#2563eb" if is_winner_b else "#0f172a"
                    
                    status_class = "badge-completed" if m['status'] == "Completed" else "badge-ongoing"
                    
                    tie_subtext = ""
                    if m['status'] == 'Completed' and m['score_a'] == m['score_b'] and m['winner_name']:
                        sport = selected_tournament['sport_type']
                        rule = "Penalty Shootout" if "Football" in sport else ("Overtime" if "Esports" in sport else ("Super Over" if "Cricket" in sport else "Tie-Break"))
                        tie_subtext = f'<div style="margin-top: 6px; font-size: 13px; color: #2563eb; font-weight: 700;">👑 {m["winner_name"]} won via {rule}</div>'
                    
                    card_html = f"""<div style="background: #ffffff; border: 1px solid #cbd5e1; padding: 14px; border-radius: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 8px rgba(148, 163, 184, 0.08);"><div><small style="color: #64748b; font-weight:600;">Round {m['round_number']} • Match #{m['id']}</small><br/><strong style="font-size: 16px; color:{color_a};">{crown_a}{team_a}</strong> <span style="background: #0f172a; color:#ffffff; padding: 4px 10px; border-radius: 6px; margin: 0 10px; font-weight:800;">{m['score_a']} - {m['score_b']}</span> <strong style="font-size: 16px; color:{color_b};">{crown_b}{team_b}</strong>{tie_subtext}</div><div><span class="badge {status_class}">{m['status']}</span></div></div>"""
                    st.markdown(card_html, unsafe_allow_html=True)

        # TAB 3: TEAMS & ROSTERS
        with tab_teams:
            st.subheader("👥 Registered Teams & Roster Details")
            teams = db.get_tournament_teams(selected_tournament['id'])
            if not teams:
                st.info("No teams registered yet.")
            else:
                t_cols = st.columns(2)
                for idx, team in enumerate(teams):
                    with t_cols[idx % 2]:
                        roster = json.loads(team['roster'])
                        st.markdown(f"""
                            <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 18px; margin-bottom: 14px; box-shadow: 0 4px 12px rgba(148,163,184,0.1);">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <h3 style="margin:0; color:#2563eb; font-weight:800;">🛡️ {team['name']}</h3>
                                    <span class="badge badge-league">Seed #{team['seed_number']}</span>
                                </div>
                                <p style="color:#64748b; margin: 6px 0; font-weight:600;"><strong>Captain:</strong> {team['captain_name']}</p>
                                <hr style="border-color: #f1f5f9;"/>
                                <p style="font-size:13px; font-weight:700; color:#334155; margin-bottom:6px;">Player Roster:</p>
                                <div style="display:flex; flex-wrap:wrap; gap:6px;">
                                    {"".join([f'<span style="background:#f1f5f9; color:#0f172a; border:1px solid #e2e8f0; padding:4px 10px; border-radius:6px; font-size:12px; font-weight:600;">👤 {p}</span>' for p in roster])}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

        # TAB 4: TOP PERFORMERS & ANALYTICS
        with tab_analytics:
            st.subheader("🏅 Tournament Top Performers & Analytics")
            matches = db.get_tournament_matches(selected_tournament['id'])
            teams = db.get_tournament_teams(selected_tournament['id'])
            
            completed_matches = [m for m in matches if m['status'] == 'Completed']
            if not completed_matches:
                st.info("No completed matches yet. Complete or simulate matches to view top performer analytics!")
            else:
                team_stats = {t['id']: {'name': t['name'], 'scored': 0, 'conceded': 0, 'wins': 0, 'matches': 0} for t in teams}
                biggest_win = {'margin': 0, 'match_str': 'N/A'}
                
                for m in completed_matches:
                    a_id, b_id = m['team_a_id'], m['team_b_id']
                    sc_a, sc_b = m['score_a'], m['score_b']
                    
                    if a_id in team_stats:
                        team_stats[a_id]['scored'] += sc_a
                        team_stats[a_id]['conceded'] += sc_b
                        team_stats[a_id]['matches'] += 1
                        if m['winner_id'] == a_id:
                            team_stats[a_id]['wins'] += 1
                            
                    if b_id in team_stats:
                        team_stats[b_id]['scored'] += sc_b
                        team_stats[b_id]['conceded'] += sc_a
                        team_stats[b_id]['matches'] += 1
                        if m['winner_id'] == b_id:
                            team_stats[b_id]['wins'] += 1
                            
                    margin = abs(sc_a - sc_b)
                    if margin > biggest_win['margin']:
                        biggest_win['margin'] = margin
                        biggest_win['match_str'] = f"{m['team_a_name']} ({sc_a}) vs ({sc_b}) {m['team_b_name']}"
                
                top_offense = sorted(team_stats.values(), key=lambda x: x['scored'], reverse=True)[0]
                top_defense = sorted([t for t in team_stats.values() if t['matches'] > 0], key=lambda x: x['conceded'])[0]
                
                an_col1, an_col2, an_col3 = st.columns(3)
                with an_col1:
                    st.markdown(f"""
                        <div style="background: #ffffff; border: 1px solid #bfdbfe; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 4px 12px rgba(37,99,235,0.08);">
                            <div style="font-size: 32px;">🔥</div>
                            <h4 style="margin: 6px 0 2px 0; color: #1e40af; font-weight:800;">Top Offense</h4>
                            <h2 style="margin: 4px 0; color: #0f172a;">{top_offense['name']}</h2>
                            <span class="badge badge-knockout" style="font-size: 13px;">{top_offense['scored']} Points Scored</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                with an_col2:
                    st.markdown(f"""
                        <div style="background: #ffffff; border: 1px solid #bbf7d0; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 4px 12px rgba(22,163,74,0.08);">
                            <div style="font-size: 32px;">🛡️</div>
                            <h4 style="margin: 6px 0 2px 0; color: #15803d; font-weight:800;">Best Defense</h4>
                            <h2 style="margin: 4px 0; color: #0f172a;">{top_defense['name']}</h2>
                            <span class="badge badge-ongoing" style="font-size: 13px;">Only {top_defense['conceded']} Conceded</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                with an_col3:
                    st.markdown(f"""
                        <div style="background: #ffffff; border: 1px solid #fef08a; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 4px 12px rgba(202,138,4,0.08);">
                            <div style="font-size: 32px;">⚡</div>
                            <h4 style="margin: 6px 0 2px 0; color: #a16207; font-weight:800;">Biggest Win Margin</h4>
                            <h3 style="margin: 4px 0; color: #0f172a; font-size: 15px;">{biggest_win['match_str']}</h3>
                            <span class="badge badge-league" style="font-size: 13px;">+{biggest_win['margin']} Difference</span>
                        </div>
                    """, unsafe_allow_html=True)

        # TAB 5: MATCH PREDICTOR & HEAD-TO-HEAD
        with tab_predictor:
            st.subheader("📊 Match Predictor & Head-to-Head Analytics")
            teams = db.get_tournament_teams(selected_tournament['id'])
            
            if len(teams) < 2:
                st.info("At least 2 registered teams required for Head-to-Head prediction.")
            else:
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    idx_a = st.selectbox("Select Team A:", range(len(teams)), format_func=lambda i: teams[i]['name'])
                with col_p2:
                    default_b = 1 if len(teams) > 1 else 0
                    idx_b = st.selectbox("Select Team B:", range(len(teams)), index=default_b, format_func=lambda i: teams[i]['name'])
                    
                team_a, team_b = teams[idx_a], teams[idx_b]
                
                if team_a['id'] == team_b['id']:
                    st.warning("Please select two different teams for Head-to-Head comparison!")
                else:
                    seed_a, seed_b = team_a['seed_number'], team_b['seed_number']
                    prob_a = max(20, min(80, 50 + (seed_b - seed_a) * 5))
                    prob_b = 100 - prob_a
                    
                    st.markdown("<br/>", unsafe_allow_html=True)
                    st.markdown("#### 🎯 Predicted Win Probability:")
                    
                    p1, p2 = st.columns([prob_a, prob_b])
                    with p1:
                        st.markdown(f"<div style='background:#2563eb; color:white; text-align:center; padding:10px; border-radius:6px 0 0 6px; font-weight:800;'>{team_a['name']}: {prob_a}%</div>", unsafe_allow_html=True)
                    with p2:
                        st.markdown(f"<div style='background:#dc2626; color:white; text-align:center; padding:10px; border-radius:0 6px 6px 0; font-weight:800;'>{prob_b}%: {team_b['name']}</div>", unsafe_allow_html=True)
                        
                    st.markdown("<br/>", unsafe_allow_html=True)
                    st.markdown("#### ⚔️ Side-by-Side Team Comparison:")
                    comp_c1, comp_c2 = st.columns(2)
                    
                    with comp_c1:
                        st.markdown(f"""
                            <div style="background:#ffffff; border:1px solid #cbd5e1; border-radius:10px; padding:16px; box-shadow: 0 2px 8px rgba(37,99,235,0.08);">
                                <h3 style="color:#2563eb; margin:0; font-weight:800;">🛡️ {team_a['name']}</h3>
                                <p style="margin:6px 0; color:#475569;"><strong>Captain:</strong> {team_a['captain_name']}</p>
                                <span class="badge badge-knockout">Team Rank #{team_a['seed_number']}</span>
                            </div>
                        """, unsafe_allow_html=True)
                        
                    with comp_c2:
                        st.markdown(f"""
                            <div style="background:#ffffff; border:1px solid #cbd5e1; border-radius:10px; padding:16px; box-shadow: 0 2px 8px rgba(220,38,38,0.08);">
                                <h3 style="color:#dc2626; margin:0; font-weight:800;">🛡️ {team_b['name']}</h3>
                                <p style="margin:6px 0; color:#475569;"><strong>Captain:</strong> {team_b['captain_name']}</p>
                                <span class="badge badge-league">Team Rank #{team_b['seed_number']}</span>
                            </div>
                        """, unsafe_allow_html=True)

# ==============================================================================
# VIEW 2: ADMIN / ORGANIZER PORTAL
# ==============================================================================
elif st.session_state["current_role"] == "Admin / Organizer":
    st.subheader("🛠️ Organizer Control Center")
    
    admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs([
        "✨ Create Tournament", 
        "🛡️ Manage Teams & Start", 
        "📝 Live Score Controller",
        "⚙️ Deletion & Reset Management"
    ])
    
    # TAB 1: CREATE TOURNAMENT
    with admin_tab1:
        st.markdown("### Create Competition Parameters")
        with st.form("admin_create_form"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                name = st.text_input("Tournament Title", placeholder="e.g. Inter-College Champions Cup")
                sport_type = st.selectbox("Sport / Game Category", ["Chess", "Football", "Esports (Valorant/BGMI)", "Basketball", "Cricket"])
            with col_f2:
                format_type = st.selectbox("Tournament Format", ["Knockout", "Round Robin"])
                max_teams = st.number_input("Max Registered Teams", min_value=2, max_value=32, value=8)
                
            col_f3, col_f4 = st.columns(2)
            with col_f3:
                match_duration = st.number_input("Match Duration (Minutes)", min_value=10, max_value=180, value=45)
                venue = st.text_input("Venue / Location", value="Main Campus Indoor Arena")
            with col_f4:
                start_date = st.text_input("Scheduled Start Date", value="2026-09-15")
            
            submit_create = st.form_submit_button("🚀 Launch Tournament Blueprint")
            if submit_create:
                if not name.strip():
                    st.error("Please enter a valid tournament title!")
                else:
                    new_id = db.create_tournament(name, sport_type, format_type, max_teams, match_duration, venue=venue, start_date=start_date)
                    st.success(f"Tournament '{name}' initialized with ID #{new_id}!")
                    st.rerun()

    # TAB 2: MANAGE TEAMS & START TOURNAMENT
    with admin_tab2:
        if not selected_tournament:
            st.warning("Please select a tournament from the sidebar.")
        else:
            st.markdown(f"### Managing: **{selected_tournament['name']}**")
            existing_teams = db.get_tournament_teams(selected_tournament['id'])
            
            col_list, col_add = st.columns([1, 1])
            
            with col_list:
                st.markdown(f"**Registered Participants ({len(existing_teams)} / {selected_tournament['max_teams']}):**")
                for t in existing_teams:
                    st.markdown(f"- **Seed #{t['seed_number']}**: {t['name']} *(Captain: {t['captain_name']})*")
                    
            with col_add:
                st.markdown("**Add Existing Team to Tournament:**")
                all_teams = db.get_all_teams()
                registered_ids = [t['id'] for t in existing_teams]
                available_teams = [t for t in all_teams if t['id'] not in registered_ids]
                
                if available_teams:
                    with st.form("add_team_form"):
                        sel_team_idx = st.selectbox(
                            "Select Team", 
                            range(len(available_teams)), 
                            format_func=lambda i: available_teams[i]['name']
                        )
                        team_sel = available_teams[sel_team_idx]
                        seed_val = st.number_input("Assign Seed Number", min_value=1, value=len(existing_teams) + 1)
                        if st.form_submit_button("Add Team"):
                            db.register_team_for_tournament(selected_tournament['id'], team_sel['id'], seed_val)
                            st.success(f"Added {team_sel['name']}!")
                            st.rerun()
                else:
                    st.info("No available unassigned teams. Create new teams in the 'Team Captain' portal!")

            st.markdown("---")
            if selected_tournament['status'] == "Upcoming":
                if len(existing_teams) >= 2:
                    if st.button("🔥 Generate Bracket & Start Tournament", use_container_width=True):
                        if selected_tournament['format'] == "Knockout":
                            knockout.generate_knockout_bracket(selected_tournament['id'], existing_teams)
                        else:
                            round_robin.generate_round_robin_schedule(selected_tournament['id'], existing_teams)
                        st.success("Fixtures generated and competition marked ONGOING!")
                        st.rerun()
                else:
                    st.error("At least 2 teams are required to start fixtures.")
            else:
                st.info(f"Tournament status is **{selected_tournament['status']}**.")

    # TAB 3: LIVE SCORE CONTROLLER
    with admin_tab3:
        if not selected_tournament:
            st.warning("Please select a tournament from the sidebar.")
        else:
            st.markdown("### Record Match Outcome & Winner Advancement")
            matches = db.get_tournament_matches(selected_tournament['id'])
            playable_matches = [m for m in matches if m['team_a_id'] and m['team_b_id'] and m['status'] != 'Completed']
            
            if not playable_matches:
                st.info("No playable matches waiting for scores right now!")
            else:
                match_labels = [f"Round {m['round_number']} - Match #{m['id']}: {m['team_a_name']} vs {m['team_b_name']}" for m in playable_matches]
                sel_m_idx = st.selectbox("Select Match to Score:", range(len(playable_matches)), format_func=lambda i: match_labels[i])
                target_m = playable_matches[sel_m_idx]
                
                st.markdown(f"""
                    <div style="background: #ffffff; padding: 16px; border-radius: 12px; border: 1px solid #2563eb; margin-bottom: 16px; box-shadow:0 4px 12px rgba(37,99,235,0.1);">
                        <h4 style="margin:0; text-align:center; color:#2563eb; font-weight:800;">Match #{target_m['id']} (Round {target_m['round_number']})</h4>
                        <div style="display:flex; justify-content:space-around; align-items:center; margin-top:10px;">
                            <h2 style="color:#0f172a; margin:0;">{target_m['team_a_name']}</h2>
                            <h3 style="color:#64748b; margin:0;">VS</h3>
                            <h2 style="color:#0f172a; margin:0;">{target_m['team_b_name']}</h2>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Check if a tied score resolution is pending for this match
                pending_key = f"pending_tie_{target_m['id']}"
                
                if pending_key in st.session_state:
                    p_sc_a, p_sc_b = st.session_state[pending_key]
                    sport = selected_tournament['sport_type']
                    if 'Esports' in sport:
                        tie_label = "🎮 Overtime / Extra Rounds Winner"
                    elif 'Football' in sport:
                        tie_label = "⚽ Penalty Shootout Winner (0-0 Draw / Tied Match)"
                    elif 'Cricket' in sport:
                        tie_label = "🏏 Super Over Winner (Tied Runs Match)"
                    elif 'Chess' in sport:
                        tie_label = "♟️ Armageddon Blitz Winner"
                    elif 'Basketball' in sport:
                        tie_label = "🏀 Overtime (OT) Winner"
                    else:
                        tie_label = "⚔️ Overtime Tie-Breaker Winner"
                        
                    st.warning(f"⚔️ Tied Score ({p_sc_a} - {p_sc_b}) Entered! Please select the official {tie_label}:")
                    
                    t_col1, t_col2 = st.columns(2)
                    with t_col1:
                        if st.button(f"🏆 Declare {target_m['team_a_name']} as Winner", type="primary", use_container_width=True):
                            knockout.record_knockout_match_result(target_m['id'], p_sc_a, p_sc_b, winner_id=target_m['team_a_id'])
                            del st.session_state[pending_key]
                            st.success(f"Match score ({p_sc_a} - {p_sc_b}) recorded! Winner: {target_m['team_a_name']}")
                            st.rerun()
                            
                    with t_col2:
                        if st.button(f"🏆 Declare {target_m['team_b_name']} as Winner", type="primary", use_container_width=True):
                            knockout.record_knockout_match_result(target_m['id'], p_sc_a, p_sc_b, winner_id=target_m['team_b_id'])
                            del st.session_state[pending_key]
                            st.success(f"Match score ({p_sc_a} - {p_sc_b}) recorded! Winner: {target_m['team_b_name']}")
                            st.rerun()
                else:
                    with st.form("score_entry_form"):
                        is_cricket = selected_tournament['sport_type'] == 'Cricket'
                        label_a = f"Runs for {target_m['team_a_name']}" if is_cricket else f"Score / Goals for {target_m['team_a_name']}"
                        label_b = f"Runs for {target_m['team_b_name']}" if is_cricket else f"Score / Goals for {target_m['team_b_name']}"
                        
                        sc_col1, sc_col2 = st.columns(2)
                        with sc_col1:
                            score_a = st.number_input(label_a, min_value=0, value=0)
                        with sc_col2:
                            score_b = st.number_input(label_b, min_value=0, value=0)

                        if st.form_submit_button("💾 Save Match Result & Advance Winner"):
                            try:
                                if selected_tournament['format'] == "Knockout":
                                    if score_a == score_b:
                                        # Trigger tie resolution prompt on save!
                                        st.session_state[pending_key] = (score_a, score_b)
                                        st.rerun()
                                    else:
                                        knockout.record_knockout_match_result(target_m['id'], score_a, score_b)
                                else:
                                    round_robin.record_round_robin_match_result(target_m['id'], score_a, score_b)
                                st.success("Score recorded successfully!")
                                st.rerun()
                            except ValueError as err:
                                st.error(str(err))

    # TAB 4: DELETION & RESET MANAGEMENT CONTROLLER
    with admin_tab4:
        st.markdown("### ⚙️ Tournament Deletion & Reset Controls")
        if not selected_tournament:
            st.warning("No active tournament selected.")
        else:
            del_c1, del_c2, del_c3 = st.columns(3)
            
            with del_c1:
                st.markdown(f"#### 🗑️ Delete Active Tournament")
                st.caption(f"Deletes #{selected_tournament['id']} ({selected_tournament['name']}) and associated matches.")
                if st.button("🗑️ Delete Selected Tournament", type="primary", use_container_width=True):
                    db.delete_tournament(selected_tournament['id'])
                    st.success("Tournament deleted!")
                    st.rerun()
                    
            with del_c2:
                st.markdown("#### 🔄 Reset Match Scores")
                st.caption("Resets match scores back to 0 and status to Scheduled.")
                if st.button("🔄 Reset Match Scores", use_container_width=True):
                    db.reset_tournament_matches(selected_tournament['id'])
                    st.success("Scores reset back to Scheduled!")
                    st.rerun()
                    
            with del_c3:
                st.markdown("#### 🧹 Clear All Test Data")
                st.caption("Wipes all test tournaments in the database for a clean start.")
                if st.button("🧹 Wipe ALL Tournaments", use_container_width=True):
                    db.delete_all_tournaments()
                    st.success("All tournaments cleared!")
                    st.rerun()

# ==============================================================================
# VIEW 3: TEAM CAPTAIN PORTAL (1-CLICK QUICK JOIN & CUSTOM BUILDER!)
# ==============================================================================
elif st.session_state["current_role"] == "Team Captain":
    st.subheader("🛡️ Team Captain Registration Portal")
    
    # Fetch all announced / upcoming tournaments open for registration
    all_tourns = db.get_all_tournaments()
    open_tournaments = []
    
    for tourn in all_tourns:
        if tourn['status'] == 'Upcoming':
            teams_in_tourn = db.get_tournament_teams(tourn['id'])
            if len(teams_in_tourn) < tourn['max_teams']:
                open_tournaments.append((tourn, len(teams_in_tourn)))
                
    if not open_tournaments:
        st.warning("⚠️ No announced upcoming tournaments currently open for registration! Please contact the Organizer to create a tournament.")
    else:
        reg_mode = st.radio("Choose Registration Mode:", ["⚡ 1-Click Select Team (Registered Teams)", "✍️ Custom Team & Roster Builder"], horizontal=True)
        
        st.markdown("---")
        
        # Select target announced tournament
        tourn_options = [f"#{t[0]['id']} - {t[0]['name']} ({t[0]['sport_type']} - {t[0]['format']}) [{t[1]}/{t[0]['max_teams']} Teams]" for t in open_tournaments]
        selected_tourn_idx = st.selectbox("🎯 Select Announced Tournament to Join:", range(len(open_tournaments)), format_func=lambda i: tourn_options[i])
        target_tourn, current_team_count = open_tournaments[selected_tourn_idx]
        
        st.markdown(f"""
            <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:10px; padding:12px; margin-bottom:16px;">
                <strong style="color:#1e40af;">Tournament Details:</strong> {target_tourn['name']}<br/>
                <small style="color:#3b82f6;">Format: {target_tourn['format']} • Sport: {target_tourn['sport_type']} • Capacity: {current_team_count}/{target_tourn['max_teams']} Registered Teams</small>
            </div>
        """, unsafe_allow_html=True)

        # MODE 1: 1-CLICK SELECT TEAM FROM LIST
        if reg_mode == "⚡ 1-Click Select Team (Registered Teams)":
            all_global_teams = db.get_all_teams()
            existing_tourn_teams = db.get_tournament_teams(target_tourn['id'])
            existing_ids = [t['id'] for t in existing_tourn_teams]
            
            available_to_join = [t for t in all_global_teams if t['id'] not in existing_ids]
            
            if not available_to_join:
                st.info("All registered global teams are already in this tournament!")
            else:
                st.markdown("### ⚡ Select Team to Join Tournament")
                with st.form("quick_select_team_form"):
                    sel_join_idx = st.selectbox(
                        "🛡️ Select Team:", 
                        range(len(available_to_join)), 
                        format_func=lambda i: f"{available_to_join[i]['name']} (Captain: {available_to_join[i]['captain_name']})"
                    )
                    team_choice = available_to_join[sel_join_idx]
                    
                    if st.form_submit_button("🚀 1-Click Join Tournament"):
                        assigned_seed = current_team_count + 1
                        db.register_team_for_tournament(target_tourn['id'], team_choice['id'], assigned_seed)
                        st.success(f"🎉 Team '{team_choice['name']}' successfully registered for '{target_tourn['name']}'! (Assigned Seed #{assigned_seed})")
                        st.rerun()

        # MODE 2: CUSTOM TEAM BUILDER
        else:
            st.markdown("### ✍️ Custom Team Builder")
            with st.form("captain_custom_register_form"):
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    t_name = st.text_input("Team Name", placeholder="e.g. Shadow Strikers")
                with col_c2:
                    c_name = st.text_input("Captain Name", placeholder="e.g. John Doe")
                    
                contact_email = st.text_input("Captain Contact Email / Phone (Optional)", placeholder="captain@college.edu")
                r_text = st.text_area("Player Roster Names (One per line)", placeholder="Player 1\nPlayer 2\nPlayer 3")
                
                if st.form_submit_button("🚀 Submit Official Team Registration"):
                    if not t_name.strip() or not c_name.strip():
                        st.error("Please enter both Team Name and Captain Name!")
                    else:
                        players = [p.strip() for p in r_text.split("\n") if p.strip()]
                        if not players:
                            players = [c_name]
                        try:
                            team_id = db.create_team(t_name, c_name, players)
                            assigned_seed = current_team_count + 1
                            db.register_team_for_tournament(target_tourn['id'], team_id, assigned_seed)
                            st.success(f"🎉 Team '{t_name}' successfully registered for '{target_tourn['name']}'! (Assigned Seed #{assigned_seed})")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Could not complete registration: {e}")

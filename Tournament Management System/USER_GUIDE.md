# Tournament Management System - Official User & Operator Guide

Welcome to the **Tournament Management System (TMS v2.0)**! This comprehensive manual provides step-by-step instructions on how to use, navigate, and demonstrate every feature of the application.

---

## 📌 1. Quick Start: How to Launch the Application

1. Open your terminal / command prompt.
2. Navigate to the project folder:
   ```powershell
   cd "c:\Users\Joydip Maiti\Desktop\Tournament Management System"
   ```
3. Run the application:
   ```powershell
   python -m streamlit run app.py
   ```
4. The application will automatically open in your default browser at `http://localhost:8501`.

---

## 👤 2. Understanding the Top Role Switcher Bar

At the top of the main screen, you will see the **Top Perspective Switcher Bar**:
```
[ 🌐 Public Spectator View ]   [ 🛠️ Organizer Controller ]   [ 🛡️ Team Captain Portal ]
```
Clicking any pill button instantly switches the user role without touching the sidebar!

---

## 🌐 3. Public Spectator View Guide

This mode provides a read-only, high-visibility dashboard for fans, players, and evaluators.

### Features & Navigation Tabs:
1. **🏆 Visual Brackets & Standings**:
   - **Knockout Format**: Renders side-by-side round columns (Round 1, Quarter-Finals, Semi-Finals, Grand Final) showing live scores, winner crowns (👑), and explicit tie-breaker notes for tied matches!
   - **Grand Final Champion Box**: When the final match finishes, a gold trophy banner appears announcing the Champion!
   - **Round Robin Format**: Displays a real-time Points Table with Rank (#1, #2...), Played (P), Won (W), Lost (L), Drawn (D), Points Scored, Conceded, Goal Difference (GD), and Total Points.

2. **📅 Fixture Schedule & Results**:
   - Lists all scheduled and completed matches.
   - Highlights match winners with a crown icon (👑) and displays explicit tie-breaker notes (e.g. `👑 Shadow Ninjas won via Penalty Shootout` or `👑 Vanguard Esports won via Overtime`).
   - Includes a **🔍 Search Match by Team Name** input box to filter fixtures instantly.

3. **🛡️ Teams & Rosters**:
   - Displays all registered teams, team seeds, captain names, and player roster tags.

4. **🏅 Top Performers & Analytics**:
   - **🔥 Top Offense**: Automatically identifies the team with the most total points scored.
   - **🛡️ Best Defense**: Highlights the team with the fewest points conceded.
   - **⚡ Biggest Win Margin**: Displays the match with the largest score differential.

5. **📊 Match Predictor & Head-to-Head**:
   - Select any 2 teams to compare their stats side-by-side and calculate **Win Probability %**.

6. **📄 Download Summary Report Button**:
   - Click **`📄 Download Summary Report`** in the top right to download an official text summary report of tournament parameters, rosters, and match results.

---

## 🛡️ 4. Team Captain Portal Guide

This mode allows Team Captains to register their teams for announced upcoming competitions.

### Step-by-Step Team Registration:
1. Click **`🛡️ Team Captain Portal`** at the top of the page.
2. Under **`🎯 Select Announced Tournament to Join`**, choose the target tournament from the dropdown.
3. Choose your registration mode:
   - **Option A: `⚡ 1-Click Select Team (Registered Teams)`** *(Recommended for fast demo)*:
     - Select a pre-loaded team (e.g., `Shadow Strikers`, `Cyber Knights`, `Apex Predators`).
     - Click **`🚀 1-Click Join Tournament`**.
   - **Option B: `✍️ Custom Team & Roster Builder`**:
     - Enter Team Name, Captain Name, Contact Details, and Player Names (one per line).
     - Click **`🚀 Submit Official Team Registration`**.
4. The system automatically registers the team and assigns its **Team Seed Number**!

---

## 🛠️ 5. Organizer Control Center Guide

This mode provides administrative control over tournament creation, team management, match scoring, and deletion.

### Tab 1: ✨ Create Tournament
1. Enter **Tournament Title** (e.g., *Campus Valorant Championship*).
2. Select **Sport / Game Category** (*Esports*, *Football*, *Cricket*, *Chess*, *Basketball*).
3. Select **Tournament Format** (*Knockout* or *Round Robin*).
4. Set **Max Registered Teams** (e.g., 4 or 8) and **Match Duration**.
5. Set **Venue / Location** (e.g., *Main Campus Arena* or *Server AP-South*) and **Start Date**.
6. Click **`🚀 Launch Tournament Blueprint`**.

### Tab 2: 🛡️ Manage Teams & Start
1. View registered teams and assigned seed numbers.
2. Add any unassigned existing teams to the tournament.
3. When ready (at least 2 teams registered), click **`🔥 Generate Bracket & Start Tournament`**.
4. The engine automatically generates the binary tree bracket or round-robin fixtures and marks the tournament **ONGOING**!

### Tab 3: 📝 Live Score Controller
1. Select a match from the **`Select Match to Score`** dropdown.
2. Enter match scores:
   - **Football / Esports**: Enter Goals / Score (e.g., `0 - 0` or `12 - 8`).
   - **Cricket**: Enter total **Runs Scored** (e.g., `185 Runs` vs `185 Runs`).
3. **Handling Tied Scores (Knockout Format)**:
   - When equal scores are saved (including `0 - 0` Football draws or `185 - 185` Cricket ties), the system prompts the Admin to select the official winner:
     - Football: `🏆 Declare Team A as Penalty Shootout Winner (0-0 Draw)`
     - Cricket: `🏆 Declare Team A as Super Over Winner (Tied Runs)`
     - Esports: `🏆 Declare Team A as Overtime Winner`
4. Clicking the winner button saves the score and advances the winner!
5. In the Public View, the match card explicitly displays how the tie was broken (e.g. `👑 Shadow Ninjas won via Penalty Shootout`).

### Tab 4: ⚙️ Deletion & Reset Management
- **`🗑️ Delete Selected Tournament`**: Permanently removes the active tournament and linked matches.
- **`🔄 Reset Match Scores`**: Resets all scores back to `0` and status to `Scheduled` so you can re-run the score entry demo.
- **`🧹 Wipe ALL Tournaments`**: Clears all tournaments and resets the ID sequence counter back to `#1`.

---

## 🎬 6. Perfect 60-Second Live Demonstration Script

Follow this exact sequence for a flawless 1-minute evaluation demo:

1. **Start Screen**:
   - Open app $\rightarrow$ Click **`🛠️ Organizer Controller`** $\rightarrow$ Sidebar: Click **`🎮 Valorant`** under *Sample Tournament Generators*.
2. **Demonstrate Public View**:
   - Click **`🌐 Public Spectator View`** at the top.
   - Show the **Visual Bracket Tree**, **Top Performers Analytics**, and **Match Predictor** tabs.
3. **Demonstrate Live Match Advancement**:
   - Click **`🛠️ Organizer Controller`** $\rightarrow$ Tab 3: **`📝 Live Score Controller`**.
   - Enter `12` for Team A and `8` for Team B $\rightarrow$ Click **`💾 Save Match Result`**.
   - Switch back to **`🌐 Public Spectator View`** $\rightarrow$ Point out how Team A automatically advanced to Round 2 with a winner crown (👑)!
4. **Demonstrate Report Exporter**:
   - Click **`📄 Download Summary Report`** at the top right to show the exported official text report card!

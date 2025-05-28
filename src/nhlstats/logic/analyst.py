import shutil
import json
import os
import matplotlib.pyplot as plt

# Find the statistics directory relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATISTICS_DIR = os.path.join(BASE_DIR, "statistics")

with open(os.path.join(STATISTICS_DIR, "teamsStats.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

with open(os.path.join(STATISTICS_DIR, "todayGames.json"), "r", encoding="utf-8") as f:
    todaysGames = json.load(f)


def player_elo():
    # Load player stats
    with open(os.path.join(STATISTICS_DIR, "playerStats.json"), "r", encoding="utf-8") as f:
        players = json.load(f)

    # --- Copy current playerelo.json to playerelo_prev.json before updating ---
    playerelo_path = os.path.join(STATISTICS_DIR, "playerelo.json")
    playerelo_prev_path = os.path.join(STATISTICS_DIR, "playerelo_prev.json")
    if os.path.exists(playerelo_path):
        shutil.copy(playerelo_path, playerelo_prev_path)

    # Default ELO calculation weights
    base_elo = 1200
    default_goal_weight = 10
    default_assist_weight = 7
    default_point_weight = 15
    plusminus_weight = 2
    ppg_weight = 50  # Points-per-game weight (adjust as needed)

    # Defensemen get higher weights
    defense_goal_weight = 12
    defense_assist_weight = 9
    defense_point_weight = 18

    elos = {}
    for player in players:
        position = player.get("position", "").upper()
        games = player.get("gamesPlayed", 0)
        points = player.get("points", 0)
        ppg = points / games if games > 0 else 0

        if position in ["D", "DEF", "DEFENSEMAN", "DEFENSEMEN"]:
            goal_weight = defense_goal_weight
            assist_weight = defense_assist_weight
            point_weight = defense_point_weight
        else:
            goal_weight = default_goal_weight
            assist_weight = default_assist_weight
            point_weight = default_point_weight

        elo = (
            base_elo
            + player.get("goals", 0) * goal_weight
            + player.get("assists", 0) * assist_weight
            + points * point_weight
            + player.get("plusMinus", 0) * plusminus_weight
            + ppg * ppg_weight  # Add points-per-game bonus
        )
        elos[player["id"]] = {
            "name": player["name"],
            "team": player.get("team"),
            "position": player.get("position"),
            "elo": round(elo, 2)   # <-- round to 2 decimals
        }

    # Save to playerelo.json
    with open(playerelo_path, "w", encoding="utf-8") as f:
        json.dump(elos, f, ensure_ascii=False, indent=2)

    return elos

# Basic elo system based on average points and goal differential
def team_elo(teams, base_elo=1500, points_weight=5, gd_weight=1):
    # Calculate league averages
    avg_points = sum(team['points'] for team in teams) / len(teams)
    avg_gd = sum(team['goalDifferential'] for team in teams) / len(teams)

    elos = {}
    for team in teams:
        # ELO is base + (points above avg) * weight + (GD above avg) * weight
        elo = (
            base_elo
            + (team['points'] - avg_points) * points_weight
            + (team['goalDifferential'] - avg_gd) * gd_weight
        )
        elos[team['abrev']] = round(elo, 1)
    return elos
#put in json file



def plot_top_players(n=20, position=None, team=None):
    """
    Plot the top n players by ELO.
    Optionally filter by position (e.g., "C", "L", "R", "D", "G") and/or team abbreviation (e.g., "BOS").
    """
    with open(os.path.join(STATISTICS_DIR, "playerelo.json"), "r", encoding="utf-8") as f:
        elos = json.load(f)

    # Convert to list and filter
    players = []
    for v in elos.values():
        if position and v.get("position", "").upper() != position.upper():
            continue
        if team and v.get("team", "").upper() != team.upper():
            continue
        players.append({"name": v["name"], "team": v["team"], "elo": v["elo"], "position": v.get("position", "")})

    players.sort(key=lambda x: x["elo"], reverse=True)
    top_players = players[:n]

    if not top_players:
        print("No players found with the given filters.")
        return

    names = [f"{p['name']} ({p['team']}, {p['position']})" for p in top_players]
    elos = [p["elo"] for p in top_players]

    plt.figure(figsize=(12, 6))
    bars = plt.barh(names[::-1], elos[::-1], color="skyblue")
    plt.xlabel("ELO")
    plt.title(f"Top {n} NHL Players by ELO"
              + (f" | Position: {position.upper()}" if position else "")
              + (f" | Team: {team.upper()}" if team else ""))

    # Ajouter la valeur ELO à l'intérieur de chaque barre
    for bar, elo in zip(bars, elos[::-1]):
        plt.text(
            bar.get_width() - 10,  # Légèrement à gauche du bord droit de la barre
            bar.get_y() + bar.get_height() / 2,
            f"{elo:.1f}",
            va='center',
            ha='right',
            color='white',
            fontsize=10,
            fontweight='bold'
        )

    plt.tight_layout()
    plt.show()

# Example usages:
#plot_top_players(20)  # Top 20 overall
#plot_top_players(10, position="D")  # Top 10 defensemen
#plot_top_players(15, team="BOS")  # Top 15 players from Boston
#plot_top_players(5, position="C", team="EDM")  # Top 5 centers from Edmonton
#plot_top_players(5, team='MTL')  # Top 5 centers from Montreal

# Example usage:
"""
elos = team_elo(data)
for abbr, elo in sorted(elos.items(), key=lambda x: x[1], reverse=True):
    print(f"{abbr}: {elo}")
"""

# Example usage:
#player_elo()


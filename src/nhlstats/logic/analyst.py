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

    playerelo_path = os.path.join(STATISTICS_DIR, "playerelo.json")
    playerelo_prev_path = os.path.join(STATISTICS_DIR, "playerelo_prev.json")
    if os.path.exists(playerelo_path):
        shutil.copy(playerelo_path, playerelo_prev_path)

    base_elo = 1200
    ppg_weight = 400
    career_ppg_weight = 120
    defense_bonus = 1.10
    playoff_bonus_weight = 60
    min_games = 10

    # Goalie weights
    save_pctg_weight = 300
    gaa_weight = -150
    shutout_weight = 10
    win_weight = 5
    playoff_goalie_weight = 40

    elos = {}
    for player in players:
        position = player.get("position", "").upper()
        if position in ["G", "GOALIE", "GOALTENDER"]:
            # Goalie ELO calculation
            games = player.get("gamesPlayed", 0)
            wins = player.get("wins", 0)
            save_pctg = player.get("savePctg", 0)
            gaa = player.get("goalsAgainstAvg", 0)
            shutouts = player.get("shutouts", 0)

            career_games = player.get("careerGamesPlayed", 0)
            career_save_pctg = player.get("careerSavePctg", 0)
            career_gaa = player.get("careerGoalsAgainstAvg", 0)
            career_shutouts = player.get("careerShutouts", 0)
            career_wins = player.get("careerWins", 0)

            playoff_games = player.get("playoffGamesPlayed", 0)
            playoff_save_pctg = player.get("playoffSavePctg", 0)
            playoff_gaa = player.get("playoffGoalsAgainstAvg", 0)
            playoff_shutouts = player.get("playoffShutouts", 0)
            playoff_wins = player.get("playoffWins", 0)

            # ELO formula for goalies
            elo = (
                base_elo
                + save_pctg * save_pctg_weight
                + gaa * gaa_weight
                + shutouts * shutout_weight
                + wins * win_weight
                + career_save_pctg * (save_pctg_weight // 3)
                + career_gaa * (gaa_weight // 3)
                + career_shutouts * (shutout_weight // 2)
                + career_wins * (win_weight // 2)
                + playoff_save_pctg * playoff_goalie_weight
                + playoff_shutouts * (shutout_weight // 2)
                + playoff_wins * (win_weight // 2)
            )
        else:
            # Skater ELO calculation (as before)
            games = player.get("gamesPlayed", 0)
            points = player.get("points", 0)
            ppg = points / games if games > 0 else 0

            career_games = player.get("careerGamesPlayed", 0)
            career_points = player.get("careerPoints", 0)
            career_ppg = career_points / career_games if career_games > 0 else 0

            playoff_games = player.get("playoffGamesPlayed", 0)
            playoff_points = player.get("playoffPoints", 0)
            playoff_ppg = playoff_points / playoff_games if playoff_games > 0 else 0

            career_playoff_games = player.get("careerPlayoffGamesPlayed", 0)
            career_playoff_points = player.get("careerPlayoffPoints", 0)
            career_playoff_ppg = career_playoff_points / career_playoff_games if career_playoff_games > 0 else 0

            playoff_bonus = 0
            if playoff_games >= min_games:
                playoff_bonus += playoff_ppg * playoff_bonus_weight
            if career_playoff_games >= min_games:
                playoff_bonus += career_playoff_ppg * (playoff_bonus_weight // 2)

            is_defense = position in ["D", "DEF", "DEFENSEMAN", "DEFENSEMEN"]
            multiplier = defense_bonus if is_defense else 1.0

            elo = (
                base_elo
                + ppg * ppg_weight
                + career_ppg * career_ppg_weight
                + playoff_bonus
            ) * multiplier

        elos[player["id"]] = {
            "name": player["name"],
            "team": player.get("team"),
            "position": player.get("position"),
            "elo": round(elo, 2)
        }

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



import requests
import json
import os
from datetime import datetime

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATISTICS_DIR = os.path.join(BASE_DIR, "statistics")
os.makedirs(STATISTICS_DIR, exist_ok=True)

def stats():
    url = 'https://api-web.nhle.com/v1/standings/now'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        equipes_stats = []

        for record in data.get('standings', []):
            equipe_info = {
                "team": record['teamName']['default'],
                "abrev": record['teamAbbrev']['default'],
                "conference": record['conferenceName'],
                "division": record['divisionName'],
                "points": record['points'],
                "homePoints": record['homePoints'],
                "roadPoints": record['roadPoints'],
                "gamesPlayed": record['gamesPlayed'],
                "wins": record['wins'],
                "homeWins": record['homeWins'],
                "roadWins": record['roadWins'],
                "loses": record['losses'],
                "homeLoses": record['homeLosses'],
                "roadLoses": record['roadLosses'],
                "OtWins": record['otLosses'],
                "goalDifferential": record['goalDifferential'],
                "goalAgainst": record['goalAgainst'],
            }
            equipes_stats.append(equipe_info)
        
        with open(os.path.join(STATISTICS_DIR, "teamsStats.json"), "w", encoding="utf-8") as f:
            json.dump(equipes_stats, f, ensure_ascii=False, indent=4)

def today_schedule():
    url = 'https://api-web.nhle.com/v1/schedule/now'
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return

    data = response.json()
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_games = []

    for day in data.get("gameWeek", []):
        if day.get("date") == today_str:
            for game in day.get("games", []):
                game_info = {
                    "date": day["date"],
                    "venue": game["venue"]["default"],
                    "startTimeUTC": game["startTimeUTC"],
                    "homeTeam": {
                        "name": game["homeTeam"]["placeName"]["default"] + " " + game["homeTeam"]["commonName"]["default"],
                        "abbrev": game["homeTeam"]["abbrev"]
                    },
                    "awayTeam": {
                        "name": game["awayTeam"]["placeName"]["default"] + " " + game["awayTeam"]["commonName"]["default"],
                        "abbrev": game["awayTeam"]["abbrev"]
                    }
                }
                today_games.append(game_info)

    with open(os.path.join(STATISTICS_DIR, "todayGames.json"), "w", encoding="utf-8") as f:
        json.dump(today_games, f, indent=2, ensure_ascii=False)

    print(f"{len(today_games)} game(s) saved to todayGames.json")



def team_players(abbr, season_id):
    url = f"https://api-web.nhle.com/v1/roster/{abbr}/{season_id}"
    response = requests.get(url)
    data = response.json()
    informations = []

    # The API groups players by position
    for group in ["forwards", "defensemen", "goalies"]:
        for player in data.get(group, []):
            player_info = {
                "name": f"{player['firstName']['default']} {player['lastName']['default']}",
                "id": player["id"],
                "position": player.get("positionCode", group[:-1].capitalize()),
                "height": player.get("heightInCentimeters"),
                "weight": player.get("weightInKilograms"),
                "birthDate": player.get("birthDate"),
                "headshot": player.get("headshot"),
                "heroImage": player.get("heroImage")  # <-- Correction ici
            }
            informations.append(player_info)
    return informations

def player_stats(player_id, season_id):
    url = f"https://api-web.nhle.com/v1/player/{player_id}/landing"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    data = response.json()
    stats = data.get("featuredStats", {}).get("regularSeason", {}).get("subSeason", {})
    return {
        "gamesPlayed": stats.get("gamesPlayed", 0),
        "goals": stats.get("goals", 0),
        "assists": stats.get("assists", 0),
        "points": stats.get("points", 0),
        "plusMinus": stats.get("plusMinus", 0),
        "sweaterNumber": data.get("sweaterNumber", ""),
        "birthDate": data.get("birthDate", ""),
        "headshot": data.get("headshot", ""),
        "heroImage": data.get("heroImage", ""),
        "teamLogo": data.get("teamLogo", "")
    }



def collect_all_player_stats(season_id):
    with open(os.path.join(STATISTICS_DIR, "teamsStats.json"), "r", encoding="utf-8") as f:
        teams = json.load(f)

    all_players = []
    for team in teams:
        abbr = team.get("abrev")
        if not abbr:
            print(f"Missing abrev for team: {team}")
            continue
        print(f"Fetching players for team: {abbr}")
        players = team_players(abbr, season_id)
        print(f"  Found {len(players)} players")
        for player in players:
            stats = player_stats(player["id"], season_id)
            # On récupère headshot et heroImage depuis player ou stats
            headshot = stats.get("headshot") or player.get("headshot") or ""
            hero_image = stats.get("heroImage") or player.get("heroImage") or ""
            if stats:
                player_info = {
                    "id": player["id"],
                    "name": player["name"],
                    "team": abbr,
                    "position": player.get("position"),
                    **stats,
                    "headshot": headshot,
                    "heroImage": hero_image  # Un seul champ, cohérent partout
                }
                all_players.append(player_info)
            else:
                print(f"    No stats for player {player['name']} ({player['id']})")

    print(f"Total players collected: {len(all_players)}")
    with open(os.path.join(STATISTICS_DIR, "playerStats.json"), "w", encoding="utf-8") as f:
        json.dump(all_players, f, ensure_ascii=False, indent=2)


def collector():
    stats()
    today_schedule()
    # Use the current season id, e.g. "20242025"
    collect_all_player_stats("20242025")

#collector()






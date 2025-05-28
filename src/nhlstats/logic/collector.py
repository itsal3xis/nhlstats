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

    position = ""
    if isinstance(data.get("position"), dict):
        position = data["position"].get("code", "").upper()
    else:
        position = str(data.get("position", "")).upper()


    awards = []
    for award in data.get("awards", []):
        trophy = award.get("trophy", {}).get("default") or award.get("displayName", "")
        seasons = [s.get("seasonId") for s in award.get("seasons", [])] or [award.get("season")]
        awards.append({
            "trophy": trophy,
            "seasons": seasons
        })

    # Regular season (current sub-season)
    reg_stats = data.get("featuredStats", {}).get("regularSeason", {}).get("subSeason", {})
    reg_career = data.get("featuredStats", {}).get("regularSeason", {}).get("career", {})
    po_stats = data.get("featuredStats", {}).get("playoffs", {}).get("subSeason", {})
    po_career = data.get("featuredStats", {}).get("playoffs", {}).get("career", {})

    # If goalie, collect goalie stats
    if position == "G":
        awards = []
        for award in data.get("awards", []):
            if award.get("displayName") and award.get("season"):
                awards.append({
                    "name": award["displayName"],
                    "season": award["season"]
                })
        return {
            # Regular season (current)
            "gamesPlayed": reg_stats.get("gamesPlayed", 0),
            "wins": reg_stats.get("wins", 0),
            "losses": reg_stats.get("losses", 0),
            "otLosses": reg_stats.get("otLosses", 0),
            "goalsAgainstAvg": reg_stats.get("goalsAgainstAvg", 0),
            "savePctg": reg_stats.get("savePctg", 0),
            "shutouts": reg_stats.get("shutouts", 0),

            # Career regular season
            "careerGamesPlayed": reg_career.get("gamesPlayed", 0),
            "careerWins": reg_career.get("wins", 0),
            "careerLosses": reg_career.get("losses", 0),
            "careerOtLosses": reg_career.get("otLosses", 0),
            "careerGoalsAgainstAvg": reg_career.get("goalsAgainstAvg", 0),
            "careerSavePctg": reg_career.get("savePctg", 0),
            "careerShutouts": reg_career.get("shutouts", 0),

            # Playoffs (current)
            "playoffGamesPlayed": po_stats.get("gamesPlayed", 0),
            "playoffWins": po_stats.get("wins", 0),
            "playoffLosses": po_stats.get("losses", 0),
            "playoffOtLosses": po_stats.get("otLosses", 0),
            "playoffGoalsAgainstAvg": po_stats.get("goalsAgainstAvg", 0),
            "playoffSavePctg": po_stats.get("savePctg", 0),
            "playoffShutouts": po_stats.get("shutouts", 0),

            # Career playoffs
            "careerPlayoffGamesPlayed": po_career.get("gamesPlayed", 0),
            "careerPlayoffWins": po_career.get("wins", 0),
            "careerPlayoffLosses": po_career.get("losses", 0),
            "careerPlayoffOtLosses": po_career.get("otLosses", 0),
            "careerPlayoffGoalsAgainstAvg": po_career.get("goalsAgainstAvg", 0),
            "careerPlayoffSavePctg": po_career.get("savePctg", 0),
            "careerPlayoffShutouts": po_career.get("shutouts", 0),

            # Identity
            "sweaterNumber": data.get("sweaterNumber", ""),
            "birthDate": data.get("birthDate", ""),
            "headshot": data.get("headshot", ""),
            "heroImage": data.get("heroImage", ""),
            "teamLogo": data.get("teamLogo", ""),
            "awards": awards
        }
    # Otherwise, skater stats (as before)
    return {
        # Regular season (current)
        "gamesPlayed": reg_stats.get("gamesPlayed", 0),
        "goals": reg_stats.get("goals", 0),
        "assists": reg_stats.get("assists", 0),
        "points": reg_stats.get("points", 0),
        "plusMinus": reg_stats.get("plusMinus", 0),
        "shots": reg_stats.get("shots", 0),
        "pim": reg_stats.get("pim", 0),
        "powerPlayGoals": reg_stats.get("powerPlayGoals", 0),
        "powerPlayPoints": reg_stats.get("powerPlayPoints", 0),
        "shorthandedGoals": reg_stats.get("shorthandedGoals", 0),
        "shorthandedPoints": reg_stats.get("shorthandedPoints", 0),
        "gameWinningGoals": reg_stats.get("gameWinningGoals", 0),
        "otGoals": reg_stats.get("otGoals", 0),
        "shootingPctg": reg_stats.get("shootingPctg", 0),

        # Career regular season
        "careerGamesPlayed": reg_career.get("gamesPlayed", 0),
        "careerGoals": reg_career.get("goals", 0),
        "careerAssists": reg_career.get("assists", 0),
        "careerPoints": reg_career.get("points", 0),
        "careerPlusMinus": reg_career.get("plusMinus", 0),
        "careerShots": reg_career.get("shots", 0),
        "careerPim": reg_career.get("pim", 0),
        "careerPowerPlayGoals": reg_career.get("powerPlayGoals", 0),
        "careerPowerPlayPoints": reg_career.get("powerPlayPoints", 0),
        "careerShorthandedGoals": reg_career.get("shorthandedGoals", 0),
        "careerShorthandedPoints": reg_career.get("shorthandedPoints", 0),
        "careerGameWinningGoals": reg_career.get("gameWinningGoals", 0),
        "careerOtGoals": reg_career.get("otGoals", 0),
        "careerShootingPctg": reg_career.get("shootingPctg", 0),

        # Playoffs (current)
        "playoffGamesPlayed": po_stats.get("gamesPlayed", 0),
        "playoffGoals": po_stats.get("goals", 0),
        "playoffAssists": po_stats.get("assists", 0),
        "playoffPoints": po_stats.get("points", 0),
        "playoffPlusMinus": po_stats.get("plusMinus", 0),
        "playoffShots": po_stats.get("shots", 0),
        "playoffPim": po_stats.get("pim", 0),
        "playoffPowerPlayGoals": po_stats.get("powerPlayGoals", 0),
        "playoffPowerPlayPoints": po_stats.get("powerPlayPoints", 0),
        "playoffShorthandedGoals": po_stats.get("shorthandedGoals", 0),
        "playoffShorthandedPoints": po_stats.get("shorthandedPoints", 0),
        "playoffGameWinningGoals": po_stats.get("gameWinningGoals", 0),
        "playoffOtGoals": po_stats.get("otGoals", 0),
        "playoffShootingPctg": po_stats.get("shootingPctg", 0),

        # Career playoffs
        "careerPlayoffGamesPlayed": po_career.get("gamesPlayed", 0),
        "careerPlayoffGoals": po_career.get("goals", 0),
        "careerPlayoffAssists": po_career.get("assists", 0),
        "careerPlayoffPoints": po_career.get("points", 0),
        "careerPlayoffPlusMinus": po_career.get("plusMinus", 0),
        "careerPlayoffShots": po_career.get("shots", 0),
        "careerPlayoffPim": po_career.get("pim", 0),
        "careerPlayoffPowerPlayGoals": po_career.get("powerPlayGoals", 0),
        "careerPlayoffPowerPlayPoints": po_career.get("powerPlayPoints", 0),
        "careerPlayoffShorthandedGoals": po_career.get("shorthandedGoals", 0),
        "careerPlayoffShorthandedPoints": po_career.get("shorthandedPoints", 0),
        "careerPlayoffGameWinningGoals": po_career.get("gameWinningGoals", 0),
        "careerPlayoffOtGoals": po_career.get("otGoals", 0),
        "careerPlayoffShootingPctg": po_career.get("shootingPctg", 0),

        # Identity
        "sweaterNumber": data.get("sweaterNumber", ""),
        "birthDate": data.get("birthDate", ""),
        "headshot": data.get("headshot", ""),
        "heroImage": data.get("heroImage", ""),
        "teamLogo": data.get("teamLogo", ""),
        "awards": awards,
        "last5Games": data.get("last5Games", []),
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
                    "heroImage": hero_image,
                    # "last5Games" est déjà dans stats
                }
                all_players.append(player_info)
            else:
                print(f"    No stats for player {player['name']} ({player['id']})")

    print(f"Total players collected: {len(all_players)}")
    with open(os.path.join(STATISTICS_DIR, "playerStats.json"), "w", encoding="utf-8") as f:
        json.dump(all_players, f, ensure_ascii=False, indent=2)


def last_games(player_id, season_id, count=5):
    url = f"https://api-web.nhle.com/v1/player/{player_id}/game-log/{season_id}"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    data = response.json()
    games = data.get("gameLog", [])[:count]
    # Détection goalie/skater
    is_goalie = any(g.get("savePctg") is not None or g.get("goalsAgainst") is not None for g in games)
    result = []
    for g in games:
        if is_goalie:
            result.append({
                "gameDate": g.get("gameDate"),
                "gameId": g.get("gameId"),
                "gameTypeId": g.get("gameTypeId"),
                "gamesStarted": g.get("gamesStarted"),
                "goalsAgainst": g.get("goalsAgainst"),
                "homeRoadFlag": g.get("homeRoadFlag"),
                "opponentAbbrev": g.get("opponentAbbrev"),
                "pim": g.get("pim"),
                "savePctg": g.get("savePctg"),
                "shotsAgainst": g.get("shotsAgainst"),
                "teamAbbrev": g.get("teamAbbrev"),
                "toi": g.get("toi"),
            })
        else:
            result.append({
                "gameDate": g.get("gameDate"),
                "gameId": g.get("gameId"),
                "gameTypeId": g.get("gameTypeId"),
                "goals": g.get("goals"),
                "assists": g.get("assists"),
                "points": g.get("points"),
                "plusMinus": g.get("plusMinus"),
                "shots": g.get("shots"),
                "hits": g.get("hits"),
                "blockedShots": g.get("blockedShots"),
                "pim": g.get("pim"),
                "powerPlayGoals": g.get("powerPlayGoals"),
                "shorthandedGoals": g.get("shorthandedGoals"),
                "shifts": g.get("shifts"),
                "toi": g.get("toi"),
                "teamAbbrev": g.get("teamAbbrev"),
                "opponentAbbrev": g.get("opponentAbbrev"),
                "homeRoadFlag": g.get("homeRoadFlag"),
            })
    return result

def reg_season():
    now = datetime.now()
    if now.month < 9:
        year1 = now.year - 1
        year2 = now.year
    else:
        year1 = now.year
        year2 = now.year + 1
    return f"{year1}{year2}" 


def collector():
    stats()
    today_schedule()
    season = reg_season()
    # Use the current season id, e.g. "20242025"
    collect_all_player_stats(f"{season}")







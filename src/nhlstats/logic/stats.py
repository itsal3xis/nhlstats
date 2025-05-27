import requests
import json
from datetime import datetime

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
        
        with open("/statistics/teamsStats.json", "w", encoding="utf-8") as f:
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

    with open("statistics/todayGames.json", "w", encoding="utf-8") as f:
        json.dump(today_games, f, indent=2, ensure_ascii=False)

    print(f"{len(today_games)} game(s) saved to today_games.json")



def team_players(abbr, season_id):
    url = "https://api-web.nhle.com/v1/roster/{abbr}/{season_id}"
    url = url.format(abbr=abbr, season_id=season_id)
    response = requests.get(url)
    data = response.json()
    informations = []
    for player in data.get("players", []):
        player_info = {
            "name": player["fullName"],
            "id": player["id"],
            "position": player["position"]["default"],
            "height": player["heightInCentimeters"],
            "weight": player["weightInKilograms"],
            "birthDate": player["birthDate"]
        }
        informations.append(player_info)
    return informations

def player_stats(player_id, season_id):
    url = "https://api-web.nhle.com/v1/player/{player_id}/landing"
    url = url.format(player_id=player_id)
    response = requests.get(url)
    data = response.json()



def collector():
    stats()
    today_schedule()



    

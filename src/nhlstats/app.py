import matplotlib
matplotlib.use('Agg')
from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
import matplotlib.pyplot as plt
import io
import base64
import random
from collections import defaultdict

app = Flask(__name__)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATISTICS_DIR = os.path.join(BASE_DIR, "logic", "statistics")

def get_top_players_per_team(stats, elos, recent_game_ids, per_team=3):
    players_by_team = defaultdict(list)
    for p in stats:
        if p['id'] in recent_game_ids:
            team = p.get('team')
            if team:
                p_elo = elos.get(str(p['id']), {}).get('elo', 0)
                players_by_team[team].append({**p, 'elo': p_elo})
    top_players = []
    for team, players in players_by_team.items():
        players.sort(key=lambda x: x['elo'], reverse=True)
        top_players.extend(players[:per_team] or players[:1])
    return top_players

def load_today_game_player_ids():
    today_games_path = os.path.join(STATISTICS_DIR, "todayGames.json")
    if not os.path.exists(today_games_path):
        return []
    with open(today_games_path, "r", encoding="utf-8") as f:
        games = json.load(f)
    player_ids = set()
    for game in games:
        for team in ("home", "away"):
            for player in game.get(team + "_players", []):
                player_ids.add(player["id"])
    return list(player_ids)

def load_today_game_teams():
    today_games_path = os.path.join(STATISTICS_DIR, "todayGames.json")
    if not os.path.exists(today_games_path):
        return []
    with open(today_games_path, "r", encoding="utf-8") as f:
        games = json.load(f)
    teams = set()
    for game in games:
        if "homeTeam" in game and "abbrev" in game["homeTeam"]:
            teams.add(game["homeTeam"]["abbrev"])
        if "awayTeam" in game and "abbrev" in game["awayTeam"]:
            teams.add(game["awayTeam"]["abbrev"])
    return list(teams)

@app.route('/', methods=['GET', 'POST'])
def index():
    player_info = None
    with open(os.path.join(STATISTICS_DIR, "playerelo.json"), "r", encoding="utf-8") as f:
        elos = json.load(f)
    with open(os.path.join(STATISTICS_DIR, "playerStats.json"), "r", encoding="utf-8") as f:
        stats = json.load(f)
    prev_elos_path = os.path.join(STATISTICS_DIR, "playerelo_prev.json")
    prev_elos = {}
    if os.path.exists(prev_elos_path):
        with open(prev_elos_path, "r", encoding="utf-8") as f:
            prev_elos = json.load(f)

    # Handle search/filter
    if request.method == 'POST':
        player_name = request.form.get('player_name', '').strip().lower()
        team = request.form.get('team', '')
        position = request.form.get('position', '')
        filtered_stats = stats
        if team:
            filtered_stats = [p for p in filtered_stats if p.get('team') == team]
        if position:
            filtered_stats = [p for p in filtered_stats if p.get('position') == position]
        for p in elos.values():
            if player_name in p['name'].lower():
                stat = next((s for s in filtered_stats if s['name'].lower() == p['name'].lower()), None)
                if stat:
                    player_info = {**p, **stat}
                else:
                    player_info = p
                break

    # Trending players
    trending_players = get_trending_players(stats, elos, prev_elos, top_n=3)

    # Get teams playing today
    today_teams = load_today_game_teams()
    recent_players = []
    for team in today_teams:
        team_players = [p for p in stats if p.get('team') == team]
        for p in team_players:
            p['elo'] = elos.get(str(p['id']), {}).get('elo', 0)
            p['elo_change'] = round(elos.get(str(p['id']), {}).get('elo', 0) - prev_elos.get(str(p['id']), {}).get('elo', 0), 2)
        if team_players:
            top_player = max(team_players, key=lambda x: x['elo'])
            recent_players.append(top_player)

    return render_template(
        'index.html',
        player=player_info,
        recent_players=recent_players,
        trending_players=trending_players
    )

@app.route('/player/<int:player_id>', methods=['GET', 'POST'])
def detailed_player_info(player_id):
    with open(os.path.join(STATISTICS_DIR, "playerStats.json"), "r", encoding="utf-8") as f:
        stats = json.load(f)
    with open(os.path.join(STATISTICS_DIR, "playerelo.json"), "r", encoding="utf-8") as f:
        elos = json.load(f)
    player = next((s for s in stats if s['id'] == player_id), None)
    if not player:
        return "No player", 404

    prev_elos_path = os.path.join(STATISTICS_DIR, "playerelo_prev.json")
    prev_elos = {}
    if os.path.exists(prev_elos_path):
        with open(prev_elos_path, "r", encoding="utf-8") as f:
            prev_elos = json.load(f)
    player_elo_info = elos.get(str(player_id))
    if player_elo_info and 'elo' in player_elo_info:
        player['elo'] = player_elo_info['elo']
        player['elo_change'] = round(player['elo'] - prev_elos.get(str(player_id), {}).get('elo', 0), 2)
    else:
        player['elo'] = None
        player['elo_change'] = 0

    # Comparaison par équipe OU position
    compare_by = request.form.get('compare_by', 'position')
    if compare_by == 'position':
        group_all = [v for v in elos.values() if v.get('position') == player.get('position')]
        title = f"ELO of {player.get('position', '')} NHL"
    else:
        group_all = [v for v in elos.values() if v.get('team') == player.get('team')]
        title = f"ELO of players on {player.get('team', '')}"

    # Trie tout le groupe par ELO décroissant
    group_all = sorted(group_all, key=lambda x: x['elo'], reverse=True)

    # Trouve l'index du joueur courant
    try:
        idx = next(i for i, g in enumerate(group_all) if g['name'] == player['name'])
    except StopIteration:
        idx = 0  # fallback

    # Prend 4 au-dessus et 5 en dessous (ou ajuste si début/fin de liste)
    start = max(0, idx - 4)
    end = min(len(group_all), idx + 5 + 1)
    group = group_all[start:end]

    # S'assure que le joueur courant est bien dans le groupe (au cas où)
    if player['name'] not in [g['name'] for g in group]:
        group.append(player)

    # Trie à nouveau pour l'affichage
    group = sorted(group, key=lambda x: x['elo'], reverse=True)

    # Préparation des données pour le graphique
    names = [g['name'] for g in group]
    elos_list = [g['elo'] for g in group]

    # Met en surbrillance le joueur courant
    colors = ['#4fc3f7' if g['name'] == player['name'] else '#888' for g in group]

    # Génère le graphique
    fig, ax = plt.subplots(figsize=(14, 6))  # Agrandit le graphique
    bars = ax.barh(names[::-1], elos_list[::-1], color=colors[::-1])
    ax.set_xlabel("ELO")
    ax.set_title(title)
    for bar, elo in zip(bars, elos_list[::-1]):
        ax.text(bar.get_width() - 10, bar.get_y() + bar.get_height()/2, f"{elo:.1f}", va='center', ha='right', color='white', fontsize=10, fontweight='bold')
    plt.tight_layout()

    ax.set_facecolor('#181c24')
    fig.patch.set_facecolor('#181c24')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')
    for spine in ax.spines.values():
        spine.set_color('white')

    # Convertit le graphique en image base64
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", facecolor='#181c24')
    plt.close(fig)
    buf.seek(0)
    graph_url = base64.b64encode(buf.getvalue()).decode('utf8')
    graph_url = f"data:image/png;base64,{graph_url}"

    # Trouver le joueur le plus proche en ELO (hors lui-même, même position)
    player_elo = player.get('elo')
    player_id = player.get('id')
    player_position = player.get('position', '').strip().lower()
    similar_player = None
    min_diff = float('inf')

    for elo_id_str, p in elos.items():
        elo_id = int(elo_id_str)
        pos = p.get('position', '').strip().lower()
        if (
            elo_id != player_id
            and 'elo' in p and p['elo'] is not None
            and pos == player_position
        ):
            diff = abs(p['elo'] - player_elo)
            if diff < min_diff:
                min_diff = diff
                similar_player = {'id': elo_id, **p}

    # Fusionne avec les infos stats (headshot, etc)
    if similar_player:
        stat_similar = next((s for s in stats if s.get('id') == similar_player['id']), None)
        if stat_similar:
            similar_player = {**similar_player, **stat_similar}

    for i, (elo_id_str, p) in enumerate(elos.items()):
        if i > 10: break
        print(f"  id={elo_id_str}, name={p.get('name')}, position={p.get('position')}, elo={p.get('elo')}")

    return render_template(
        'player_detail.html',
        player=player,
        elo_graph=graph_url,
        similar_player=similar_player
    )

@app.route('/duel/<int:player1_id>/<int:player2_id>')
def detailed_duel(player1_id, player2_id):
    import os, json
    with open(os.path.join(STATISTICS_DIR, "playerStats.json"), "r", encoding="utf-8") as f:
        stats = json.load(f)
    with open(os.path.join(STATISTICS_DIR, "playerelo.json"), "r", encoding="utf-8") as f:
        elos = json.load(f)

    # Find player stats and merge with ELO
    def get_player(pid):
        stat = next((s for s in stats if str(s.get('id')) == str(pid)), {})
        elo = elos.get(str(pid), {}).get('elo', 0)
        # Provide defaults if missing
        return {
            "id": pid,
            "name": stat.get("name", f"Player {pid}"),
            "headshot": stat.get("headshot", stat.get("heroImage", "")),
            "elo": elo,
            "goals": stat.get("goals", 0),
            "assists": stat.get("assists", 0),
            "points": stat.get("points", 0),
            "plusMinus": stat.get("plusMinus", 0),
            "gamesPlayed": stat.get("gamesPlayed", 0),
            "sweaterNumber": stat.get("sweaterNumber", ""),
            "teamLogo": stat.get("teamLogo", ""),
        }

    player1 = get_player(player1_id)
    player2 = get_player(player2_id)

    # Stat comparison logic (as before)
    stat_keys = ["goals", "assists", "points", "plusMinus"]
    stat_labels = {
        "goals": "Goals",
        "assists": "Assists",
        "points": "Points",
        "plusMinus": "+/-",
        "gamesPlayed": "Games Played",
        "elo": "ELO"
    }
    comparison = []
    p1_score = 0
    p2_score = 0
    for key in stat_keys:
        v1 = player1.get(key, 0)
        v2 = player2.get(key, 0)
        if v1 > v2:
            winner = 1
            p1_score += 1
        elif v2 > v1:
            winner = 2
            p2_score += 1
        else:
            winner = 0
        comparison.append({
            "label": stat_labels.get(key, key),
            "p1": v1,
            "p2": v2,
            "winner": winner
        })

    if p1_score > p2_score:
        duel_winner = 1
    elif p2_score > p1_score:
        duel_winner = 2
    else:
        duel_winner = 0

    return render_template(
        'duel.html',
        player1=player1,
        player2=player2,
        comparison=comparison,
        p1_score=p1_score,
        p2_score=p2_score,
        duel_winner=duel_winner
    )

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q', '').strip().lower()
    if not query:
        return jsonify([])
    with open(os.path.join(STATISTICS_DIR, "playerStats.json"), "r", encoding="utf-8") as f:
        stats = json.load(f)
    results = []
    for player in stats:
        name = player.get('name', '')
        if query in name.lower():
            pid = player.get('id')
            headshot = player.get('headshot')
            results.append({
                'id': pid,
                'name': name,
                'headshot': headshot
            })
        if len(results) >= 2:
            break
    return jsonify(results)

@app.route('/random_player')
def random_player():
    with open(os.path.join(STATISTICS_DIR, "playerStats.json"), "r", encoding="utf-8") as f:
        stats = json.load(f)
    if not stats:
        return "No players available", 404
    player = random.choice(stats)
    return redirect(url_for('detailed_player_info', player_id=player['id']))

@app.route('/api/random_player_id')
def api_random_player_id():
    with open(os.path.join(STATISTICS_DIR, "playerStats.json"), "r", encoding="utf-8") as f:
        stats = json.load(f)
    if not stats:
        return jsonify({'id': None})
    player = random.choice(stats)
    return jsonify({'id': player['id']})

def get_elo_change(elos, prev_elos):
    """Returns a dict of player_id -> elo_change (float)"""
    changes = {}
    for pid, p in elos.items():
        prev = prev_elos.get(pid, {}).get('elo', 0)
        now = p.get('elo', 0)
        changes[pid] = round(now - prev, 2)
    return changes

def get_trending_players(stats, elos, prev_elos, top_n=3):
    changes = get_elo_change(elos, prev_elos)
    trending = []
    for p in stats:
        pid = str(p['id'])
        if pid in elos:
            elo = elos[pid].get('elo', 0)
            delta = changes.get(pid, 0)
            trending.append({**p, 'elo': elo, 'elo_change': delta})
    # Sort by absolute value of change, biggest up or down
    trending.sort(key=lambda x: abs(x['elo_change']), reverse=True)
    return trending[:top_n]

if __name__ == '__main__':
    # Ensure statistics directory exists
    if not os.path.exists(STATISTICS_DIR):
        os.makedirs(STATISTICS_DIR)

    # Collect data if needed
    #if not os.path.exists(os.path.join(STATISTICS_DIR, "playerelo.json")):
        #logic.collector.collector()
    
    app.run(debug=False, port=5001)

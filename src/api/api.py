from flask import Blueprint, jsonify, send_file, request
import os
import json
import matplotlib.pyplot as plt
import io
from flask import Flask


api = Blueprint('api', __name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATISTICS_DIR = os.path.join(BASE_DIR, "..", "nhlstats", "logic", "statistics")

@api.route('/players', methods=['GET'])
def get_players():
    with open(os.path.join(STATISTICS_DIR, "playerelo.json"), "r", encoding="utf-8") as f:
        elos = json.load(f)
    return jsonify(list(elos.values()))

@api.route('/player/<int:player_id>', methods=['GET'])
def get_player(player_id):
    with open(os.path.join(STATISTICS_DIR, "playerelo.json"), "r", encoding="utf-8") as f:
        elos = json.load(f)
    player = elos.get(str(player_id))
    if not player:
        return jsonify({"error": "Player not found"}), 404
    return jsonify(player)

@api.route('/top_players_graph')
def top_players_graph():
    n = int(request.args.get("n", 20))
    with open(os.path.join(STATISTICS_DIR, "playerelo.json"), "r", encoding="utf-8") as f:
        elos = json.load(f)
    players = sorted(elos.values(), key=lambda x: x["elo"], reverse=True)[:n]
    names = [f"{p['name']} ({p['team']})" for p in players]
    elos_list = [p["elo"] for p in players]

    plt.figure(figsize=(12, 6))
    plt.barh(names[::-1], elos_list[::-1], color="skyblue")
    plt.xlabel("ELO")
    plt.title(f"Top {n} NHL Players by ELO")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return send_file(buf, mimetype='image/png')



app = Flask(__name__)
app.register_blueprint(api, url_prefix='/api')

if __name__ == "__main__":
    app.run(debug=True, port=5001)
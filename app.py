from flask import Flask, jsonify
from flask_cors import CORS  # 👈 Add this
import requests

app = Flask(__name__)
CORS(app)  # 👈 Enable CORS for all routes
@app.route('/gameweek')
def get_gameweek():
    res = requests.get("https://fantasy.premierleague.com/api/event-status/")
    data = res.json()
    current_gw = data["status"][0]["event"]
    return jsonify({"gameweek": current_gw})

@app.route('/top-picks')
def top_picks():
    # Load data from FPL API
    players_data = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/").json()
    fixtures_data = requests.get("https://fantasy.premierleague.com/api/fixtures/").json()
    event_status = requests.get("https://fantasy.premierleague.com/api/event-status/").json()
    current_gw = event_status["status"][0]["event"]

    players = players_data['elements']
    teams = {team['id']: team['name'] for team in players_data['teams']}
    team_short_names = {team['id']: team['short_name'] for team in players_data['teams']}

    # Filter valid upcoming fixtures
    upcoming_fixtures = [f for f in fixtures_data if f['event'] == current_gw]

    top_picks = []
    for player in players:
        if player['minutes'] < 300:
            continue
        if player['news'] or (
            player.get('chance_of_playing_next_round') is not None and
            player['chance_of_playing_next_round'] < 75
        ):
            continue

        value = player['total_points'] / player['minutes']
        if float(player['form']) >= 5 and value >= 0.1:
            team_id = player['team']
            team_name = teams[team_id]
            form = float(player['form'])

            # Find upcoming fixture for the player's team
            fixture = next((f for f in upcoming_fixtures if f['team_h'] == team_id or f['team_a'] == team_id), None)
            if not fixture:
                continue

            is_home = fixture['team_h'] == team_id
            opponent_id = fixture['team_a'] if is_home else fixture['team_h']
            opponent = team_short_names[opponent_id]
            location = 'H' if is_home else 'A'

            top_picks.append({
                'name': f"{player['first_name']} {player['second_name']}",
                'team': team_name,
                'opponent': f"{opponent} ({location})",
                'form': player['form'],
                'points': player['total_points'],
                'price': player['now_cost'] / 10
            })

    top_picks = sorted(top_picks, key=lambda x: float(x['form']), reverse=True)[:10]
    return jsonify(top_picks)

@app.route('/fpl-data')
def fpl_data():
    response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
    data = response.json()
    players = data['elements']
    teams = {team['id']: team['name'] for team in data['teams']}
    positions = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

    suggestions = []
    for player in players:
        if player['minutes'] < 300:
            continue

        if player['news'] or (
            player.get('chance_of_playing_next_round') is not None and
            player['chance_of_playing_next_round'] < 75
        ):
            continue

        value = player['total_points'] / player['minutes']
        if float(player['form']) >= 5 and value >= 0.1:
            suggestions.append({
                'name': f"{player['first_name']} {player['second_name']}",
                'team': teams[player['team']],
                'position': positions[player['element_type']],
                'form': player['form'],
                'points': player['total_points'],
                'price': player['now_cost'] / 10
            })

    suggestions = sorted(suggestions, key=lambda x: float(x['form']), reverse=True)[:10]
    return jsonify(suggestions)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)

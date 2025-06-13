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
    players_data = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/").json()
    fixtures_data = requests.get("https://fantasy.premierleague.com/api/fixtures/").json()
    event_status = requests.get("https://fantasy.premierleague.com/api/event-status/").json()
    current_gw = event_status["status"][0]["event"]

    players = players_data['elements']
    teams = {team['id']: team['name'] for team in players_data['teams']}
    team_short_names = {team['id']: team['short_name'] for team in players_data['teams']}
    positions = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

    upcoming_fixtures = [f for f in fixtures_data if f['event'] == current_gw]

    scored_picks = []

    for player in players:
        if player['minutes'] < 300:
            continue
        if player['news'] or (
            player.get('chance_of_playing_next_round') is not None and
            player['chance_of_playing_next_round'] < 75
        ):
            continue

        form = float(player['form'])
        if form < 5:
            continue

        team_id = player['team']
        team_name = teams[team_id]
        player_position = positions[player['element_type']]

        fixture = next((f for f in upcoming_fixtures if f['team_h'] == team_id or f['team_a'] == team_id), None)
        if not fixture:
            continue

        is_home = fixture['team_h'] == team_id
        opponent_id = fixture['team_a'] if is_home else fixture['team_h']
        difficulty = fixture['team_h_difficulty'] if is_home else fixture['team_a_difficulty']

        score = (form * 2) + (6 - difficulty)

        scored_picks.append({
            'name': f"{player['first_name']} {player['second_name']}",
            'team': team_name,
            'position': player_position,
            'opponent': f"{team_short_names[opponent_id]} ({'H' if is_home else 'A'})",
            'form': player['form'],
            'points': player['total_points'],
            'price': player['now_cost'] / 10,
            'score': round(score, 2)
        })

    # Sort by score
    sorted_players = sorted(scored_picks, key=lambda x: x['score'], reverse=True)

    final_team = []
    position_count = {'GK': 0, 'DEF': 0, 'MID': 0, 'FWD': 0}

    for player in sorted_players:
        pos = player['position']

        # Ensure we have at least 1 goalkeeper
        if pos == 'GK' and position_count['GK'] < 1:
            final_team.append(player)
            position_count['GK'] += 1
        elif pos != 'GK' and len(final_team) < 11:
            final_team.append(player)
            position_count[pos] += 1

        if len(final_team) == 11:
            break

    return jsonify(final_team)

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

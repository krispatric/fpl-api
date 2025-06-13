from flask import Flask, jsonify
import requests

app = Flask(__name__)

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
        if player['news'] or player.get('chance_of_playing_next_round', 100) < 75:
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


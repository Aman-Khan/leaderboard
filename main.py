import os

from flask import Flask, send_file, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///local_database.db'
db = SQLAlchemy(app)

# Define the TeamScore model
class TeamScore(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    team_name = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)

# Define the TeamMembers model
class TeamMembers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_name = db.Column(db.String(50), nullable=False)
    team_name = db.Column(db.String(50), db.ForeignKey('team_score.team_name'), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    teams = TeamScore.query.order_by(TeamScore.score.desc()).all()
    return render_template('leaderboard.html', teams=teams)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        team_name = request.form.get('team_name')
        member_names = request.form.getlist('member_names[]')

        # Generate the team ID from the team name (lowercase, no spaces)
        team_id = team_name.lower().replace(' ', '_')

        if team_name:
            # Check if the team already exists
            existing_team = TeamScore.query.get(team_id)
            if existing_team:
                return jsonify({'error': 'Team already exists'}), 400

            # Create a new team
            new_team = TeamScore(id=team_id, team_name=team_name, score=0)
            db.session.add(new_team)
            db.session.commit()

            # Add members to the team
            for member_name in member_names:
                if member_name:
                    new_member = TeamMembers(member_name=member_name, team_name=team_name)
                    db.session.add(new_member)

            db.session.commit()

            return redirect(url_for('index'))

    return render_template('add_team.html')

@app.route('/teams_all')
def teams_all():
    teams = TeamScore.query.all()
    teams_data = []
    for team in teams:
        members = TeamMembers.query.filter_by(team_name=team.team_name).all()
        team_data = {
            'id': team.id,
            'team_name': team.team_name,
            'score': team.score,
            'members': [{'id': member.id, 'member_name': member.member_name} for member in members]
        }
        teams_data.append(team_data)
    
    return render_template('teams_all.html', teams=teams_data)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').lower()
    teams = db.session.query(TeamScore).join(TeamMembers).filter(TeamMembers.member_name.ilike(f'%{query}%')).distinct().all()
    teams_list = [{'id': team.id, 'team_name': team.team_name, 'score': team.score} for team in teams]
    return jsonify(teams_list)

@app.route('/update_score', methods=['POST'])
def update_score():
    team_id = request.form.get('team_id')
    new_score = request.form.get('score')
    
    if team_id and new_score:
        team = TeamScore.query.get(team_id)
        if team:
            team.score = int(new_score)
            db.session.commit()
            return jsonify({'message': 'Score updated successfully.'}), 200
    
    return jsonify({'error': 'Invalid team ID or score.'}), 400

@app.route('/search_page')
def search_page():
    return render_template('search.html')


# def main():
#     app.run(port=int(os.environ.get('PORT', 80)))

if __name__ == "__main__":
    app.run(port=8000, debug=True)

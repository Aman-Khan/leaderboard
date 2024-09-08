import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)

# Use environment variable for database URI
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'postgresql://default:liLPk1Ozt9CB@ep-billowing-sun-a1bkn2x0.ap-southeast-1.aws.neon.tech:5432/verceldb?sslmode=require')
db = SQLAlchemy(app)

CORS(app)

class TeamScore(db.Model):
    __tablename__ = 'team_score'
    id = db.Column(db.String, primary_key=True)
    team_name = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)

class TeamMembers(db.Model):
    __tablename__ = 'team_members'
    id = db.Column(db.Integer, primary_key=True)
    member_name = db.Column(db.String(50), nullable=False)
    team_id = db.Column(db.String, db.ForeignKey('team_score.id'), nullable=False)
    
    team = db.relationship('TeamScore', backref=db.backref('members', lazy=True))

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
                    new_member = TeamMembers(member_name=member_name, team_id=team_id)
                    db.session.add(new_member)

            db.session.commit()

            return redirect(url_for('index'))

    return render_template('add_team.html')


@app.route('/teams_all')
def teams_all():
    teams = TeamScore.query.all()
    teams_data = []
    for team in teams:
        members = TeamMembers.query.filter_by(team_id=team.id).all()
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


@app.route('/clear_database_page', methods=['GET'])
def clear_database_page():
    return render_template('clear_database.html')

@app.route('/clear_database', methods=['POST'])
def clear_database():
    try:
        # Drop all tables
        db.drop_all()
        
        # Recreate tables
        db.create_all()
        
        return jsonify({'message': 'Database cleared successfully.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# def main():
#     app.run(port=int(os.environ.get('PORT', 80)))

if __name__ == "__main__":
    app.run(port=8000, debug=True)

#!/usr/bin/env python3

from flask import Flask, request, session, jsonify, make_response
from models import db, User, Recipe
from flask_migrate import Migrate
from werkzeug.exceptions import Unauthorized, UnprocessableEntity

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = b'a\xdb\xd2\x13\x93\xc1\xe9\x97\xef2\xe3\x004U\xd1Z'

db.init_app(app)
migrate = Migrate(app, db)

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    image_url = data.get('image_url')
    bio = data.get('bio')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 422

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 422

    new_user = User(username=username, image_url=image_url, bio=bio)
    new_user.password_hash = password
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        return jsonify({'message': 'Login successful', 'username': user.username}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/logout', methods=['DELETE'])
def logout():
    if 'user_id' not in session or not session['user_id']:
        raise Unauthorized("No active session to log out from")

    session.pop('user_id')
    return {}, 204

@app.route('/check_session', methods=['GET'])
def check_session():
    user_id = session.get('user_id')
    if user_id:
        user = db.session.get(User, user_id)  # Updated line
        if user:
            return jsonify(user.to_dict()), 200
        else:
            return jsonify({'message': 'User not found'}), 404
    else:
        return jsonify({'message': 'No active session'}), 401

@app.route('/recipes', methods=['GET', 'POST'])
def handle_recipes():
    if request.method == 'GET':
        user_id = session.get('user_id')
        if not user_id:
            raise Unauthorized("User not logged in")

        recipes = Recipe.query.filter_by(user_id=user_id).all()
        return jsonify([recipe.to_dict() for recipe in recipes]), 200

    if request.method == 'POST':
        user_id = session.get('user_id')
        if not user_id:
            raise Unauthorized("User not logged in")

        data = request.get_json()
        title = data.get('title')
        instructions = data.get('instructions')
        minutes_to_complete = data.get('minutes_to_complete')

        if not title or len(instructions) < 50:
            raise UnprocessableEntity("Instructions must be at least 50 characters long")

        new_recipe = Recipe(
            title=title,
            instructions=instructions,
            minutes_to_complete=minutes_to_complete,
            user_id=user_id
        )
        db.session.add(new_recipe)
        db.session.commit()

        return make_response(jsonify(new_recipe.to_dict()), 201)

if __name__ == '__main__':
    app.run(debug=True)

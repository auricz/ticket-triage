from os import getenv
from secrets import token_hex

import argon2
from dotenv import load_dotenv
from datetime import datetime, timedelta
from flask import Flask, g, jsonify, request
from functools import wraps
import jwt

from models import db, User, Department, Severity

load_dotenv()

DB_NAME = getenv('DB_NAME')
DB_USER = getenv('DB_USER')
DB_PW = getenv('DB_PW')
DB_HOST = getenv('DB_HOST')
DB_PORT = getenv('DB_PORT')

JWT_ALGO = "HS256"

app = Flask(__name__)
app.config['SECRET_KEY'] = token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{DB_PW}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

db.init_app(app)

with app.app_context():
    db.create_all()

pw_hasher = argon2.PasswordHasher()

# Decorator to check JWT token and extract username
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        header = request.headers.get('Authorization')
        token = header.replace('Bearer ', '') if header else None
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            if data['exp'] < datetime.now().timestamp():
                raise jwt.ExpiredSignatureError
            
            g.username = data['username']
        except:
            return jsonify({'message': 'Token is invalid or expired!'}), 403
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['POST'])
def login():
    try:
        # Ensure the request has JSON content type
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json(silent=False) 

        # Validate required fields
        if "username" not in data or "password" not in data:
            return jsonify({"error": "Missing 'username' or 'password' field"}), 400
        
        # Get stored hash and verify
        username = data["username"]
        password = data["password"]
        
        stored_hash = db.session.execute(
            db.select(User.pw_hash).where(User.username == username)
        ).scalar_one_or_none()

        if stored_hash is None or not pw_hasher.verify(stored_hash, password):
            return jsonify({"error": "Invalid username or password"}), 401

        token = jwt.encode({
            'username': username,
            'exp': datetime.now() + timedelta(days=1)
        }, app.config['SECRET_KEY'], algorithm=JWT_ALGO)

        return jsonify({"token": token})

    except argon2.exceptions.VerifyMismatchError:
        return jsonify({"error": "Invalid username or password"}), 401
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/departments', methods=['GET'])
@auth_required
def get_departments():
    departments = Department.query.all()
    return [dep.name for dep in departments]

@app.route('/severities', methods=['GET'])
@auth_required
def get_severities():
    severities = Severity.query.all()
    return [sev.name for sev in severities]

if __name__ == "__main__":
    app.run(host='localhost', port=4000)
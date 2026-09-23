from math import ceil
from os import getenv
from secrets import token_hex

import argon2
from dotenv import load_dotenv
from datetime import datetime, timedelta
from flask import Flask, g, jsonify, request
from flask_socketio import SocketIO
from functools import wraps
import jwt

from models import db, User, Department, Severity, Ticket, AuditLog

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
socketio = SocketIO(app, cors_allowed_origins="*")

def _decode_token(token):
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=[JWT_ALGO])
    if data['exp'] < datetime.now().timestamp():
        raise jwt.ExpiredSignatureError
    return data

# Decorator to check JWT token and extract username
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        header = request.headers.get('Authorization')
        token = header.replace('Bearer ', '') if header else None
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        try:
            data = _decode_token(token)
            g.username = data['username']
            g.user_id = data['user_id']
        except:
            return jsonify({'message': 'Token is invalid or expired!'}), 403
        return f(*args, **kwargs)
    return decorated

# Rejects the websocket handshake unless a valid JWT is supplied, since
# ticket data broadcast over the socket is the same data the REST endpoints
# guard with auth_required.
@socketio.on('connect')
def handle_socket_connect(auth):
    token = (auth or {}).get('token') if isinstance(auth, dict) else None
    if not token:
        token = request.args.get('token')
    try:
        _decode_token(token)
    except:
        return False

def _record_audit(ticket_id, action):
    log = AuditLog()
    log.ticket_id = ticket_id
    log.action = action
    log.created_by = g.user_id
    db.session.add(log)

def _emit_ticket_created(ticket):
    socketio.emit('ticket_created', ticket.to_dict())

def _emit_ticket_updated(ticket):
    socketio.emit('ticket_updated', ticket.to_dict())

def _parse_datetime(value):
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None

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
        
        # Get stored user and verify
        username = data["username"]
        password = data["password"]

        user = db.session.execute(
            db.select(User).where(User.username == username)
        ).scalar_one_or_none()

        if user is None or not pw_hasher.verify(user.pw_hash, password):
            return jsonify({"error": "Invalid username or password"}), 401

        token = jwt.encode({
            'username': username,
            'user_id': user.id,
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
    return jsonify([dep.to_dict() for dep in departments])

@app.route('/severities', methods=['GET'])
@auth_required
def get_severities():
    severities = Severity.query.all()
    return jsonify([sev.to_dict() for sev in severities])

@app.route('/tickets', methods=['POST'])
@auth_required
def create_ticket():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    requestor_email = data.get('requestor_email')
    assigned_team_id = data.get('assigned_team_id')
    sev_id = data.get('sev_id')
    if not requestor_email or not assigned_team_id or not sev_id:
        return jsonify({"error": "Missing 'requestor_email', 'assigned_team_id', or 'sev_id' field"}), 400

    department = db.session.get(Department, assigned_team_id)
    if department is None:
        return jsonify({"error": f"No department with id {assigned_team_id}"}), 400

    severity = db.session.get(Severity, sev_id)
    if severity is None:
        return jsonify({"error": f"No severity with id {sev_id}"}), 400

    ticket = Ticket()
    ticket.requestor_email = requestor_email
    ticket.email_subject = data.get('email_subject')
    ticket.email_body = data.get('email_body')
    ticket.assigned_team_id = assigned_team_id
    ticket.sev_id = sev_id
    ticket.ai_explaination = data.get('ai_explaination')
    db.session.add(ticket)
    db.session.flush()

    _record_audit(ticket.id, "created")
    db.session.commit()

    _emit_ticket_created(ticket)
    return jsonify(ticket.to_dict()), 201

@app.route('/tickets', methods=['GET'])
@auth_required
def get_tickets():
    query = Ticket.query.filter(Ticket.resolved_at.is_(None))

    team = request.args.get('team')
    if team:
        query = query.join(Department, Ticket.assigned_team_id == Department.id).filter(Department.name == team)

    severity = request.args.get('severity')
    if severity:
        query = query.join(Severity, Ticket.sev_id == Severity.id).filter(Severity.name == severity)

    requestor_email = request.args.get('requestor_email')
    if requestor_email:
        query = query.filter(Ticket.requestor_email == requestor_email)

    replied = request.args.get('replied')
    if replied is not None:
        is_replied = replied.lower() == 'true'
        query = query.filter(Ticket.replied_at.isnot(None) if is_replied else Ticket.replied_at.is_(None))

    created_after = request.args.get('created_after')
    if created_after:
        parsed = _parse_datetime(created_after)
        if parsed is None:
            return jsonify({"error": "Invalid 'created_after', expected ISO 8601"}), 400
        query = query.filter(Ticket.created_at >= parsed)

    created_before = request.args.get('created_before')
    if created_before:
        parsed = _parse_datetime(created_before)
        if parsed is None:
            return jsonify({"error": "Invalid 'created_before', expected ISO 8601"}), 400
        query = query.filter(Ticket.created_at <= parsed)

    page = request.args.get('page', default=1, type=int)
    per_page = min(request.args.get('per_page', default=25, type=int), 100)

    total = query.count()
    tickets = query.order_by(Ticket.created_at.desc()) \
        .offset((page - 1) * per_page) \
        .limit(per_page) \
        .all()

    return jsonify({
        "tickets": [ticket.to_dict() for ticket in tickets],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": ceil(total / per_page) if per_page else 0
    })

@app.route('/tickets/<int:ticket_id>/team', methods=['PATCH'])
@auth_required
def update_ticket_team(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        return jsonify({"error": f"No ticket with id {ticket_id}"}), 404

    data = request.get_json(silent=True) or {}
    assigned_team_id = data.get('assigned_team_id')
    if not assigned_team_id:
        return jsonify({"error": "Missing 'assigned_team_id' field"}), 400

    department = db.session.get(Department, assigned_team_id)
    if department is None:
        return jsonify({"error": f"No department with id {assigned_team_id}"}), 400

    ticket.assigned_team_id = assigned_team_id
    _record_audit(ticket.id, f"assigned team changed to {department.name}")
    db.session.commit()

    _emit_ticket_updated(ticket)
    return jsonify(ticket.to_dict())

@app.route('/tickets/<int:ticket_id>/severity', methods=['PATCH'])
@auth_required
def update_ticket_severity(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        return jsonify({"error": f"No ticket with id {ticket_id}"}), 404

    data = request.get_json(silent=True) or {}
    sev_id = data.get('sev_id')
    if not sev_id:
        return jsonify({"error": "Missing 'sev_id' field"}), 400

    severity = db.session.get(Severity, sev_id)
    if severity is None:
        return jsonify({"error": f"No severity with id {sev_id}"}), 400

    ticket.sev_id = sev_id
    _record_audit(ticket.id, f"severity changed to {severity.name}")
    db.session.commit()

    _emit_ticket_updated(ticket)
    return jsonify(ticket.to_dict())

@app.route('/tickets/<int:ticket_id>/reply', methods=['PATCH'])
@auth_required
def reply_ticket(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        return jsonify({"error": f"No ticket with id {ticket_id}"}), 404
    if ticket.replied_at is not None:
        return jsonify({"error": "Ticket has already been replied to"}), 400

    # Use the DB's own clock (not Python's) so this always satisfies the
    # replied_at <= CURRENT_TIMESTAMP check: CURRENT_TIMESTAMP is frozen to
    # the transaction's start, and a Python-side timestamp taken after that
    # point would otherwise fall a few milliseconds later than it.
    ticket.replied_at = db.func.now()
    _record_audit(ticket.id, "replied")
    db.session.commit()

    _emit_ticket_updated(ticket)
    return jsonify(ticket.to_dict())

@app.route('/tickets/<int:ticket_id>/resolve', methods=['PATCH'])
@auth_required
def resolve_ticket(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        return jsonify({"error": f"No ticket with id {ticket_id}"}), 404
    if ticket.resolved_at is not None:
        return jsonify({"error": "Ticket has already been resolved"}), 400

    ticket.resolved_at = db.func.now()
    _record_audit(ticket.id, "resolved")
    db.session.commit()

    _emit_ticket_updated(ticket)
    return jsonify(ticket.to_dict())

@app.route('/tickets/<int:ticket_id>/audit', methods=['GET'])
@auth_required
def get_ticket_audit(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        return jsonify({"error": f"No ticket with id {ticket_id}"}), 404

    logs = db.session.execute(
        db.select(AuditLog, User.username)
        .join(User, AuditLog.created_by == User.id)
        .where(AuditLog.ticket_id == ticket_id)
        .order_by(AuditLog.created_at)
    ).all()

    return jsonify([
        {
            "id": log.id,
            "action": log.action,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "username": username
        }
        for log, username in logs
    ])

if __name__ == "__main__":
    socketio.run(app, host='localhost', port=4000)
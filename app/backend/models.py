from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    pw_hash = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username
        }

class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }

class Severity(db.Model):
    __tablename__ = "severities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    respond_time_hours = db.Column(db.Integer, nullable=False)
    resolve_time_hours = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "respond_time_hours": self.respond_time_hours,
            "resolve_time_hours": self.resolve_time_hours
        }

class Requester(db.Model):
    __tablename__ = "requesters"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(100))

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name
        }

class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    requestor_id = db.Column(db.Integer, db.ForeignKey("requesters.id"), nullable=False)
    email_subject = db.Column(db.String(255))
    email_body = db.Column(db.Text)
    assigned_team_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)
    sev_id = db.Column(db.Integer, db.ForeignKey("severities.id"), nullable=False)
    ai_explaination = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    replied_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)

    requestor = db.relationship("Requester")
    assigned_team = db.relationship("Department")
    severity = db.relationship("Severity")

    def to_dict(self):
        return {
            "id": self.id,
            "requestor_id": self.requestor_id,
            "email_subject": self.email_subject,
            "email_body": self.email_body,
            "assigned_team_id": self.assigned_team_id,
            "sev_id": self.sev_id,
            "ai_explaination": self.ai_explaination,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "replied_at": self.replied_at.isoformat() if self.replied_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }

class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    ticket = db.relationship("Ticket")
    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "action": self.action,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by
        }
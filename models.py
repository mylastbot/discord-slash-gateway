from datetime import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    
    # Discord related fields
    discord_id = db.Column(db.String(32), unique=True, nullable=True)
    games = db.relationship('FocusGame', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Server(db.Model):
    id = db.Column(db.String(32), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    member_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Server {self.name}>'

class Command(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    usage_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Command {self.name}>'

class CommandLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    command_name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.String(32), nullable=False)
    server_id = db.Column(db.String(32), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CommandLog {self.command_name} by {self.user_id}>'

class FocusGame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(32), nullable=False)
    user_db_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    score = db.Column(db.Integer, default=0)
    multiplier = db.Column(db.Float, default=1.0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<FocusGame {self.user_id}: {self.score}>'

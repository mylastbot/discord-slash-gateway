import os

class Config:
    """Configuration settings for the Flask application."""
    
    # Flask settings
    DEBUG = os.environ.get('DEBUG', 'True') == 'True'
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev_secret_key')
    
    # Database settings
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///bot.db')
    # Fix for postgres://... URLs for SQLAlchemy 1.4+
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Discord settings
    DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN', '')
    DISCORD_CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID', '')
    
    # Socket.IO settings
    SOCKETIO_PING_TIMEOUT = 60
    SOCKETIO_PING_INTERVAL = 25

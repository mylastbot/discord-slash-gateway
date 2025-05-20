import os

class Config:
    """Configuration settings for the Flask application."""
    
    # Flask settings
    DEBUG = os.environ.get('DEBUG', 'True') == 'True'
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev_secret_key')
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///bot.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Discord settings
    DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN', '')
    DISCORD_CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID', '')
    
    # Socket.IO settings
    SOCKETIO_PING_TIMEOUT = 60
    SOCKETIO_PING_INTERVAL = 25

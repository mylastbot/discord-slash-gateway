import os
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import threading
import time
from config import Config

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize database base class
class Base(DeclarativeBase):
    pass

# Initialize Flask app and SQLAlchemy
db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Load database configuration from Config object
connect_args = {}
if "neon.tech" in str(Config.SQLALCHEMY_DATABASE_URI):
    connect_args["sslmode"] = "require"

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "connect_args": connect_args
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SocketIO with longer ping timeout and interval
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25, async_mode='eventlet')

# Initialize database
db.init_app(app)

# Import models after db initialization
with app.app_context():
    import models
    from bot import start_bot, get_bot_status, bot_instance
    db.create_all()

# Discord bot thread
bot_thread = None

def start_bot_thread():
    global bot_thread
    if bot_thread is None or not bot_thread.is_alive():
        bot_thread = threading.Thread(target=start_bot)
        bot_thread.daemon = True
        bot_thread.start()
        logger.info("Bot thread started")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    status = get_bot_status()
    guilds = []
    if bot_instance and bot_instance.is_ready():
        guilds = [{"id": guild.id, "name": guild.name} for guild in bot_instance.guilds]
    
    # Get game statistics from the database
    with app.app_context():
        game_stats = models.FocusGame.query.order_by(models.FocusGame.score.desc()).limit(10).all()
        stats = [{"user": stat.user_id, "score": stat.score, "timestamp": stat.timestamp} for stat in game_stats]
    
    return render_template('dashboard.html', status=status, guilds=guilds, stats=stats)

@app.route('/api/bot/status')
def bot_status():
    return jsonify(get_bot_status())

# Socket.IO events
@socketio.on('connect')
def handle_connect():
    logger.debug('Client connected to WebSocket')
    emit('status_update', get_bot_status())

@socketio.on('disconnect')
def handle_disconnect():
    logger.debug('Client disconnected from WebSocket')

@socketio.on('request_status')
def handle_status_request():
    emit('status_update', get_bot_status())

# Start the bot thread when the app starts
# Using with_app_context since before_first_request is deprecated
@app.route('/initialize', methods=['GET'])
def initialize_route():
    start_bot_thread()
    return "Bot initialized"

# Initialize bot on startup
with app.app_context():
    start_bot_thread()

# WebSocket event to broadcast bot events
def broadcast_bot_event(event_type, data):
    socketio.emit('bot_event', {'type': event_type, 'data': data})

# Broadcast focus game updates
def broadcast_game_update(user_id, score):
    socketio.emit('game_update', {'user_id': user_id, 'score': score})

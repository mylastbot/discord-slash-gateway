import multiprocessing

# Gunicorn configuration for the Discord bot application

# Worker processes
workers = 1  # For WebSockets, single worker is often better for session handling
worker_class = 'eventlet'  # Use eventlet for WebSocket support

# Server socket settings
bind = '0.0.0.0:5000'
backlog = 2048

# Process naming
proc_name = 'discord_bot'

# Logging settings
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Timeout settings for WebSockets
timeout = 120
keepalive = 5
graceful_timeout = 10

# Server mechanics
daemon = False
reload = True
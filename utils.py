import os
import re
import json
import time
from datetime import datetime

def format_timestamp(timestamp):
    """Format a timestamp into a readable format."""
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    now = datetime.now()
    delta = now - timestamp
    
    if delta.days > 0:
        return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
    elif delta.seconds >= 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif delta.seconds >= 60:
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return f"{delta.seconds} second{'s' if delta.seconds != 1 else ''} ago"

def format_duration(seconds):
    """Format a duration in seconds to a readable format."""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)

def sanitize_input(text):
    """Sanitize user input to prevent code injection."""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>&;]', '', text)
    return text

def get_env_or_default(key, default=""):
    """Get an environment variable or return a default value."""
    return os.environ.get(key, default)

def is_valid_discord_id(discord_id):
    """Check if a string is a valid Discord ID."""
    if not discord_id:
        return False
    
    # Discord IDs are numeric strings
    return re.match(r'^\d{17,19}$', discord_id) is not None

def calculate_leaderboard_position(user_score, all_scores):
    """Calculate a user's position on the leaderboard."""
    if not user_score:
        return 0
    
    # Count how many scores are higher
    higher_scores = sum(1 for score in all_scores if score > user_score)
    return higher_scores + 1  # Add 1 to get 1-based ranking

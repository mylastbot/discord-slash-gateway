import os
import asyncio
import logging
import discord
from discord import app_commands
from discord.ext import commands, tasks
import threading
import time
from datetime import datetime, timedelta
import random
from models import Server, Command, CommandLog, FocusGame
from app import db

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Global variables
bot_status = {
    "online": False,
    "guilds": 0,
    "uptime": 0,
    "commands_used": 0,
    "last_command": None,
    "start_time": None
}

bot_instance = None

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='/', intents=intents)
        self.start_time = datetime.now()
        self.focus_games = {}
        self.synced = False

    async def setup_hook(self):
        # Sync commands with Discord
        if not self.synced:
            await self.tree.sync()
            self.synced = True
            logger.info("Slash commands synced")

    async def on_ready(self):
        global bot_status
        bot_status["online"] = True
        bot_status["start_time"] = self.start_time.isoformat()
        bot_status["guilds"] = len(self.guilds)
        logger.info(f"Bot {self.user.name} is ready!")
        
        # Start tasks
        self.update_status.start()
        self.update_focus_games.start()
        
        # Update server information in database - using app context
        from app import app
        with app.app_context():
            for guild in self.guilds:
                server = Server.query.get(str(guild.id))
                if not server:
                    server = Server(id=str(guild.id), name=guild.name, member_count=guild.member_count)
                    db.session.add(server)
                else:
                    server.name = guild.name
                    server.member_count = guild.member_count
            db.session.commit()

    async def on_guild_join(self, guild):
        global bot_status
        logger.info(f"Joined new guild: {guild.name}")
        bot_status["guilds"] = len(self.guilds)
        
        # Add server to database
        server = Server(id=str(guild.id), name=guild.name, member_count=guild.member_count)
        db.session.add(server)
        db.session.commit()

    async def on_guild_remove(self, guild):
        global bot_status
        logger.info(f"Left guild: {guild.name}")
        bot_status["guilds"] = len(self.guilds)
        
        # Update server status in database
        server = Server.query.get(str(guild.id))
        if server:
            db.session.delete(server)
            db.session.commit()

    async def on_app_command_completion(self, interaction, command):
        global bot_status
        bot_status["commands_used"] += 1
        bot_status["last_command"] = {
            "name": command.name,
            "user": interaction.user.name,
            "time": datetime.now().isoformat()
        }
        
        # Log command in database
        cmd = Command.query.filter_by(name=command.name).first()
        if not cmd:
            cmd = Command(name=command.name, description=command.description, usage_count=1)
            db.session.add(cmd)
        else:
            cmd.usage_count += 1
        
        log = CommandLog(
            command_name=command.name,
            user_id=str(interaction.user.id),
            server_id=str(interaction.guild_id) if interaction.guild else None
        )
        db.session.add(log)
        db.session.commit()

    @tasks.loop(seconds=5)
    async def update_status(self):
        global bot_status
        # Update uptime
        uptime = datetime.now() - self.start_time
        bot_status["uptime"] = str(uptime).split('.')[0]  # Format as HH:MM:SS
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servers | /help"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)

    @tasks.loop(minutes=2)
    async def update_focus_games(self):
        """Update focus game scores periodically"""
        current_time = datetime.now()
        
        for user_id, game_data in self.focus_games.items():
            if game_data["active"]:
                # Calculate time difference
                time_diff = (current_time - game_data["last_update"]).total_seconds() / 60
                
                # Add points based on time and multiplier
                points_to_add = int(time_diff * game_data["multiplier"])
                if points_to_add > 0:
                    game_data["score"] += points_to_add
                    game_data["last_update"] = current_time
                    
                    # Update in database
                    game = FocusGame.query.filter_by(user_id=user_id).first()
                    if game:
                        game.score = game_data["score"]
                        game.multiplier = game_data["multiplier"]
                        game.last_updated = current_time
                        db.session.commit()
                    
                    # If game has been running for more than 30 minutes, add a bonus
                    session_duration = (current_time - game_data["session_start"]).total_seconds() / 60
                    if session_duration > 30 and random.random() < 0.15:  # 15% chance
                        game_data["multiplier"] += 0.1
                        if game:
                            game.multiplier = game_data["multiplier"]
                            db.session.commit()
                        
                        # Try to notify the user if they have a DM channel
                        user = self.get_user(int(user_id))
                        if user:
                            try:
                                await user.send(f"🎯 Focus boost! Your multiplier is now {game_data['multiplier']:.1f}x")
                            except:
                                pass  # Ignore if we can't send DM

# Register slash commands
def setup_commands(bot):
    @bot.tree.command(name="ping", description="Check if the bot is online")
    async def ping(interaction: discord.Interaction):
        await interaction.response.send_message(f"Pong! Bot latency: {round(bot.latency * 1000)}ms")

    @bot.tree.command(name="help", description="Show available commands")
    async def help_command(interaction: discord.Interaction):
        embed = discord.Embed(
            title="Discord Bot Help",
            description="Here are the available commands:",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="/ping", value="Check if the bot is online", inline=False)
        embed.add_field(name="/help", value="Show this help message", inline=False)
        embed.add_field(name="/focus", value="Start a focus session to earn points", inline=False)
        embed.add_field(name="/unfocus", value="End your focus session", inline=False)
        embed.add_field(name="/stats", value="Show your focus stats", inline=False)
        embed.add_field(name="/leaderboard", value="Show the focus leaderboard", inline=False)
        
        embed.set_footer(text="Focus multiplier game - stay focused to earn more points!")
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="focus", description="Start a focus session to earn points")
    async def focus(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        # Check if already in focus mode
        if user_id in bot.focus_games and bot.focus_games[user_id]["active"]:
            await interaction.response.send_message("You're already in focus mode! Use `/unfocus` to end your session.")
            return
        
        current_time = datetime.now()
        
        # Get or create game record
        game = FocusGame.query.filter_by(user_id=user_id).first()
        if not game:
            game = FocusGame(user_id=user_id)
            db.session.add(game)
            db.session.commit()
            score = 0
            multiplier = 1.0
        else:
            score = game.score
            multiplier = game.multiplier
        
        # Set up focus session
        bot.focus_games[user_id] = {
            "active": True,
            "score": score,
            "multiplier": multiplier,
            "session_start": current_time,
            "last_update": current_time
        }
        
        embed = discord.Embed(
            title="Focus Mode Activated! 🎯",
            description="Your focus session has started. Stay focused to earn points!",
            color=discord.Color.green()
        )
        embed.add_field(name="Current Score", value=str(score), inline=True)
        embed.add_field(name="Multiplier", value=f"{multiplier:.1f}x", inline=True)
        embed.add_field(name="How it works", value="Points accumulate while you focus. The longer you focus, the more points you earn!", inline=False)
        embed.set_footer(text="Use /unfocus to end your session")
        
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="unfocus", description="End your focus session")
    async def unfocus(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        # Check if in focus mode
        if user_id not in bot.focus_games or not bot.focus_games[user_id]["active"]:
            await interaction.response.send_message("You're not in focus mode! Use `/focus` to start a session.")
            return
        
        # Calculate final score
        current_time = datetime.now()
        game_data = bot.focus_games[user_id]
        time_diff = (current_time - game_data["last_update"]).total_seconds() / 60
        points_to_add = int(time_diff * game_data["multiplier"])
        game_data["score"] += points_to_add
        game_data["active"] = False
        
        # Session duration
        duration = current_time - game_data["session_start"]
        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        
        # Update database
        game = FocusGame.query.filter_by(user_id=user_id).first()
        if game:
            game.score = game_data["score"]
            game.last_updated = current_time
            db.session.commit()
        
        embed = discord.Embed(
            title="Focus Session Complete! 🎉",
            description="Your focus session has ended.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Final Score", value=str(game_data["score"]), inline=True)
        embed.add_field(name="Session Duration", value=duration_str, inline=True)
        embed.add_field(name="Points Earned", value=str(points_to_add), inline=True)
        embed.set_footer(text="Start a new session with /focus")
        
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="stats", description="Show your focus stats")
    async def stats(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        # Get game data
        game = FocusGame.query.filter_by(user_id=user_id).first()
        
        if not game:
            await interaction.response.send_message("You haven't started any focus sessions yet! Use `/focus` to begin.")
            return
        
        # Current session data
        current_session = None
        if user_id in bot.focus_games and bot.focus_games[user_id]["active"]:
            current_time = datetime.now()
            game_data = bot.focus_games[user_id]
            duration = current_time - game_data["session_start"]
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
            current_session = {
                "active": True,
                "duration": duration_str,
                "multiplier": game_data["multiplier"]
            }
        
        embed = discord.Embed(
            title=f"{interaction.user.name}'s Focus Stats",
            color=discord.Color.purple()
        )
        embed.add_field(name="Total Score", value=str(game.score), inline=True)
        embed.add_field(name="Current Multiplier", value=f"{game.multiplier:.1f}x", inline=True)
        
        if current_session:
            embed.add_field(name="Status", value="Currently focusing! 🎯", inline=False)
            embed.add_field(name="Session Duration", value=current_session["duration"], inline=True)
        else:
            embed.add_field(name="Status", value="Not currently focusing", inline=False)
            embed.add_field(name="Last Session", value=game.last_updated.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        
        # Get rank
        rank = db.session.query(FocusGame).filter(FocusGame.score > game.score).count() + 1
        embed.add_field(name="Global Rank", value=f"#{rank}", inline=True)
        
        embed.set_footer(text="Focus more to increase your score and multiplier!")
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="leaderboard", description="Show the focus leaderboard")
    async def leaderboard(interaction: discord.Interaction):
        # Get top 10 players
        top_players = FocusGame.query.order_by(FocusGame.score.desc()).limit(10).all()
        
        if not top_players:
            await interaction.response.send_message("No focus game data available yet!")
            return
        
        embed = discord.Embed(
            title="🏆 Focus Leaderboard 🏆",
            description="Top focus warriors:",
            color=discord.Color.gold()
        )
        
        for idx, player in enumerate(top_players):
            # Try to get username
            try:
                user = await bot.fetch_user(int(player.user_id))
                username = user.name
            except:
                username = f"User {player.user_id}"
            
            # Add medal emoji for top 3
            medal = ""
            if idx == 0:
                medal = "🥇 "
            elif idx == 1:
                medal = "🥈 "
            elif idx == 2:
                medal = "🥉 "
            
            embed.add_field(
                name=f"{medal}#{idx+1}: {username}",
                value=f"Score: {player.score} | Multiplier: {player.multiplier:.1f}x",
                inline=False
            )
        
        embed.set_footer(text="Use /focus to start climbing the ranks!")
        await interaction.response.send_message(embed=embed)

# Discord bot instance and running
def create_bot():
    global bot_instance
    bot_instance = DiscordBot()
    setup_commands(bot_instance)
    return bot_instance

def start_bot():
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    if not token:
        logger.error("No Discord bot token found in environment variables!")
        bot_status["online"] = False
        return
    
    bot = create_bot()
    
    try:
        logger.info("Starting Discord bot...")
        bot.run(token)
    except Exception as e:
        logger.error(f"Error starting Discord bot: {e}")
        bot_status["online"] = False

def get_bot_status():
    global bot_status
    # Add additional status info if bot is running
    if bot_instance and bot_instance.is_ready():
        bot_status["online"] = True
        bot_status["guilds"] = len(bot_instance.guilds)
        
        if bot_status["start_time"]:
            start_time = datetime.fromisoformat(bot_status["start_time"])
            uptime = datetime.now() - start_time
            bot_status["uptime"] = str(uptime).split('.')[0]  # Format as HH:MM:SS
        
        # Get active users
        active_users = sum(1 for game in bot_instance.focus_games.values() if game["active"])
        bot_status["active_users"] = active_users
        
        # Get total focus score across all users
        total_score = sum(game["score"] for game in bot_instance.focus_games.values())
        bot_status["total_focus_score"] = total_score
    
    return bot_status

import os
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import aiohttp
import asyncio
import datetime
import pytz
import re
from dateutil import parser
import traceback
import random

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('urmom-bot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
OMDB_API_KEY = os.getenv('OMDB_API_KEY')

# Bot configuration
class BotConfig:
    # Paths
    GIF_DIR = 'gifs'
    URMOM_GIF = f"{GIF_DIR}/ur-mom.gif"
    ALOT_GIF = f"{GIF_DIR}/alot.gif"
    
    # Response triggers
    ALOT_EXCEPTIONS = ['zealot', 'zealots', 'zealotry']
    
    # Feature toggles
    USE_REACTIONS = True
    USE_GIF_RESPONSES = True
    
    # API endpoints
    OMDB_API_URL = "http://www.omdbapi.com/"
    NHL_API_BASE = "https://api-web.nhle.com/v1"
    NHL_STATS_API = "https://api.nhle.com/stats/rest/en"
    
    # Panthers team ID and abbreviation
    PANTHERS_TEAM_ID = 13
    PANTHERS_TEAM_ABBREV = "FLA"
    
    # Timezone for reminders
    TIMEZONE = pytz.timezone('US/Eastern')
    
    # Reminder storage
    REMINDER_CHECK_INTERVAL = 10  # seconds
    
    # Panthers player quotes (can be expanded)
    PANTHERS_QUOTES = [
        "\"We're just taking it one game at a time.\" - Aleksander Barkov",
        "\"The fans here are incredible. We feed off their energy.\" - Matthew Tkachuk",
        "\"This team has something special. We believe in each other.\" - Aaron Ekblad",
        "\"Florida is a hockey state now, and we're proud to represent it.\" - Sam Reinhart",
        "\"We play for each other and for this city.\" - Carter Verhaeghe",
        "\"The culture here is different. We're all pulling in the same direction.\" - Gustav Forsling",
        "\"Every shift matters. Every game matters.\" - Brandon Montour",
        "\"We want to bring a Cup to South Florida.\" - Sergei Bobrovsky",
        "\"The chemistry on this team is unreal.\" - Sam Bennett",
        "\"We're not done yet. We want more.\" - Paul Maurice (Head Coach)"
    ]

class Reminder:
    """Class to represent a reminder"""
    def __init__(self, user_id, channel_id, message, time, reference_msg=None, reference_author=None):
        self.user_id = user_id
        self.channel_id = channel_id
        self.message = message
        self.time = time
        self.reference_msg = reference_msg
        self.reference_author = reference_author

class ReminderManager:
    """Class to manage reminders"""
    def __init__(self, bot):
        self.bot = bot
        self.reminders = []
        self.est_timezone = pytz.timezone('US/Eastern')
        
    def add_reminder(self, reminder):
        """Add a new reminder"""
        self.reminders.append(reminder)
        # Sort reminders by time
        self.reminders.sort(key=lambda r: r.time)
        
    async def check_reminders(self):
        """Check for due reminders"""
        now = datetime.datetime.now(pytz.utc)
        due_reminders = [r for r in self.reminders if r.time <= now]
        
        for reminder in due_reminders:
            self.reminders.remove(reminder)
            await self.send_reminder(reminder)
    
    async def send_reminder(self, reminder):
        """Send a reminder to the user"""
        try:
            channel = self.bot.get_channel(reminder.channel_id)
            if not channel:
                channel = await self.bot.fetch_channel(reminder.channel_id)
                
            user_mention = f"<@{reminder.user_id}>"
            
            if reminder.reference_msg and reminder.reference_author:
                ref_author_mention = f"<@{reminder.reference_author}>"
                message = f"{user_mention}, you asked to be reminded about this message from {ref_author_mention}:\n\n> {reminder.reference_msg}\n\n{reminder.message}"
            else:
                message = f"{user_mention}, you asked me to remind you: {reminder.message}"
                
            await channel.send(message)
            
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")
    
    def parse_time(self, time_str):
        """Parse a time string into a datetime object"""
        now = datetime.datetime.now(self.est_timezone)
        logger.info(f"Parsing time: {time_str} (Current time EST: {now})")
        
        # First try to parse as a relative time
        relative_time = self._parse_relative_time(time_str, now)
        if relative_time:
            logger.info(f"Parsed as relative time: {relative_time}")
            return relative_time
            
        # Then try to parse as an absolute time
        absolute_time = self._parse_absolute_time(time_str, now)
        if absolute_time:
            logger.info(f"Parsed as absolute time: {absolute_time}")
            return absolute_time
            
        logger.warning(f"Failed to parse time: {time_str}")
        return None
        
    def _parse_relative_time(self, time_str, now):
        """Parse relative time expressions like '5 minutes' or '2 hours'"""
        # Handle direct number followed by time unit
        time_units = {
            "sec": "seconds", "secs": "seconds", "second": "seconds", "seconds": "seconds",
            "min": "minutes", "mins": "minutes", "minute": "minutes", "minutes": "minutes",
            "hr": "hours", "hrs": "hours", "hour": "hours", "hours": "hours",
            "day": "days", "days": "days",
            "week": "weeks", "weeks": "weeks"
        }
        
        # First pattern: number followed by unit (with optional 'in')
        # Examples: "5 minutes", "in 2 hours", "3 days"
        pattern = r'(?:in\s+)?(\d+)\s+([a-zA-Z]+)'
        match = re.match(pattern, time_str.lower().strip())
        
        if match:
            amount = int(match.group(1))
            unit_raw = match.group(2).lower().strip()
            
            # Handle plural/singular and abbreviations
            unit = time_units.get(unit_raw)
            
            if unit:
                # Create timedelta based on unit
                delta_args = {unit: amount}
                delta = datetime.timedelta(**delta_args)
                return now + delta
        
        return None
        
    def _parse_absolute_time(self, time_str, now):
        """Parse absolute time expressions like 'at 5pm' or '14:30'"""
        try:
            # Try to parse with dateutil's parser
            parsed_time = parser.parse(time_str, fuzzy=True)
            logger.info(f"Parser result: {parsed_time}, type: {type(parsed_time)}")
            
            # Make sure it's a datetime object
            if not isinstance(parsed_time, datetime.datetime):
                logger.warning(f"Parsed time is not a datetime object: {parsed_time}")
                return None
            
            # If only time is specified (no date), use today's date
            if parsed_time.year == 1900:
                logger.info("Detected time-only value, combining with today's date")
                # Combine current date with parsed time
                parsed_time = datetime.datetime.combine(
                    now.date(),
                    parsed_time.time()
                )
                # Add timezone info
                parsed_time = self.est_timezone.localize(parsed_time)
                
                # If the parsed time is earlier than now, assume tomorrow
                if parsed_time < now:
                    logger.info("Time is in the past, assuming tomorrow")
                    parsed_time = parsed_time + datetime.timedelta(days=1)
            else:
                # If it already has a date, just add timezone
                if parsed_time.tzinfo is None:
                    logger.info("Adding timezone info to datetime")
                    parsed_time = self.est_timezone.localize(parsed_time)
            
            return parsed_time
        
        except (ValueError, parser.ParserError) as e:
            logger.error(f"Error parsing absolute time: {e}")
            return None

class PanthersManager:
    """Class to manage Panthers NHL data"""
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        
    async def get_team_info(self):
        """Get basic Panthers team information"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get team stats and standings
                url = f"{self.config.NHL_API_BASE}/standings/now"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Find Panthers in standings
                        for team in data.get('standings', []):
                            if team.get('teamAbbrev', {}).get('default') == 'FLA':
                                return team
        except Exception as e:
            logger.error(f"Error fetching Panthers team info: {e}")
            return None
        
    async def get_current_game(self):
        """Get current Panthers game if one is active or scheduled for today"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get today's schedule
                today = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d')
                url = f"{self.config.NHL_API_BASE}/schedule/{today}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Look for Panthers game
                        for game_week in data.get('gameWeek', []):
                            for game in game_week.get('games', []):
                                home_team = game.get('homeTeam', {})
                                away_team = game.get('awayTeam', {})
                                if (home_team.get('id') == self.config.PANTHERS_TEAM_ID or 
                                    away_team.get('id') == self.config.PANTHERS_TEAM_ID):
                                    return game
                
                # Fallback: check team schedule for today's game
                url = f"{self.config.NHL_API_BASE}/club-schedule/{self.config.PANTHERS_TEAM_ABBREV}/week/now"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        games = data.get('games', [])
                        today_utc = datetime.datetime.now(pytz.utc).date()
                        
                        for game in games:
                            game_date_str = game.get('gameDate', '')
                            if game_date_str:
                                try:
                                    if 'T' in game_date_str:
                                        game_date = datetime.datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
                                    else:
                                        date_part = datetime.datetime.strptime(game_date_str, '%Y-%m-%d')
                                        game_date = pytz.utc.localize(date_part)
                                    
                                    # Check if game is today
                                    if game_date.date() == today_utc:
                                        return game
                                except ValueError:
                                    continue
                        
        except Exception as e:
            logger.error(f"Error fetching current Panthers game: {e}")
            
        return None
            
    async def get_next_game(self):
        """Get next Panthers game"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get team schedule using team abbreviation
                url = f"{self.config.NHL_API_BASE}/club-schedule-season/{self.config.PANTHERS_TEAM_ABBREV}/now"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        games = data.get('games', [])
                        now_utc = datetime.datetime.now(pytz.utc)
                        
                        # Find next game
                        for game in games:
                            try:
                                game_date_str = game.get('gameDate', '')
                                if not game_date_str:
                                    continue
                                    
                                game_date = datetime.datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
                                if game_date > now_utc:
                                    return game
                            except (ValueError, TypeError) as e:
                                logger.warning(f"Error parsing game date: {e}")
                                continue
                    else:
                        logger.warning(f"Failed to fetch next game: {response.status}")
        except Exception as e:
            logger.error(f"Error fetching next Panthers game: {e}")
            
        return None
            
    async def get_recent_games(self, limit=5):
        """Get recent Panthers games"""
        try:
            async with aiohttp.ClientSession() as session:
                # Use the correct team abbreviation endpoint
                url = f"{self.config.NHL_API_BASE}/club-schedule-season/{self.config.PANTHERS_TEAM_ABBREV}/now"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        games = data.get('games', [])
                        now_utc = datetime.datetime.now(pytz.utc)
                        
                        # Get recent completed games
                        recent_games = []
                        for game in reversed(games):  # Start from most recent
                            try:
                                game_date_str = game.get('gameDate', '')
                                game_state = game.get('gameState', '')
                                
                                if not game_date_str:
                                    continue
                                
                                # Parse the ISO date string - handle different formats
                                try:
                                    if 'T' in game_date_str:
                                        # Full ISO format
                                        game_date = datetime.datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
                                    else:
                                        # Date only format - assume midnight UTC
                                        date_part = datetime.datetime.strptime(game_date_str, '%Y-%m-%d')
                                        game_date = pytz.utc.localize(date_part)
                                except ValueError:
                                    continue
                                
                                # Include completed games - expand the list of final states
                                final_states = ['OFF', 'FINAL', 'OVER', 'FINAL_OT', 'FINAL_SO']
                                if game_date < now_utc and game_state in final_states:
                                    recent_games.append(game)
                                    if len(recent_games) >= limit:
                                        break
                                    
                            except Exception as e:
                                logger.warning(f"Error processing game {game.get('id', 'unknown')}: {e}")
                                continue
                        
                        if recent_games:
                            return recent_games
                    else:
                        logger.warning(f"Failed to fetch games for team {self.config.PANTHERS_TEAM_ABBREV}: {response.status}")
                
                # Fallback: try with specific season format
                url = f"{self.config.NHL_API_BASE}/club-schedule-season/{self.config.PANTHERS_TEAM_ABBREV}/20242025"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        games = data.get('games', [])
                        now_utc = datetime.datetime.now(pytz.utc)
                        
                        recent_games = []
                        for game in reversed(games):
                            try:
                                game_date_str = game.get('gameDate', '')
                                game_state = game.get('gameState', '')
                                
                                if not game_date_str:
                                    continue
                                
                                # Parse the ISO date string
                                try:
                                    if 'T' in game_date_str:
                                        game_date = datetime.datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
                                    else:
                                        date_part = datetime.datetime.strptime(game_date_str, '%Y-%m-%d')
                                        game_date = pytz.utc.localize(date_part)
                                except ValueError:
                                    continue
                                
                                final_states = ['OFF', 'FINAL', 'OVER', 'FINAL_OT', 'FINAL_SO', 'FINAL_OTHER']
                                if game_date < now_utc and game_state in final_states:
                                    recent_games.append(game)
                                    if len(recent_games) >= limit:
                                        break
                            except Exception as e:
                                logger.warning(f"Error parsing game: {e}")
                                continue
                        
                        if recent_games:
                            return recent_games
                    else:
                        logger.warning(f"Failed to fetch 2024-2025 season schedule: {response.status}")
                
                # Final fallback: try monthly schedule
                url = f"{self.config.NHL_API_BASE}/club-schedule/{self.config.PANTHERS_TEAM_ABBREV}/month/now"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        games = data.get('games', [])
                        now_utc = datetime.datetime.now(pytz.utc)
                        
                        recent_games = []
                        for game in reversed(games):
                            try:
                                game_date_str = game.get('gameDate', '')
                                game_state = game.get('gameState', '')
                                
                                if not game_date_str:
                                    continue
                                
                                try:
                                    if 'T' in game_date_str:
                                        game_date = datetime.datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
                                    else:
                                        date_part = datetime.datetime.strptime(game_date_str, '%Y-%m-%d')
                                        game_date = pytz.utc.localize(date_part)
                                except ValueError:
                                    continue
                                
                                final_states = ['OFF', 'FINAL', 'OVER', 'FINAL_OT', 'FINAL_SO', 'FINAL_OTHER']
                                if game_date < now_utc and game_state in final_states:
                                    recent_games.append(game)
                                    if len(recent_games) >= limit:
                                        break
                            except Exception as e:
                                logger.warning(f"Error parsing game: {e}")
                                continue
                        
                        return recent_games
                    else:
                        logger.warning(f"Failed to fetch monthly schedule: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error fetching recent Panthers games: {e}")
            
        return []

class UrmomBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.config = BotConfig()
        self.reminder_manager = ReminderManager(self)
        self.panthers_manager = PanthersManager(self)
        self.movie_selections = {}
        
        # Register commands and events
        self.add_commands()
        
        # Start reminder check loop
        self.reminder_check_task = None
    
    async def setup_hook(self):
        """Set up background tasks when the bot is ready"""
        self.reminder_check_task = self.loop.create_task(self.reminder_check_loop())
    
    async def reminder_check_loop(self):
        """Background task to check for due reminders"""
        await self.wait_until_ready()
        while not self.is_closed():
            await self.reminder_manager.check_reminders()
            await asyncio.sleep(self.config.REMINDER_CHECK_INTERVAL)
    
    def add_commands(self):
        @self.command(name='mom')
        async def mom_command(ctx):
            """Command to respond to !mom"""
            await ctx.send('what...?')
            
        @self.command(name='cats')
        async def cats_command(ctx, subcommand=None):
            """Panthers team information"""
            if subcommand is None:
                await self.handle_cats_main(ctx)
            elif subcommand.lower() == 'quote':
                await self.handle_cats_quote(ctx)
            elif subcommand.lower() == 'game':
                await self.handle_cats_game(ctx)
            elif subcommand.lower() == 'recent':
                await self.handle_cats_recent(ctx)
            elif subcommand.lower() == 'help':
                await self.handle_cats_help(ctx)
            else:
                await ctx.send("Unknown cats command. Use `!cats help` for available options.")
        
        async def handle_cats_main(self, ctx):
            """Main cats command - team overview"""
            await ctx.send("🐾 Fetching Panthers info...")
            
            # Get team info and current/next game
            team_info = await self.panthers_manager.get_team_info()
            current_game = await self.panthers_manager.get_current_game()
            
            embed = discord.Embed(
                title="🐾 Florida Panthers",
                color=0xC8102E,  # Panthers red
                timestamp=datetime.datetime.now()
            )
            
            if team_info:
                record = f"{team_info.get('wins', 0)}-{team_info.get('losses', 0)}-{team_info.get('otLosses', 0)}"
                points = team_info.get('points', 0)
                games_played = team_info.get('gamesPlayed', 0)
                
                embed.add_field(name="Record", value=record, inline=True)
                embed.add_field(name="Points", value=f"{points} pts", inline=True)
                embed.add_field(name="Games Played", value=games_played, inline=True)
                
                # Division/Conference standing
                division_rank = team_info.get('divisionSequence', 'N/A')
                conference_rank = team_info.get('conferenceSequence', 'N/A')
                league_rank = team_info.get('leagueSequence', 'N/A')
                
                embed.add_field(name="Atlantic Division", value=f"#{division_rank}", inline=True)
                embed.add_field(name="Eastern Conference", value=f"#{conference_rank}", inline=True)
                embed.add_field(name="League", value=f"#{league_rank}", inline=True)
            
            # Current game info
            if current_game:
                home_team = current_game.get('homeTeam', {})
                away_team = current_game.get('awayTeam', {})
                game_state = current_game.get('gameState', '')
                
                if game_state in ['LIVE', 'CRIT']:
                    home_score = home_team.get('score', 0)
                    away_score = away_team.get('score', 0)
                    period = current_game.get('periodDescriptor', {}).get('number', '')
                    time_remaining = current_game.get('clock', {}).get('timeRemaining', '')
                    
                    game_info = f"🔴 **LIVE GAME**\n"
                    game_info += f"{away_team.get('abbrev', 'AWAY')} {away_score} - {home_score} {home_team.get('abbrev', 'HOME')}\n"
                    game_info += f"Period {period} - {time_remaining}"
                    
                    embed.add_field(name="Current Game", value=game_info, inline=False)
                else:
                    # Game today but not started
                    game_time = current_game.get('startTimeUTC', '')
                    if game_time:
                        game_dt = datetime.datetime.fromisoformat(game_time.replace('Z', '+00:00'))
                        est_time = game_dt.astimezone(pytz.timezone('US/Eastern'))
                        formatted_time = est_time.strftime('%I:%M %p ET')
                        
                        opponent = away_team.get('abbrev', '') if home_team.get('id') == self.config.PANTHERS_TEAM_ID else home_team.get('abbrev', '')
                        location = "HOME" if home_team.get('id') == self.config.PANTHERS_TEAM_ID else "AWAY"
                        
                        game_info = f"🏒 **TODAY'S GAME**\n"
                        game_info += f"vs {opponent} ({location})\n"
                        game_info += f"{formatted_time}"
                        
                        embed.add_field(name="Today's Game", value=game_info, inline=False)
            else:
                # Get next game
                next_game = await self.panthers_manager.get_next_game()
                if next_game:
                    game_date = datetime.datetime.fromisoformat(next_game.get('gameDate', '').replace('Z', '+00:00'))
                    est_date = game_date.astimezone(pytz.timezone('US/Eastern'))
                    formatted_date = est_date.strftime('%a, %b %d at %I:%M %p ET')
                    
                    home_team = next_game.get('homeTeam', {})
                    away_team = next_game.get('awayTeam', {})
                    opponent = away_team.get('abbrev', '') if home_team.get('id') == self.config.PANTHERS_TEAM_ID else home_team.get('abbrev', '')
                    location = "HOME" if home_team.get('id') == self.config.PANTHERS_TEAM_ID else "AWAY"
                    venue = next_game.get('venue', {}).get('default', '')
                    
                    game_info = f"🗓️ **NEXT GAME**\n"
                    game_info += f"vs {opponent} ({location})\n"
                    game_info += f"{formatted_date}\n"
                    if venue:
                        game_info += f"📍 {venue}"
                    
                    embed.add_field(name="Next Game", value=game_info, inline=False)
            
            embed.add_field(
                name="Commands", 
                value="`!cats quote` - Random player quote\n`!cats game` - Detailed game info\n`!cats recent` - Recent games\n`!cats help` - All commands", 
                inline=False
            )
            embed.set_footer(text="Go Panthers! 🐾")
            
            await ctx.send(embed=embed)
        
        async def handle_cats_quote(self, ctx):
            """Random Panthers quote"""
            quote = random.choice(self.config.PANTHERS_QUOTES)
            embed = discord.Embed(
                title="🐾 Panthers Quote",
                description=quote,
                color=0xC8102E
            )
            await ctx.send(embed=embed)
        
        async def handle_cats_game(self, ctx):
            """Detailed game information"""
            current_game = await self.panthers_manager.get_current_game()
            
            if not current_game:
                next_game = await self.panthers_manager.get_next_game()
                if next_game:
                    embed = discord.Embed(
                        title="🏒 Next Panthers Game",
                        color=0xC8102E
                    )
                    
                    game_date_str = next_game.get('gameDate', '')
                    if game_date_str:
                        try:
                            if 'T' in game_date_str:
                                game_date = datetime.datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
                            else:
                                date_part = datetime.datetime.strptime(game_date_str, '%Y-%m-%d')
                                game_date = pytz.utc.localize(date_part)
                            
                            est_date = game_date.astimezone(pytz.timezone('US/Eastern'))
                            formatted_date = est_date.strftime('%A, %B %d at %I:%M %p ET')
                            formatted_date_short = est_date.strftime('%B %d, %Y')
                        except ValueError:
                            formatted_date = "Date TBD"
                            formatted_date_short = "TBD"
                    else:
                        formatted_date = "Date TBD"
                        formatted_date_short = "TBD"
                    
                    home_team = next_game.get('homeTeam', {})
                    away_team = next_game.get('awayTeam', {})
                    opponent = away_team.get('abbrev', '') if home_team.get('id') == self.config.PANTHERS_TEAM_ID else home_team.get('abbrev', '')
                    location = "🏠 HOME" if home_team.get('id') == self.config.PANTHERS_TEAM_ID else "✈️ AWAY"
                    venue = next_game.get('venue', {}).get('default', '')
                    
                    embed.add_field(name="Date", value=formatted_date_short, inline=True)
                    embed.add_field(name="Opponent", value=f"vs {opponent}", inline=True)
                    embed.add_field(name="Location", value=location, inline=True)
                    embed.add_field(name="Game Time", value=formatted_date, inline=False)
                    if venue:
                        embed.add_field(name="Venue", value=f"📍 {venue}", inline=False)
                    
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("No upcoming games found!")
                return
            
            # Current/today's game details
            embed = discord.Embed(
                title="🏒 Panthers Game",
                color=0xC8102E
            )
            
            home_team = current_game.get('homeTeam', {})
            away_team = current_game.get('awayTeam', {})
            game_state = current_game.get('gameState', '')
            
            # Basic game info
            opponent = away_team.get('abbrev', '') if home_team.get('id') == self.config.PANTHERS_TEAM_ID else home_team.get('abbrev', '')
            location = "🏠 HOME" if home_team.get('id') == self.config.PANTHERS_TEAM_ID else "✈️ AWAY"
            
            # Add game date with safe parsing
            game_date_str = current_game.get('gameDate', '')
            if game_date_str:
                try:
                    if 'T' in game_date_str:
                        game_date = datetime.datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
                    else:
                        date_part = datetime.datetime.strptime(game_date_str, '%Y-%m-%d')
                        game_date = pytz.utc.localize(date_part)
                    
                    est_date = game_date.astimezone(pytz.timezone('US/Eastern'))
                    formatted_date_short = est_date.strftime('%B %d, %Y')
                except ValueError:
                    formatted_date_short = "TBD"
            else:
                formatted_date_short = "TBD"
            
            embed.add_field(name="Date", value=formatted_date_short, inline=True)
            embed.add_field(name="Opponent", value=f"vs {opponent}", inline=True)
            embed.add_field(name="Location", value=location, inline=True)
            
            if game_state in ['LIVE', 'CRIT']:
                home_score = home_team.get('score', 0)
                away_score = away_team.get('score', 0)
                period = current_game.get('periodDescriptor', {}).get('number', '')
                time_remaining = current_game.get('clock', {}).get('timeRemaining', '')
                
                score_display = f"{away_team.get('abbrev', 'AWAY')} {away_score} - {home_score} {home_team.get('abbrev', 'HOME')}"
                embed.add_field(name="🔴 LIVE SCORE", value=score_display, inline=False)
                embed.add_field(name="Period", value=period, inline=True)
                embed.add_field(name="Time Remaining", value=time_remaining, inline=True)
                
                # Add shots if available
                home_shots = home_team.get('sog', 0)
                away_shots = away_team.get('sog', 0)
                if home_shots or away_shots:
                    shots_display = f"{away_team.get('abbrev', 'AWAY')} {away_shots} - {home_shots} {home_team.get('abbrev', 'HOME')}"
                    embed.add_field(name="Shots on Goal", value=shots_display, inline=False)
            else:
                # Pre-game
                game_time = current_game.get('startTimeUTC', '')
                if game_time:
                    try:
                        game_dt = datetime.datetime.fromisoformat(game_time.replace('Z', '+00:00'))
                        est_time = game_dt.astimezone(pytz.timezone('US/Eastern'))
                        formatted_time = est_time.strftime('%I:%M %p ET')
                        embed.add_field(name="Game Time", value=formatted_time, inline=True)
                    except ValueError:
                        embed.add_field(name="Game Time", value="TBD", inline=True)
            
            venue = current_game.get('venue', {}).get('default', '')
            if venue:
                embed.add_field(name="Venue", value=f"📍 {venue}", inline=False)
            
            await ctx.send(embed=embed)
        
        async def handle_cats_recent(self, ctx):
            """Recent Panthers games"""
            await ctx.send("📊 Getting recent Panthers games...")
            
            recent_games = await self.panthers_manager.get_recent_games()
            
            if not recent_games:
                await ctx.send("No recent games found!")
                return
            
            embed = discord.Embed(
                title="🐾 Recent Panthers Games",
                color=0xC8102E
            )
            
            for game in recent_games[:5]:  # Last 5 games
                home_team = game.get('homeTeam', {})
                away_team = game.get('awayTeam', {})
                
                game_date = datetime.datetime.fromisoformat(game.get('gameDate', '').replace('Z', '+00:00'))
                formatted_date = game_date.strftime('%m/%d')
                
                home_score = home_team.get('score', 0)
                away_score = away_team.get('score', 0)
                
                # Determine if Panthers won
                panthers_home = home_team.get('id') == self.config.PANTHERS_TEAM_ID
                panthers_score = home_score if panthers_home else away_score
                opponent_score = away_score if panthers_home else home_score
                opponent = away_team.get('abbrev', '') if panthers_home else home_team.get('abbrev', '')
                
                result = "W" if panthers_score > opponent_score else "L"
                result_emoji = "✅" if result == "W" else "❌"
                location = "vs" if panthers_home else "@"
                
                game_summary = f"{result_emoji} {result} {panthers_score}-{opponent_score} {location} {opponent}"
                embed.add_field(name=formatted_date, value=game_summary, inline=False)
            
            await ctx.send(embed=embed)
        
        async def handle_cats_help(self, ctx):
            """Panthers commands help"""
            embed = discord.Embed(
                title="🐾 Panthers Commands",
                color=0xC8102E,
                description="All available Panthers commands"
            )
            
            commands_info = [
                ("`!cats`", "Team overview, standings, and next/current game"),
                ("`!cats quote`", "Random player or coach quote"),
                ("`!cats game`", "Detailed current or next game information"),
                ("`!cats recent`", "Last 5 Panthers games with results"),
                ("`!cats help`", "This help message")
            ]
            
            for cmd, desc in commands_info:
                embed.add_field(name=cmd, value=desc, inline=False)
            
            embed.set_footer(text="Go Panthers! 🐾")
            await ctx.send(embed=embed)
        
        # Bind the handler methods to the class
        self.handle_cats_main = handle_cats_main.__get__(self, UrmomBot)
        self.handle_cats_quote = handle_cats_quote.__get__(self, UrmomBot)
        self.handle_cats_game = handle_cats_game.__get__(self, UrmomBot)
        self.handle_cats_recent = handle_cats_recent.__get__(self, UrmomBot)
        self.handle_cats_help = handle_cats_help.__get__(self, UrmomBot)
        
        @self.command(name='movie')
        async def movie_command(ctx, *, query=None):
            """Look up a movie on IMDB"""
            if not query:
                await ctx.send("Please provide a movie title to search for.")
                return
            
            if not OMDB_API_KEY:
                await ctx.send("OMDB API key is not configured. Please set the OMDB_API_KEY environment variable.")
                return
                
            async with aiohttp.ClientSession() as session:
                params = {
                    'apikey': OMDB_API_KEY,
                    's': query,
                    'type': 'movie'
                }
                async with session.get(self.config.OMDB_API_URL, params=params) as response:
                    if response.status != 200:
                        await ctx.send(f"Error: Could not fetch movie data (Status code: {response.status})")
                        return
                    
                    data = await response.json()
                    
                    if data.get('Response') == 'False':
                        await ctx.send(f"No movies found for '{query}'.")
                        return
                    
                    results = data.get('Search', [])
                    if len(results) == 1:
                        # Single result, get detailed info
                        movie = results[0]
                        await self.send_movie_details(ctx, movie['imdbID'])
                    else:
                        # Multiple results, show selection
                        selection_msg = "**Found multiple movies. Please select one by number:**\n\n"
                        
                        # Get more details for each movie
                        detailed_results = []
                        for i, movie in enumerate(results[:10]):  # Limit to 10 results
                            # Get detailed info for this movie
                            movie_id = movie['imdbID']
                            params = {
                                'apikey': OMDB_API_KEY,
                                'i': movie_id
                            }
                            async with session.get(self.config.OMDB_API_URL, params=params) as detail_response:
                                if detail_response.status == 200:
                                    detail_data = await detail_response.json()
                                    if detail_data.get('Response') == 'True':
                                        detailed_results.append(detail_data)
                        
                        for i, movie in enumerate(detailed_results):
                            year = movie.get('Year', 'N/A')
                            actors = movie.get('Actors', 'N/A').split(', ')[:2]  # Get first two actors
                            actors_str = ', '.join(actors) if len(actors) > 0 else 'N/A'
                            director = movie.get('Director', 'N/A')
                            
                            selection_msg += f"**{i+1}.** {movie['Title']} ({year})\n"
                            selection_msg += f"   Actors: {actors_str}\n"
                            selection_msg += f"   Director: {director}\n\n"
                        
                        # Store the results for selection
                        self.movie_selections[ctx.author.id] = [movie['imdbID'] for movie in results[:10]]
                        
                        await ctx.send(selection_msg)
        
        @self.command(name='remind')
        async def remind_command(ctx, *args):
            """Set a reminder"""
            if not args:
                await ctx.send("Usage: `!remind [time] [message]`\n"
                              "Examples:\n"
                              "- `!remind 5 minutes Check the oven`\n"
                              "- `!remind 2 hours Call Mom`\n"
                              "- `!remind at 5pm Go to the gym`\n"
                              "- `!remind tomorrow at 9am Meeting with team`")
                return
            
            # Try to parse time from the arguments
            # First, try to find a time pattern in the first few arguments
            time_str = None
            message_start_index = 0
            
            # Try different combinations of arguments to find a valid time
            for i in range(min(4, len(args))):
                potential_time_str = ' '.join(args[:i+1])
                potential_time = self.reminder_manager.parse_time(potential_time_str)
                if potential_time:
                    time_str = potential_time_str
                    message_start_index = i+1
                    break
            
            if not time_str:
                await ctx.send("I couldn't understand the time format. Please try again with a format like '5 minutes' or 'at 3pm'.")
                return
                
            # Get the message (the rest of the arguments)
            message = ' '.join(args[message_start_index:]) if message_start_index < len(args) else None
            
            # If no message provided, ask for one
            if not message:
                await ctx.send("What would you like to be reminded about?")
                
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel
                
                try:
                    response = await self.wait_for('message', check=check, timeout=60)
                    message = response.content
                except asyncio.TimeoutError:
                    await ctx.send("Reminder creation timed out.")
                    return
            
            # Parse the time
            reminder_time = self.reminder_manager.parse_time(time_str)
            if not reminder_time:
                await ctx.send("I couldn't understand that time format. Please try again with a format like '5 minutes' or 'at 3pm'.")
                return
            
            # Convert to UTC for storage
            reminder_time_utc = reminder_time.astimezone(pytz.utc)
            
            # Check if this is a reply to another message
            reference_msg = None
            reference_author = None
            if ctx.message.reference and ctx.message.reference.resolved:
                referenced_msg = ctx.message.reference.resolved
                reference_msg = referenced_msg.content
                reference_author = referenced_msg.author.id
            
            # Create the reminder
            reminder = Reminder(
                user_id=ctx.author.id,
                channel_id=ctx.channel.id,
                message=message,
                time=reminder_time_utc,
                reference_msg=reference_msg,
                reference_author=reference_author
            )
            
            self.reminder_manager.add_reminder(reminder)
            
            # Format the confirmation time in EST
            est_time = reminder_time.strftime("%I:%M %p %Z on %b %d, %Y")
            await ctx.send(f"I'll remind you at {est_time}!")
                
        @self.event
        async def on_ready():
            """Event fired when the bot is ready"""
            logger.info(f'Logged in as {self.user.name} - {self.user.id}')
            logger.info(f'Bot is ready to serve in {len(self.guilds)} guilds')
        
        @self.event
        async def on_message(message):
            """Event fired when a message is received"""
            if message.author == self.user:
                return
            
            # Check for movie selection
            if message.author.id in self.movie_selections and message.content.isdigit():
                selection = int(message.content)
                if 1 <= selection <= len(self.movie_selections[message.author.id]):
                    movie_id = self.movie_selections[message.author.id][selection-1]
                    await self.send_movie_details(message.channel, movie_id)
                    del self.movie_selections[message.author.id]
                    return
            
            # Process commands first
            await self.process_commands(message)
            
            # Check for 'ur mom' or 'your mom' in message
            if 'ur mom' in message.content.lower() or 'your mom' in message.content.lower():
                await self.handle_mom_reference(message)
            
            # Check for 'alot' in message
            if 'alot' in message.content.lower() and not any(exception in message.content.lower() for exception in self.config.ALOT_EXCEPTIONS):
                await self.handle_alot_reference(message)
    
    async def send_movie_details(self, channel, imdb_id):
        """Send detailed information about a movie"""
        if not OMDB_API_KEY:
            await channel.send("OMDB API key is not configured.")
            return
            
        async with aiohttp.ClientSession() as session:
            params = {
                'apikey': OMDB_API_KEY,
                'i': imdb_id,
                'plot': 'full'
            }
            async with session.get(self.config.OMDB_API_URL, params=params) as response:
                if response.status != 200:
                    await channel.send(f"Error: Could not fetch movie details (Status code: {response.status})")
                    return
                
                data = await response.json()
                
                if data.get('Response') == 'False':
                    await channel.send(f"Could not find movie details.")
                    return
                
                # Create an embed for the movie
                embed = discord.Embed(
                    title=data.get('Title'),
                    description=data.get('Plot'),
                    color=0x5865F2
                )
                
                # Add movie poster if available
                poster = data.get('Poster')
                if poster and poster != 'N/A':
                    embed.set_thumbnail(url=poster)
                
                # Add fields for movie details
                embed.add_field(name="Year", value=data.get('Year', 'N/A'), inline=True)
                embed.add_field(name="Rated", value=data.get('Rated', 'N/A'), inline=True)
                embed.add_field(name="Runtime", value=data.get('Runtime', 'N/A'), inline=True)
                embed.add_field(name="Genre", value=data.get('Genre', 'N/A'), inline=True)
                embed.add_field(name="Director", value=data.get('Director', 'N/A'), inline=True)
                embed.add_field(name="Writer", value=data.get('Writer', 'N/A')[:1024] if data.get('Writer') else 'N/A', inline=True)
                embed.add_field(name="Actors", value=data.get('Actors', 'N/A'), inline=True)
                embed.add_field(name="Language", value=data.get('Language', 'N/A'), inline=True)
                embed.add_field(name="Country", value=data.get('Country', 'N/A'), inline=True)
                
                # Add ratings
                ratings = data.get('Ratings', [])
                ratings_text = ""
                for rating in ratings:
                    ratings_text += f"{rating.get('Source')}: {rating.get('Value')}\n"
                
                if ratings_text:
                    embed.add_field(name="Ratings", value=ratings_text, inline=False)
                
                # Add footer with IMDB ID
                embed.set_footer(text=f"IMDB ID: {data.get('imdbID')} | Powered by OMDB API")
                
                await channel.send(embed=embed)
    
    async def handle_mom_reference(self, message):
        """Handle when someone mentions 'ur mom' or 'your mom'"""
        await message.channel.send(file=discord.File(self.config.URMOM_GIF))
    
    async def handle_alot_reference(self, message):
        """Handle when someone uses 'alot' instead of 'a lot'"""
        if self.config.USE_REACTIONS:
            # Add letter reactions to spell "ALOT"
            await message.add_reaction('🇦')
            await message.add_reaction('🇱')
            await message.add_reaction('🇴')
            await message.add_reaction('🇹')
        
        # Optionally send the alot GIF if enabled
        if self.config.USE_GIF_RESPONSES:
            # Currently commented out as in original code
            # await message.channel.send(file=discord.File(self.config.ALOT_GIF))
            pass

def main():
    """Main function to run the bot"""
    bot = UrmomBot()
    
    if not TOKEN:
        logger.error("No token provided. Set the DISCORD_TOKEN environment variable.")
        return
    
    try:
        logger.info("Starting bot...")
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        logger.error("Invalid token provided")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        
    # Clean up reminder task if it exists
    if bot.reminder_check_task:
        bot.reminder_check_task.cancel()

if __name__ == "__main__":
    main()
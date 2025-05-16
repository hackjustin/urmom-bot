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
    
    # Timezone for reminders
    TIMEZONE = pytz.timezone('US/Eastern')
    
    # Reminder storage
    REMINDER_CHECK_INTERVAL = 10  # seconds

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
            try:
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

class UrmomBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.config = BotConfig()
        self.reminder_manager = ReminderManager(self)
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

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
        
        # Check for relative time format (e.g., "in 5 minutes", "in 2 hours")
        relative_match = re.match(r'(?:in\s+)?(\d+)\s+(second|minute|hour|day|week)s?', time_str, re.IGNORECASE)
        if relative_match:
            amount = int(relative_match.group(1))
            unit = relative_match.group(2).lower()
            
            if unit.startswith('second'):
                delta = datetime.timedelta(seconds=amount)
            elif unit.startswith('minute'):
                delta = datetime.timedelta(minutes=amount)
            elif unit.startswith('hour'):
                delta = datetime.timedelta(hours=amount)
            elif unit.startswith('day'):
                delta = datetime.timedelta(days=amount)
            elif unit.startswith('week'):
                delta = datetime.timedelta(weeks=amount)
            
            return now + delta
        
        # Check for absolute time format (e.g., "at 5pm", "at 14:30")
        at_match = re.match(r'(?:at\s+)?(.*)', time_str, re.IGNORECASE)
        if at_match:
            time_text = at_match.group(1)
            try:
                parsed_time = parser.parse(time_text, fuzzy=True)
                
                # If only time is specified (no date), use today's date
                if parsed_time.date() == datetime.datetime.today().date():
                    # If the parsed time is earlier than now, assume tomorrow
                    if parsed_time.time() < now.time():
                        parsed_time = parsed_time + datetime.timedelta(days=1)
                
                # Convert to EST timezone
                return parsed_time.replace(tzinfo=self.est_timezone)
                
            except ValueError:
                return None
        
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
                            production = movie.get('Production', 'N/A')
                            
                            selection_msg += f"**{i+1}.** {movie['Title']} ({year})\n"
                            selection_msg += f"   Actors: {actors_str}\n"
                            selection_msg += f"   Director: {director}\n"
                            selection_msg += f"   Studio: {production}\n\n"
                        
                        # Store the results for selection
                        self.movie_selections[ctx.author.id] = [movie['imdbID'] for movie in results[:10]]
                        
                        await ctx.send(selection_msg)
        
        @self.command(name='remind')
        async def remind_command(ctx, time_str=None, *, message=None):
            """Set a reminder"""
            # If no time provided, show usage instructions
            if not time_str:
                await ctx.send("Usage: `!remind [time] [message]`\n"
                              "Examples:\n"
                              "- `!remind 5 minutes Check the oven`\n"
                              "- `!remind 2 hours Call Mom`\n"
                              "- `!remind at 5pm Go to the gym`\n"
                              "- `!remind tomorrow at 9am Meeting with team`")
                return
            
            # Check if message is provided
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
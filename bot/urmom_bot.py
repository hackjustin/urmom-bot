import discord
from discord.ext import commands
import asyncio
import logging

from bot.config import BotConfig
from bot.panthers_manager import PanthersManager
from bot.reminder_manager import ReminderManager
from bot.team_comparison import TeamComparison
from bot.movie_manager import MovieManager
from bot.live_monitor import LiveGameMonitor
from bot.panthers_commands import PanthersCommands
from bot.player_stats import PlayerStatsManager
from bot.playoff_bracket import PlayoffBracketManager  # Add this import

logger = logging.getLogger('urmom-bot')

class UrmomBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        # Initialize configuration and managers
        self.config = BotConfig()
        self.panthers_manager = PanthersManager(self.config)
        self.reminder_manager = ReminderManager(self)
        self.team_comparison = TeamComparison(self.config)
        self.movie_manager = MovieManager(self.config)
        self.player_stats_manager = PlayerStatsManager(self.config)
        self.bracket_manager = PlayoffBracketManager(self.config)  # Add this line
        self.live_monitor = LiveGameMonitor(self, self.panthers_manager, self.config)
        self.panthers_commands = PanthersCommands(
            self.config, 
            self.panthers_manager, 
            self.live_monitor, 
            self.team_comparison,
            self.bracket_manager  # Add this parameter
        )
        
        # Background tasks
        self.reminder_check_task = None
        self.emote_check_task = None
        
        # Random emote system
        self.last_emote_date = None
        self.emote_sent_today = False
        
        # Register commands and events
        self.add_commands()
    
    async def setup_hook(self):
        """Set up background tasks when the bot is ready"""
        self.reminder_check_task = self.loop.create_task(self.reminder_check_loop())
        self.emote_check_task = self.loop.create_task(self.random_emote_loop())
        self.live_monitor.start_monitoring()
    
    async def reminder_check_loop(self):
        """Background task to check for due reminders"""
        await self.wait_until_ready()
        while not self.is_closed():
            await self.reminder_manager.check_reminders()
            await asyncio.sleep(self.config.REMINDER_CHECK_INTERVAL)
    
    async def random_emote_loop(self):
        """Background task to send random emotes once per day"""
        await self.wait_until_ready()
        logger.info("🎭 Random emote scheduler started!")
        
        while not self.is_closed():
            try:
                import datetime
                current_time = datetime.datetime.now(self.config.TIMEZONE)
                current_date = current_time.date()
                
                # Reset daily flag if it's a new day
                if self.last_emote_date != current_date:
                    self.emote_sent_today = False
                    self.last_emote_date = current_date
                
                # Check if we should send an emote today (8 AM - 11 PM)
                if (not self.emote_sent_today and 
                    8 <= current_time.hour <= 23):
                    
                    # Random chance to send emote this hour (1 in 8 chance per check)
                    import random
                    if random.randint(1, 8) == 1:
                        await self.send_random_emote_to_channels()
                        self.emote_sent_today = True
                
                # Check every hour
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in random emote loop: {e}")
                await asyncio.sleep(3600)  # Wait an hour if there's an error
    
    async def send_random_emote_to_channels(self):
        """Send a random emote to channels"""
        try:
            import random
            # Get a random emote
            emote = random.choice(self.config.RANDOM_EMOTES)
            
            # Find any channel we can access
            for guild in self.guilds:
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        await channel.send(f"*{emote}*")
                        logger.info(f"Sent random daily emote to channel {channel.id}: {emote}")
                        return  # Only send to one channel
                        
        except Exception as e:
            logger.error(f"Error sending random emote: {e}")
    
    def add_commands(self):
        @self.command(name='mom')
        async def mom_command(ctx):
            """Command to respond to !mom"""
            await ctx.send('what...?')
            
        @self.command(name='cats')
        async def cats_command(ctx, subcommand=None, *, args=None):
            """Panthers team information"""
            if subcommand is None:
                await self.panthers_commands.handle_cats_main(ctx)
            elif subcommand.lower() == 'vs' and args:
                team_name = args.strip()
                await self.team_comparison.handle_team_comparison(ctx, team_name)
            elif subcommand.lower() == 'player' and args:
                player_name = args.strip()
                await self.player_stats_manager.search_player(ctx, player_name)
            elif subcommand.lower() == 'quote':
                await self.panthers_commands.handle_cats_quote(ctx)
            elif subcommand.lower() == 'game':
                await self.panthers_commands.handle_cats_game(ctx)
            elif subcommand.lower() == 'recent':
                await self.panthers_commands.handle_cats_recent(ctx)
            elif subcommand.lower() == 'live':
                action = args.strip() if args else None
                await self.panthers_commands.handle_cats_live(ctx, action)
            elif subcommand.lower() == 'bracket':  # Add bracket command
                await self.panthers_commands.handle_cats_bracket(ctx)
            elif subcommand.lower() == 'series':  # Add series command
                await self.panthers_commands.handle_cats_series(ctx)
            elif subcommand.lower() == 'round':  # Add round command
                round_num = args.strip() if args else None
                await self.panthers_commands.handle_cats_round(ctx, round_num)
            elif subcommand.lower() == 'help':
                await self.panthers_commands.handle_cats_help(ctx)
            else:
                await ctx.send("Unknown command. Use `!cats`, `!cats game`, `!cats live`, `!cats vs <team>`, `!cats player <name>`, `!cats bracket`, `!cats series`, or `!cats help`")
        
        @self.command(name='wisdom')
        async def wisdom_command(ctx):
            """Random Taylor Swift quote"""
            import random
            quote = random.choice(self.config.TAYLOR_SWIFT_QUOTES)
            await ctx.send(quote)

        @self.command(name='movie')
        async def movie_command(ctx, *, query=None):
            """Look up a movie on IMDB"""
            if not query:
                await ctx.send("Please provide a movie title to search for.")
                return
            
            await self.movie_manager.search_movie(ctx, query)
        
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
            import pytz
            reminder_time_utc = reminder_time.astimezone(pytz.utc)
            
            # Check if this is a reply to another message
            reference_msg = None
            reference_author = None
            if ctx.message.reference and ctx.message.reference.resolved:
                referenced_msg = ctx.message.reference.resolved
                reference_msg = referenced_msg.content
                reference_author = referenced_msg.author.id
            
            # Create the reminder
            from bot.reminder_manager import Reminder
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
        
        @self.command(name='emote')
        async def emote_command(ctx, action=None):
            """Test the random emote system"""
            if action and action.lower() == 'test':
                import random
                # Send a random emote for testing
                emote = random.choice(self.config.RANDOM_EMOTES)
                await ctx.send(f"*{emote}*")
                logger.info(f"Manual emote triggered by {ctx.author}: {emote}")
            else:
                await ctx.send("Usage: `!emote test` - Trigger a random emote for testing")
                
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
            if await self.movie_manager.handle_movie_selection(message):
                return
            
            # Check for player selection
            if await self.player_stats_manager.handle_player_selection(message):
                return
            
            # Process commands first
            await self.process_commands(message)
            
            # Check for 'ur mom' or 'your mom' in message
            if 'ur mom' in message.content.lower() or 'your mom' in message.content.lower():
                await self.handle_mom_reference(message)
            
            # Check for 'alot' in message
            if 'alot' in message.content.lower() and not any(exception in message.content.lower() for exception in self.config.ALOT_EXCEPTIONS):
                await self.handle_alot_reference(message)
    
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
    
    async def close(self):
        """Clean up resources when shutting down"""
        # Clean up movie manager resources
        await self.movie_manager.cleanup()
        
        # Cancel background tasks
        if hasattr(self, 'reminder_check_task') and self.reminder_check_task:
            self.reminder_check_task.cancel()
        
        # Call parent close
        await super().close()
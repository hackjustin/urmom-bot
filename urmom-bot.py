import os
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('urmom-bot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

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
    
    # User tracking (for future features)
    WORD_COUNT_THRESHOLD = 10

class WordCounter:
    """Class to track word usage by users"""
    def __init__(self):
        self.user_word_counts = {}
    
    def record_word(self, user_id, word):
        """Record a word usage by a user"""
        if user_id not in self.user_word_counts:
            self.user_word_counts[user_id] = {}
        
        if word not in self.user_word_counts[user_id]:
            self.user_word_counts[user_id][word] = 0
        
        self.user_word_counts[user_id][word] += 1
        return self.user_word_counts[user_id][word]
    
    def get_count(self, user_id, word):
        """Get the count of a word for a user"""
        return self.user_word_counts.get(user_id, {}).get(word, 0)

class UrmomBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.config = BotConfig()
        self.word_counter = WordCounter()
        
        # Register commands and events
        self.add_commands()
    
    def add_commands(self):
        @self.command(name='mom')
        async def mom_command(ctx):
            """Command to respond to !mom"""
            await ctx.send('what...?')
        
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
            
            # Process commands first
            await self.process_commands(message)
            
            # Check for 'ur mom' or 'your mom' in message
            if 'ur mom' in message.content.lower() or 'your mom' in message.content.lower():
                await self.handle_mom_reference(message)
            
            # Check for 'alot' in message
            if 'alot' in message.content.lower() and not any(exception in message.content.lower() for exception in self.config.ALOT_EXCEPTIONS):
                await self.handle_alot_reference(message)
                
            # Example of tracking word usage (for future feature)
            for word in message.content.lower().split():
                count = self.word_counter.record_word(message.author.id, word)
                if count == self.config.WORD_COUNT_THRESHOLD:
                    await self.handle_word_threshold_reached(message, word)
    
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
            # await message.channel.send(file=discord.File(self.config.ALOT_GIF))
            pass
    
    async def handle_word_threshold_reached(self, message, word):
        """Handle when a user uses the same word multiple times"""
        await message.channel.send(f"Hey {message.author.mention}, you've used the word '{word}' {self.config.WORD_COUNT_THRESHOLD} times!")

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

if __name__ == "__main__":
    main()

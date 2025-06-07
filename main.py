import os
import logging
from dotenv import load_dotenv
from bot.urmom_bot import UrmomBot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('urmom-bot')

def main():
    """Main function to run the bot"""
    load_dotenv()
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("No token provided. Set the DISCORD_TOKEN environment variable.")
        return
    
    bot = UrmomBot()
    
    try:
        logger.info("Starting bot...")
        bot.run(token)
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        
    # Clean up tasks if they exist
    if hasattr(bot, 'reminder_check_task') and bot.reminder_check_task:
        bot.reminder_check_task.cancel()
    if hasattr(bot, 'live_monitor_task') and bot.live_monitor_task:
        bot.live_monitor_task.cancel()

if __name__ == "__main__":
    main()
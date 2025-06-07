import asyncio
import datetime
import logging

logger = logging.getLogger('urmom-bot')

class LiveGameMonitor:
    """Handles live game monitoring and updates"""
    
    def __init__(self, bot, panthers_manager, config):
        self.bot = bot
        self.panthers_manager = panthers_manager
        self.config = config
        self.live_channels = set()  # Channels that want live updates
        self.last_game_state = {}  # Store last known game state
        self.monitor_task = None
    
    def start_monitoring(self):
        """Start the live game monitoring task"""
        if self.monitor_task is None or self.monitor_task.done():
            self.monitor_task = self.bot.loop.create_task(self.live_game_monitor())
            logger.info("🏒 Live game monitor started!")
    
    def stop_monitoring(self):
        """Stop the live game monitoring task"""
        if self.monitor_task and not self.monitor_task.done():
            self.monitor_task.cancel()
            logger.info("Live game monitor stopped")
    
    def add_channel(self, channel_id):
        """Add a channel to live updates"""
        self.live_channels.add(channel_id)
        logger.info(f"Live updates enabled for channel {channel_id}")
    
    def remove_channel(self, channel_id):
        """Remove a channel from live updates"""
        self.live_channels.discard(channel_id)
        logger.info(f"Live updates disabled for channel {channel_id}")
    
    def is_channel_subscribed(self, channel_id):
        """Check if channel is subscribed to live updates"""
        return channel_id in self.live_channels
    
    async def live_game_monitor(self):
        """Background task to monitor live Panthers games"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            try:
                # Only check if we have channels subscribed to live updates
                if self.live_channels:
                    current_game = await self.panthers_manager.get_current_game()
                    
                    if current_game:
                        game_state = current_game.get('gameState', '')
                        game_id = current_game.get('id', '')
                        
                        # Check if game is live
                        if game_state in ['LIVE', 'CRIT']:
                            await self.check_for_score_changes(current_game)
                        elif game_state == 'OFF' and game_id in self.last_game_state:
                            # Game just ended
                            await self.announce_game_end(current_game)
                            # Clear the stored state
                            if game_id in self.last_game_state:
                                del self.last_game_state[game_id]
                
                # Check every 30 seconds during potential game times, less frequently otherwise
                current_hour = datetime.datetime.now().hour
                if 18 <= current_hour <= 23:  # Prime game hours (6 PM - 11 PM ET)
                    await asyncio.sleep(30)
                else:
                    await asyncio.sleep(300)  # 5 minutes during off-hours
                    
            except Exception as e:
                logger.error(f"Error in live game monitor: {e}")
                await asyncio.sleep(60)  # Wait longer if there's an error
    
    async def check_for_score_changes(self, current_game):
        """Check if the score has changed and announce updates"""
        game_id = current_game.get('id', '')
        home_team = current_game.get('homeTeam', {})
        away_team = current_game.get('awayTeam', {})
        
        # Current game state
        current_state = {
            'home_score': home_team.get('score', 0),
            'away_score': away_team.get('score', 0),
            'period': current_game.get('periodDescriptor', {}).get('number', ''),
            'home_abbrev': home_team.get('abbrev', 'HOME'),
            'away_abbrev': away_team.get('abbrev', 'AWAY')
        }
        
        # Check if we have previous state
        if game_id in self.last_game_state:
            last_state = self.last_game_state[game_id]
            
            # Score change detected!
            if (current_state['home_score'] != last_state['home_score'] or 
                current_state['away_score'] != last_state['away_score']):
                await self.announce_score_change(current_state, last_state)
            
            # Period change detected!
            elif current_state['period'] != last_state['period']:
                await self.announce_period_change(current_state)
        
        # Update stored state
        self.last_game_state[game_id] = current_state
    
    async def announce_score_change(self, current_state, last_state):
        """Announce a score change to subscribed channels"""
        # Figure out who scored
        panthers_scored = False
        if current_state['home_abbrev'] == 'FLA':
            panthers_scored = current_state['home_score'] > last_state['home_score']
        else:
            panthers_scored = current_state['away_score'] > last_state['away_score']
        
        # Create announcement
        if panthers_scored:
            announcement = f"🚨 **PANTHERS GOAL!** 🚨\n"
        else:
            announcement = f"⚪ Goal scored\n"
        
        announcement += f"{current_state['away_abbrev']} {current_state['away_score']} - {current_state['home_score']} {current_state['home_abbrev']}\n"
        announcement += f"Period {current_state['period']}"
        
        await self.send_to_live_channels(announcement)
    
    async def announce_period_change(self, current_state):
        """Announce period changes"""
        announcement = f"🏒 **Period {current_state['period']} Starting**\n"
        announcement += f"{current_state['away_abbrev']} {current_state['away_score']} - {current_state['home_score']} {current_state['home_abbrev']}"
        
        await self.send_to_live_channels(announcement)
    
    async def announce_game_end(self, game):
        """Announce when the game ends"""
        home_team = game.get('homeTeam', {})
        away_team = game.get('awayTeam', {})
        
        home_score = home_team.get('score', 0)
        away_score = away_team.get('score', 0)
        
        # Check if Panthers won
        panthers_won = False
        if home_team.get('abbrev') == 'FLA':
            panthers_won = home_score > away_score
        else:
            panthers_won = away_score > home_score
        
        if panthers_won:
            announcement = f"🎉 **PANTHERS WIN!** 🎉\n"
        else:
            announcement = f"😞 **Game Over**\n"
        
        announcement += f"Final: {away_team.get('abbrev', 'AWAY')} {away_score} - {home_score} {home_team.get('abbrev', 'HOME')}"
        
        await self.send_to_live_channels(announcement)
    
    async def send_to_live_channels(self, message):
        """Send a message to all channels subscribed to live updates"""
        for channel_id in self.live_channels.copy():  # Copy to avoid modification during iteration
            try:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send(message)
                else:
                    # Channel not found, remove from live channels
                    self.live_channels.discard(channel_id)
            except Exception as e:
                logger.error(f"Failed to send live update to channel {channel_id}: {e}")
                # Remove problematic channels
                self.live_channels.discard(channel_id)
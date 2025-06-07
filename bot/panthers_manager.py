import aiohttp
import datetime
import pytz
import logging

logger = logging.getLogger('urmom-bot')

class PanthersManager:
    """Class to manage Panthers NHL data"""
    def __init__(self, config):
        self.config = config
        
    async def get_team_info(self):
        """Get basic Panthers team information"""
        try:
            async with aiohttp.ClientSession() as session:
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
                # Method 1: Check today's league schedule
                today = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d')
                url = f"{self.config.NHL_API_BASE}/schedule/{today}"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for game_week in data.get('gameWeek', []):
                            for game in game_week.get('games', []):
                                home_team = game.get('homeTeam', {})
                                away_team = game.get('awayTeam', {})
                                if (home_team.get('id') == self.config.PANTHERS_TEAM_ID or 
                                    away_team.get('id') == self.config.PANTHERS_TEAM_ID):
                                    return game
                
                # Method 2: Check team's weekly schedule
                url = f"{self.config.NHL_API_BASE}/club-schedule/{self.config.PANTHERS_TEAM_ABBREV}/week/now"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        games = data.get('games', [])
                        today_utc = datetime.datetime.now(pytz.utc).date()
                        
                        for game in games:
                            if self._is_game_today(game, today_utc):
                                return game
                        
        except Exception as e:
            logger.error(f"Error fetching current Panthers game: {e}")
            
        return None
    
    def _is_game_today(self, game, today_utc):
        """Helper to check if a game is today"""
        game_date_str = game.get('gameDate', '')
        if not game_date_str:
            return False
            
        try:
            if 'T' in game_date_str:
                game_date = datetime.datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
            else:
                date_part = datetime.datetime.strptime(game_date_str, '%Y-%m-%d')
                game_date = pytz.utc.localize(date_part)
            
            return game_date.date() == today_utc
        except ValueError:
            return False
            
    async def get_next_game(self):
        """Get next Panthers game"""
        try:
            async with aiohttp.ClientSession() as session:
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
                            except (ValueError, TypeError):
                                continue
        except Exception as e:
            logger.error(f"Error fetching next Panthers game: {e}")
            
        return None
            
    async def get_recent_games(self, limit=5):
        """Get recent Panthers games"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.config.NHL_API_BASE}/club-schedule-season/{self.config.PANTHERS_TEAM_ABBREV}/now"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        games = data.get('games', [])
                        now_utc = datetime.datetime.now(pytz.utc)
                        
                        recent_games = []
                        final_states = ['OFF', 'FINAL', 'OVER', 'FINAL_OT', 'FINAL_SO']
                        
                        for game in reversed(games):  # Start from most recent
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
                                
                                if game_date < now_utc and game_state in final_states:
                                    recent_games.append(game)
                                    if len(recent_games) >= limit:
                                        break
                                    
                            except Exception as e:
                                logger.warning(f"Error processing game: {e}")
                                continue
                        
                        return recent_games
                        
        except Exception as e:
            logger.error(f"Error fetching recent Panthers games: {e}")
            
        return []
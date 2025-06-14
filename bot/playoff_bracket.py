import aiohttp
import discord
import logging
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger('urmom-bot')

class PlayoffBracketManager:
    """Handles Stanley Cup playoff bracket tracking and display"""
    
    def __init__(self, config):
        self.config = config
        self.bracket_cache = {}
        self.cache_expiry = 300  # 5 minutes
        self.last_update = None
        
        # Team emoji mapping for visual flair
        self.team_emojis = {
            'FLA': '🐾', 'TBL': '⚡', 'TOR': '🍁', 'BOS': '🐻',
            'NYR': '🗽', 'CAR': '🌪️', 'WSH': '🦅', 'NYI': '🏝️',
            'EDM': '🛢️', 'VAN': '🏔️', 'COL': '❄️', 'VGK': '⚔️',
            'DAL': '⭐', 'WPG': '✈️', 'NSH': '🎵', 'LA': '👑'
        }
    
    async def show_bracket(self, ctx):
        """Display the current Stanley Cup playoff bracket"""
        try:
            bracket_data = await self._get_playoff_data()
            
            if not bracket_data:
                # Create a manual fallback embed
                embed = discord.Embed(
                    title="🏆 Stanley Cup Playoffs",
                    color=0xFFD700,
                    description="⚠️ NHL playoff API is currently unavailable"
                )
                embed.add_field(
                    name="🔥 Current Status",
                    value="**2025 Stanley Cup Final**\n🐾 Florida Panthers vs Edmonton Oilers ⚡",
                    inline=False
                )
                embed.add_field(
                    name="📊 Latest Info",
                    value="Check NHL.com or ESPN for live bracket updates, game schedules, and series scores.",
                    inline=False
                )
                embed.set_footer(text="API temporarily unavailable - check back later")
                await ctx.send(embed=embed)
                return
            
            # Create bracket embed
            embed = await self._create_bracket_embed(bracket_data)
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing bracket: {e}")
            await ctx.send("❌ Error displaying playoff bracket. The NHL API might be temporarily unavailable.")
    
    async def show_panthers_series(self, ctx):
        """Show current Panthers playoff series status"""
        try:
            bracket_data = await self._get_playoff_data()
            
            if not bracket_data:
                await ctx.send("❌ Unable to fetch playoff data.")
                return
            
            # Handle fallback case
            if bracket_data.get('fallback'):
                embed = discord.Embed(
                    title="🐾 Panthers Playoff Status",
                    color=0xC8102E,
                    description="🏆 **2025 Stanley Cup Final**\n\n🐾 **Florida Panthers** vs **Edmonton Oilers** ⚡"
                )
                embed.add_field(
                    name="🔥 Series Status",
                    value="The Panthers are competing for the Stanley Cup!\nCheck NHL.com or ESPN for live game updates and series scores.",
                    inline=False
                )
                embed.add_field(
                    name="📺 Where to Watch",
                    value="Games air on TNT\nCheck your local listings for exact times",
                    inline=False
                )
                embed.set_footer(text="Go Panthers! Bring home the Cup! 🏆🐾")
                await ctx.send(embed=embed)
                return
            
            panthers_series = self._find_panthers_series(bracket_data)
            
            if not panthers_series:
                await ctx.send("🐾 Panthers are not currently in the playoffs, or playoff data is unavailable.")
                return
            
            embed = await self._create_series_embed(panthers_series)
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing Panthers series: {e}")
            await ctx.send("❌ Error displaying Panthers series.")
    
    async def show_round_summary(self, ctx, round_num=None):
        """Show summary of specific playoff round"""
        try:
            bracket_data = await self._get_playoff_data()
            
            if not bracket_data:
                await ctx.send("❌ Unable to fetch playoff data.")
                return
            
            embed = await self._create_round_summary_embed(bracket_data, round_num)
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing round summary: {e}")
            await ctx.send("❌ Error displaying round summary.")
    
    async def _get_playoff_data(self):
        """Fetch current playoff bracket data from NHL API"""
        try:
            # Check cache first
            now = datetime.now()
            if (self.bracket_cache and self.last_update and 
                (now - self.last_update).seconds < self.cache_expiry):
                return self.bracket_cache
            
            async with aiohttp.ClientSession() as session:
                # Try multiple API endpoints for playoff data
                urls_to_try = [
                    "https://api-web.nhle.com/v1/playoff-bracket/now",
                    "https://api-web.nhle.com/v1/playoff-bracket/2025",
                    "https://api-web.nhle.com/v1/playoff-bracket/20242025",
                    "https://api-web.nhle.com/v1/playoffs"
                ]
                
                for url in urls_to_try:
                    try:
                        async with session.get(url) as response:
                            if response.status == 200:
                                data = await response.json()
                                self.bracket_cache = data
                                self.last_update = now
                                logger.info(f"Successfully fetched playoff data from {url}")
                                return data
                            else:
                                logger.warning(f"Failed to fetch from {url}: {response.status}")
                    except Exception as e:
                        logger.warning(f"Error trying {url}: {e}")
                        continue
                
                # If all playoff APIs fail, try to get current season data and show a friendly message
                logger.error("All playoff API endpoints failed, creating fallback response")
                return self._create_fallback_data()
                        
        except Exception as e:
            logger.error(f"Error fetching playoff data: {e}")
            return self._create_fallback_data()
    
    def _create_fallback_data(self):
        """Create fallback data when API is unavailable"""
        return {
            "fallback": True,
            "message": "Playoff bracket data is currently unavailable from the NHL API. This might be during the offseason or due to API maintenance.",
            "current_info": "Based on recent news, the 2025 Stanley Cup Final features Panthers vs Oilers!"
        }
    
    async def _create_bracket_embed(self, bracket_data):
        """Create Discord embed for playoff bracket"""
        embed = discord.Embed(
            title="🏆 Stanley Cup Playoffs Bracket",
            color=0xFFD700,  # Gold color
            timestamp=datetime.now(timezone.utc)
        )
        
        # Handle fallback case when API is unavailable
        if bracket_data.get('fallback'):
            embed.description = bracket_data.get('message', 'Playoff data unavailable')
            embed.add_field(
                name="🔥 Current Status", 
                value=bracket_data.get('current_info', 'Check NHL.com for the latest playoff information'),
                inline=False
            )
            embed.add_field(
                name="🐾 Panthers Update",
                value="The Panthers are competing in the 2025 Stanley Cup Final against the Edmonton Oilers! Go Cats! 🏆",
                inline=False
            )
            embed.set_footer(text="Playoff data unavailable - check back later")
            return embed
        
        # Process bracket by rounds
        rounds = bracket_data.get('rounds', [])
        
        if not rounds:
            embed.description = "Playoff bracket data not available."
            return embed
        
        # Get current round info
        current_round = self._get_current_round(rounds)
        
        embed.description = f"**Current Round:** {current_round['name'] if current_round else 'Offseason'}"
        
        # Add each round as a field
        for round_data in rounds:
            round_name = round_data.get('roundNumber', 'Unknown')
            round_display = self._get_round_display_name(round_name)
            
            series_text = ""
            series_list = round_data.get('series', [])
            
            for series in series_list:
                series_summary = self._format_series_summary(series)
                if series_summary:
                    series_text += series_summary + "\n"
            
            if series_text:
                embed.add_field(
                    name=f"{round_display}",
                    value=series_text.strip(),
                    inline=False
                )
        
        # Add Panthers-specific info if they're playing
        panthers_info = self._get_panthers_status(rounds)
        if panthers_info:
            embed.add_field(
                name="🐾 Panthers Status",
                value=panthers_info,
                inline=False
            )
        
        embed.set_footer(text="NHL Playoff Bracket | Updates every 5 minutes")
        return embed
    
    async def _create_series_embed(self, series_data):
        """Create detailed embed for Panthers series"""
        embed = discord.Embed(
            title="🐾 Panthers Playoff Series",
            color=0xC8102E,  # Panthers red
            timestamp=datetime.now(timezone.utc)
        )
        
        team1 = series_data.get('team1', {})
        team2 = series_data.get('team2', {})
        
        # Determine which team is Panthers
        panthers_team = team1 if team1.get('abbrev') == 'FLA' else team2
        opponent_team = team2 if panthers_team == team1 else team1
        
        panthers_wins = panthers_team.get('wins', 0)
        opponent_wins = opponent_team.get('wins', 0)
        
        # Series status
        round_name = self._get_round_display_name(series_data.get('roundNumber', 1))
        series_status = f"**{round_name}**\n"
        series_status += f"🐾 **Panthers** {panthers_wins} - {opponent_wins} **{opponent_team.get('name', 'TBD')}**"
        
        embed.add_field(name="Series Score", value=series_status, inline=False)
        
        # Games breakdown
        games = series_data.get('games', [])
        if games:
            games_text = ""
            for i, game in enumerate(games, 1):
                game_summary = self._format_game_summary(game, i)
                if game_summary:
                    games_text += game_summary + "\n"
            
            if games_text:
                embed.add_field(name="Games", value=games_text.strip(), inline=False)
        
        # Next game info
        next_game = self._get_next_game(games)
        if next_game:
            embed.add_field(name="Next Game", value=next_game, inline=False)
        
        # Series notes
        if panthers_wins == 4:
            embed.add_field(name="🎉 Result", value="**Panthers Win Series!**", inline=False)
        elif opponent_wins == 4:
            embed.add_field(name="💔 Result", value="**Panthers Eliminated**", inline=False)
        else:
            games_needed = 4 - max(panthers_wins, opponent_wins)
            embed.add_field(name="📊 Series Status", 
                          value=f"First to 4 wins advances\n{games_needed} more wins needed", 
                          inline=False)
        
        embed.set_footer(text="Panthers Playoff Series | Go Cats!")
        return embed
    
    async def _create_round_summary_embed(self, bracket_data, round_num):
        """Create embed for specific round summary"""
        rounds = bracket_data.get('rounds', [])
        
        if round_num:
            target_round = next((r for r in rounds if r.get('roundNumber') == round_num), None)
            if not target_round:
                embed = discord.Embed(title="❌ Round Not Found", color=0xFF0000)
                embed.description = f"Round {round_num} not found in current playoff bracket."
                return embed
            rounds = [target_round]
        
        embed = discord.Embed(
            title="🏒 Playoff Round Summary",
            color=0x005BB7,
            timestamp=datetime.now(timezone.utc)
        )
        
        for round_data in rounds:
            round_name = self._get_round_display_name(round_data.get('roundNumber', 1))
            series_list = round_data.get('series', [])
            
            round_text = ""
            for series in series_list:
                series_summary = self._format_series_summary(series, detailed=True)
                if series_summary:
                    round_text += series_summary + "\n"
            
            if round_text:
                embed.add_field(
                    name=round_name,
                    value=round_text.strip(),
                    inline=False
                )
        
        embed.set_footer(text="NHL Playoff Summary")
        return embed
    
    def _find_panthers_series(self, bracket_data):
        """Find Panthers current series in bracket data"""
        rounds = bracket_data.get('rounds', [])
        
        for round_data in rounds:
            series_list = round_data.get('series', [])
            for series in series_list:
                team1 = series.get('team1', {})
                team2 = series.get('team2', {})
                
                if (team1.get('abbrev') == 'FLA' or team2.get('abbrev') == 'FLA'):
                    return series
        
        return None
    
    def _get_current_round(self, rounds):
        """Determine current active round"""
        for round_data in rounds:
            series_list = round_data.get('series', [])
            for series in series_list:
                # Check if series is ongoing (not completed)
                team1_wins = series.get('team1', {}).get('wins', 0)
                team2_wins = series.get('team2', {}).get('wins', 0)
                
                if team1_wins < 4 and team2_wins < 4:
                    return round_data
        
        return rounds[-1] if rounds else None
    
    def _get_round_display_name(self, round_num):
        """Convert round number to display name"""
        round_names = {
            1: "🥅 First Round",
            2: "⚡ Second Round", 
            3: "🏒 Conference Finals",
            4: "🏆 Stanley Cup Final"
        }
        return round_names.get(round_num, f"Round {round_num}")
    
    def _format_series_summary(self, series, detailed=False):
        """Format series for display"""
        team1 = series.get('team1', {})
        team2 = series.get('team2', {})
        
        if not team1.get('name') or not team2.get('name'):
            return None
        
        team1_name = team1.get('abbrev', team1.get('name', 'TBD'))
        team2_name = team2.get('abbrev', team2.get('name', 'TBD'))
        team1_wins = team1.get('wins', 0)
        team2_wins = team2.get('wins', 0)
        
        # Add emoji if available
        team1_emoji = self.team_emojis.get(team1_name, '🏒')
        team2_emoji = self.team_emojis.get(team2_name, '🏒')
        
        if detailed:
            return f"{team1_emoji} **{team1_name}** {team1_wins} - {team2_wins} **{team2_name}** {team2_emoji}"
        else:
            return f"{team1_emoji} {team1_name} {team1_wins}-{team2_wins} {team2_name} {team2_emoji}"
    
    def _format_game_summary(self, game, game_num):
        """Format individual game summary"""
        if not game:
            return f"Game {game_num}: TBD"
        
        home_team = game.get('homeTeam', {}).get('abbrev', 'TBD')
        away_team = game.get('awayTeam', {}).get('abbrev', 'TBD')
        home_score = game.get('homeTeam', {}).get('score')
        away_score = game.get('awayTeam', {}).get('score')
        
        if home_score is not None and away_score is not None:
            return f"Game {game_num}: {away_team} {away_score} - {home_score} {home_team}"
        else:
            game_date = game.get('gameDate', '')
            if game_date:
                return f"Game {game_num}: {away_team} @ {home_team} - {game_date}"
            else:
                return f"Game {game_num}: {away_team} @ {home_team} - TBD"
    
    def _get_next_game(self, games):
        """Get next scheduled game info"""
        for game in games:
            home_score = game.get('homeTeam', {}).get('score')
            away_score = game.get('awayTeam', {}).get('score')
            
            # If no scores, this is the next game
            if home_score is None and away_score is None:
                home_team = game.get('homeTeam', {}).get('abbrev', 'TBD')
                away_team = game.get('awayTeam', {}).get('abbrev', 'TBD')
                game_date = game.get('gameDate', 'TBD')
                
                return f"{away_team} @ {home_team}\n📅 {game_date}"
        
        return None
    
    def _get_panthers_status(self, rounds):
        """Get Panthers-specific status info"""
        for round_data in rounds:
            series_list = round_data.get('series', [])
            for series in series_list:
                team1 = series.get('team1', {})
                team2 = series.get('team2', {})
                
                if team1.get('abbrev') == 'FLA':
                    panthers_wins = team1.get('wins', 0)
                    opponent_wins = team2.get('wins', 0)
                    opponent_name = team2.get('name', 'TBD')
                    round_name = self._get_round_display_name(round_data.get('roundNumber', 1))
                    
                    if panthers_wins == 4:
                        return f"✅ **Advanced from {round_name}!**"
                    elif opponent_wins == 4:
                        return f"❌ **Eliminated in {round_name}**"
                    else:
                        return f"🔥 **Active in {round_name}** vs {opponent_name}\nSeries tied {panthers_wins}-{opponent_wins}"
                
                elif team2.get('abbrev') == 'FLA':
                    panthers_wins = team2.get('wins', 0)
                    opponent_wins = team1.get('wins', 0)
                    opponent_name = team1.get('name', 'TBD')
                    round_name = self._get_round_display_name(round_data.get('roundNumber', 1))
                    
                    if panthers_wins == 4:
                        return f"✅ **Advanced from {round_name}!**"
                    elif opponent_wins == 4:
                        return f"❌ **Eliminated in {round_name}**"
                    else:
                        return f"🔥 **Active in {round_name}** vs {opponent_name}\nSeries tied {panthers_wins}-{opponent_wins}"
        
        return None
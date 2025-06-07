import aiohttp
import discord
import logging
from difflib import SequenceMatcher

logger = logging.getLogger('urmom-bot')

class PlayerStatsManager:
    """Handles NHL player statistics lookup"""
    
    def __init__(self, config):
        self.config = config
        self.player_cache = {}  # Cache player data to avoid repeated API calls
    
    async def search_player(self, ctx, player_name):
        """Search for a player and show their stats"""
        try:
            # Step 1: Search for players matching the name
            players = await self._search_players_by_name(player_name)
            
            if not players:
                await ctx.send(f"❌ No players found matching '{player_name}'. Try a different spelling or first/last name only.")
                return
            
            if len(players) == 1:
                # Single match - show stats directly
                await self._show_player_stats(ctx, players[0])
            else:
                # Multiple matches - show selection menu
                await self._show_player_selection(ctx, players, player_name)
                
        except Exception as e:
            logger.error(f"Error in player search: {e}")
            await ctx.send("❌ Error searching for player stats.")
    
    async def _search_players_by_name(self, player_name):
        """Search for players by name using the stats API - includes both skaters and goalies"""
        try:
            async with aiohttp.ClientSession() as session:
                all_players = []
                
                # Search skaters first
                skater_url = "https://api.nhle.com/stats/rest/en/skater/summary"
                skater_params = {
                    'isAggregate': 'false',
                    'isGame': 'false',
                    'sort': '[{"property":"points","direction":"DESC"}]',
                    'start': '0',
                    'limit': '1000',  # Get lots of players
                    'cayenneExp': 'seasonId<=20242025 and seasonId>=20242025 and gameTypeId=2'
                }
                
                async with session.get(skater_url, params=skater_params) as response:
                    if response.status == 200:
                        data = await response.json()
                        skaters = data.get('data', [])
                        # Add player type for identification
                        for skater in skaters:
                            skater['player_type'] = 'skater'
                        all_players.extend(skaters)
                
                # Search goalies too
                goalie_url = "https://api.nhle.com/stats/rest/en/goalie/summary"
                goalie_params = {
                    'isAggregate': 'false',
                    'isGame': 'false',
                    'sort': '[{"property":"wins","direction":"DESC"}]',
                    'start': '0',
                    'limit': '200',  # Fewer goalies than skaters
                    'cayenneExp': 'seasonId<=20242025 and seasonId>=20242025 and gameTypeId=2'
                }
                
                async with session.get(goalie_url, params=goalie_params) as response:
                    if response.status == 200:
                        data = await response.json()
                        goalies = data.get('data', [])
                        # Add player type and normalize field names for goalies
                        for goalie in goalies:
                            goalie['player_type'] = 'goalie'
                            # Goalies use 'goalieFullName' instead of 'skaterFullName'
                            goalie['skaterFullName'] = goalie.get('goalieFullName', '')
                        all_players.extend(goalies)
                    
                # Search for name matches in both skaters and goalies
                matches = []
                search_name = player_name.lower().strip()
                
                for player in all_players:
                    full_name = player.get('skaterFullName', '').lower()
                    first_name = player.get('firstName', '').lower()
                    last_name = player.get('lastName', '').lower()
                    
                    # Check various matching strategies
                    if (search_name in full_name or 
                        search_name == first_name or 
                        search_name == last_name or
                        full_name.startswith(search_name) or
                        self._similarity_match(search_name, full_name) > 0.8):
                        matches.append(player)
                
                # Sort by similarity to search term
                matches.sort(key=lambda p: self._similarity_match(search_name, p.get('skaterFullName', '').lower()), reverse=True)
                
                return matches[:10]  # Return top 10 matches
                    
        except Exception as e:
            logger.error(f"Error searching players: {e}")
            return []
    
    def _similarity_match(self, search_term, full_name):
        """Calculate similarity between search term and player name"""
        return SequenceMatcher(None, search_term, full_name).ratio()
    
    async def _show_player_selection(self, ctx, players, original_search):
        """Show player selection menu when multiple matches found"""
        embed = discord.Embed(
            title=f"🏒 Multiple players found for '{original_search}'",
            description="Select a player by number:",
            color=0x005BB7  # NHL blue
        )
        
        selection_text = ""
        for i, player in enumerate(players[:5], 1):  # Show top 5
            name = player.get('skaterFullName', 'Unknown')
            team = player.get('teamAbbrevs', [''])[0] if player.get('teamAbbrevs') else 'N/A'
            position = player.get('positionCode', 'N/A')
            games = player.get('gamesPlayed', 0)
            points = player.get('points', 0)
            
            selection_text += f"**{i}.** {name} ({team}) - {position}\n"
            selection_text += f"   {games} GP, {points} pts this season\n\n"
        
        embed.description = f"Select a player by number:\n\n{selection_text}"
        embed.set_footer(text="Type a number (1-5) to select a player")
        
        await ctx.send(embed=embed)
        
        # Store selections for user
        if not hasattr(self, 'player_selections'):
            self.player_selections = {}
        self.player_selections[ctx.author.id] = players[:5]
    
    async def handle_player_selection(self, message):
        """Handle player selection from user"""
        if not hasattr(self, 'player_selections'):
            return False
            
        if message.author.id in self.player_selections and message.content.isdigit():
            selection = int(message.content)
            if 1 <= selection <= len(self.player_selections[message.author.id]):
                player = self.player_selections[message.author.id][selection-1]
                await self._show_player_stats(message.channel, player)
                del self.player_selections[message.author.id]
                return True
        return False
    
    async def _show_player_stats(self, ctx_or_channel, player_data):
        """Show detailed player statistics"""
        try:
            # Get additional player info from web API if we have player ID
            player_id = player_data.get('playerId')
            player_info = None
            
            if player_id:
                player_info = await self._get_player_info(player_id)
            
            # Create stats embed
            embed = await self._create_player_stats_embed(player_data, player_info)
            
            if hasattr(ctx_or_channel, 'send'):
                await ctx_or_channel.send(embed=embed)
            else:
                await ctx_or_channel.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error showing player stats: {e}")
            if hasattr(ctx_or_channel, 'send'):
                await ctx_or_channel.send("❌ Error retrieving player statistics.")
            else:
                await ctx_or_channel.send("❌ Error retrieving player statistics.")
    
    async def _get_player_info(self, player_id):
        """Get additional player information from web API"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api-web.nhle.com/v1/player/{player_id}/landing"
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.error(f"Error fetching player info for {player_id}: {e}")
        return None
    
    async def _create_player_stats_embed(self, stats_data, player_info):
        """Create embed with player statistics - handles both skaters and goalies"""
        name = stats_data.get('skaterFullName', 'Unknown Player')
        team_abbrevs = stats_data.get('teamAbbrevs', [])
        current_team = team_abbrevs[0] if team_abbrevs else 'N/A'
        player_type = stats_data.get('player_type', 'skater')
        
        embed = discord.Embed(
            title=f"🥅 {name}" if player_type == 'goalie' else f"🏒 {name}",
            color=0x005BB7
        )
        
        # Add player photo if available
        if player_info and 'headshot' in player_info:
            embed.set_thumbnail(url=player_info['headshot'])
        
        # Basic info
        position = stats_data.get('positionCode', 'G' if player_type == 'goalie' else 'N/A')
        jersey_num = player_info.get('sweaterNumber') if player_info else None
        
        basic_info = f"**Team:** {current_team}\n**Position:** {position}"
        if jersey_num:
            basic_info += f"\n**Number:** #{jersey_num}"
        
        # Add physical stats if available - FIXED BIRTH LOCATION PARSING
        if player_info:
            height = player_info.get('heightInInches')
            weight = player_info.get('weightInPounds')
            birth_city = player_info.get('birthCity')
            birth_country = player_info.get('birthCountry')
            
            if height:
                feet = height // 12
                inches = height % 12
                basic_info += f"\n**Height:** {feet}'{inches}\""
            if weight:
                basic_info += f"\n**Weight:** {weight} lbs"
            if birth_city and birth_country:
                # Clean up birth location - handle dictionary or string values
                if isinstance(birth_city, dict):
                    city_str = birth_city.get('default', birth_city.get('en', list(birth_city.values())[0] if birth_city else ''))
                else:
                    city_str = str(birth_city)
                
                if isinstance(birth_country, dict):
                    country_str = birth_country.get('default', birth_country.get('en', list(birth_country.values())[0] if birth_country else ''))
                else:
                    country_str = str(birth_country)
                
                basic_info += f"\n**Born:** {city_str}, {country_str}"
        
        embed.add_field(name="Player Info", value=basic_info, inline=True)
        
        if player_type == 'goalie':
            # Goalie stats
            games = stats_data.get('gamesPlayed', 0)
            wins = stats_data.get('wins', 0)
            losses = stats_data.get('losses', 0)
            ot_losses = stats_data.get('otLosses', 0)
            save_pct = stats_data.get('savePct', 0.0)
            gaa = stats_data.get('goalsAgainstAverage', 0.0)
            shutouts = stats_data.get('shutouts', 0)
            
            goalie_stats = f"**GP:** {games}\n**W:** {wins}\n**L:** {losses}\n**OTL:** {ot_losses}\n**SV%:** {save_pct:.3f}\n**GAA:** {gaa:.2f}\n**SO:** {shutouts}"
            embed.add_field(name="2024-25 Season", value=goalie_stats, inline=True)
            
            # Advanced goalie stats
            shots_against = stats_data.get('shotsAgainst', 0)
            saves = stats_data.get('saves', 0)
            goals_against = stats_data.get('goalsAgainst', 0)
            time_on_ice = stats_data.get('timeOnIce', 0.0)
            
            # Convert time on ice from minutes to hours:minutes format for goalies
            if time_on_ice > 0:
                total_minutes = int(time_on_ice)
                hours = total_minutes // 60
                minutes = total_minutes % 60
                toi_formatted = f"{hours}:{minutes:02d}" if hours > 0 else f"{minutes} min"
            else:
                toi_formatted = "0 min"
            
            advanced_stats = f"**Shots Against:** {shots_against}\n**Saves:** {saves}\n**GA:** {goals_against}\n**TOI:** {toi_formatted}"
            embed.add_field(name="Advanced Stats", value=advanced_stats, inline=True)
            
        else:
            # Skater stats (existing code)
            games = stats_data.get('gamesPlayed', 0)
            goals = stats_data.get('goals', 0)
            assists = stats_data.get('assists', 0)
            points = stats_data.get('points', 0)
            plus_minus = stats_data.get('plusMinus', 0)
            pim = stats_data.get('penaltyMinutes', 0)
            
            current_stats = f"**GP:** {games}\n**G:** {goals}\n**A:** {assists}\n**Pts:** {points}\n**+/-:** {plus_minus:+d}\n**PIM:** {pim}"
            embed.add_field(name="2024-25 Season", value=current_stats, inline=True)
            
            # Advanced stats - FIXED SHOOTING % AND TOI
            shots = stats_data.get('shots', 0)
            shooting_pct = stats_data.get('shootingPct', 0.0)
            toi_per_game = stats_data.get('timeOnIcePerGame', 0.0)
            hits = stats_data.get('hits', 0)
            blocks = stats_data.get('blockedShots', 0)
            
            # Fix shooting percentage - convert from decimal to percentage
            shooting_pct_display = shooting_pct * 100 if shooting_pct > 0 else 0.0
            
            # Fix TOI - convert from total seconds to MM:SS format
            if toi_per_game > 0:
                total_seconds = int(toi_per_game)
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                toi_formatted = f"{minutes}:{seconds:02d}"
            else:
                toi_formatted = "0:00"
            
            advanced_stats = f"**Shots:** {shots}\n**S%:** {shooting_pct_display:.1f}%\n**TOI/GP:** {toi_formatted}\n**Hits:** {hits}\n**Blocks:** {blocks}"
            embed.add_field(name="Advanced Stats", value=advanced_stats, inline=True)
            
            # Power play stats if significant - FIXED PP ASSISTS CALCULATION
            pp_goals = stats_data.get('powerPlayGoals', 0)
            pp_points = stats_data.get('powerPlayPoints', 0)  # Use the actual PP points field
            pp_assists = pp_points - pp_goals if pp_points > pp_goals else 0  # Calculate assists properly
            
            if pp_points > 0:
                pp_stats = f"**PP Goals:** {pp_goals}\n**PP Assists:** {pp_assists}\n**PP Points:** {pp_points}"
                embed.add_field(name="Power Play", value=pp_stats, inline=True)
            
            # Add pace stats if player has played games
            if games > 0:
                goals_per_game = goals / games
                points_per_game = points / games
                embed.add_field(name="Pace", value=f"**Goals/GP:** {goals_per_game:.2f}\n**Points/GP:** {points_per_game:.2f}", inline=True)
        
        embed.set_footer(text="2024-25 Regular Season Stats | NHL")
        return embed
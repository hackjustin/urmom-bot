import aiohttp
import discord
import logging
from bot.config import TEAM_ALIASES

logger = logging.getLogger('urmom-bot')

class TeamComparison:
    """Handles team comparison functionality"""
    
    def __init__(self, config):
        self.config = config
    
    async def handle_team_comparison(self, ctx, team_name):
        """Handle team comparison command"""
        # Get team ID from aliases
        team_id = TEAM_ALIASES.get(team_name.lower())
        if not team_id:
            await ctx.send(f"❌ Unknown team: `{team_name}`. Try team names like `oilers`, `edmonton`, `EDM`, etc.")
            return
        
        try:
            # Get regular season team stats
            regular_url = "https://api.nhle.com/stats/rest/en/team/summary"
            regular_params = {
                'isAggregate': 'false',
                'isGame': 'false',
                'sort': '[{"property":"points","direction":"DESC"}]',
                'start': '0',
                'limit': '32',
                'cayenneExp': 'gameTypeId=2 and seasonId<=20242025 and seasonId>=20242025'
            }
            
            async with aiohttp.ClientSession() as session:
                # Get regular season stats
                async with session.get(regular_url, params=regular_params) as response:
                    if response.status != 200:
                        await ctx.send("❌ Error fetching team stats.")
                        return
                    
                    data = await response.json()
                    teams = data.get('data', [])
                    
                    # Find Panthers and comparison team
                    panthers_stats = None
                    compare_stats = None
                    
                    for team in teams:
                        if team['teamId'] == 13:  # Panthers
                            panthers_stats = team
                        if team['teamId'] == team_id:
                            compare_stats = team
                    
                    if not panthers_stats or not compare_stats:
                        await ctx.send("❌ Could not find team stats.")
                        return
                
                # Try to get playoff stats for both teams
                playoff_url = "https://api.nhle.com/stats/rest/en/team/summary"
                playoff_params = {
                    'isAggregate': 'false',
                    'isGame': 'false',
                    'sort': '[{"property":"points","direction":"DESC"}]',
                    'start': '0',
                    'limit': '32',
                    'cayenneExp': 'gameTypeId=3 and seasonId<=20242025 and seasonId>=20242025'
                }
                
                panthers_playoff = None
                compare_playoff = None
                
                async with session.get(playoff_url, params=playoff_params) as playoff_response:
                    if playoff_response.status == 200:
                        playoff_data = await playoff_response.json()
                        playoff_teams = playoff_data.get('data', [])
                        
                        for team in playoff_teams:
                            if team['teamId'] == 13:  # Panthers
                                panthers_playoff = team
                            if team['teamId'] == team_id:
                                compare_playoff = team
                
                # Create comparison embed
                embed = await self._create_comparison_embed(
                    panthers_stats, compare_stats, 
                    panthers_playoff, compare_playoff, 
                    teams
                )
                
                await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error in team comparison: {e}")
            await ctx.send("❌ Error fetching team comparison data.")
    
    async def _create_comparison_embed(self, panthers_stats, compare_stats, panthers_playoff, compare_playoff, all_teams):
        """Create the comparison embed"""
        embed = discord.Embed(
            title=f"🏒 Team Comparison: Panthers vs {compare_stats['teamFullName']}",
            color=0xB8860B
        )
        
        # Regular Season Record comparison
        fla_record = f"{panthers_stats['wins']}-{panthers_stats['losses']}-{panthers_stats['otLosses']}"
        opp_record = f"{compare_stats['wins']}-{compare_stats['losses']}-{compare_stats['otLosses']}"
        
        embed.add_field(
            name="📊 Regular Season Record",
            value=f"**Panthers:** {fla_record} ({panthers_stats['points']} pts)\n"
                  f"**{compare_stats['teamFullName']}:** {opp_record} ({compare_stats['points']} pts)",
            inline=False
        )
        
        # Playoff Record (if available)
        if panthers_playoff and compare_playoff:
            fla_playoff_record = f"{panthers_playoff['wins']}-{panthers_playoff['losses']}"
            opp_playoff_record = f"{compare_playoff['wins']}-{compare_playoff['losses']}"
            
            embed.add_field(
                name="🏆 2025 Playoff Record",
                value=f"**Panthers:** {fla_playoff_record}\n"
                      f"**{compare_stats['teamFullName']}:** {opp_playoff_record}",
                inline=False
            )
        
        # Goals comparison (regular season)
        embed.add_field(
            name="⚽ Goals For/Against (Regular)",
            value=f"**Panthers:** {panthers_stats['goalsFor']}/{panthers_stats['goalsAgainst']}\n"
                  f"**{compare_stats['teamFullName']}:** {compare_stats['goalsFor']}/{compare_stats['goalsAgainst']}",
            inline=True
        )
        
        # Special teams (regular season)
        fla_pp = f"{panthers_stats['powerPlayPct']:.1%}"
        fla_pk = f"{panthers_stats['penaltyKillPct']:.1%}"
        opp_pp = f"{compare_stats['powerPlayPct']:.1%}"
        opp_pk = f"{compare_stats['penaltyKillPct']:.1%}"
        
        embed.add_field(
            name="⚡ Special Teams (PP/PK)",
            value=f"**Panthers:** {fla_pp}/{fla_pk}\n"
                  f"**{compare_stats['teamFullName']}:** {opp_pp}/{opp_pk}",
            inline=True
        )
        
        # Shots and faceoffs
        fla_shots = f"{panthers_stats['shotsForPerGame']:.1f}/{panthers_stats['shotsAgainstPerGame']:.1f}"
        opp_shots = f"{compare_stats['shotsForPerGame']:.1f}/{compare_stats['shotsAgainstPerGame']:.1f}"
        fla_fo = f"{panthers_stats['faceoffWinPct']:.1%}"
        opp_fo = f"{compare_stats['faceoffWinPct']:.1%}"
        
        embed.add_field(
            name="🎯 Shots/Game (For/Against)",
            value=f"**Panthers:** {fla_shots}\n"
                  f"**{compare_stats['teamFullName']}:** {opp_shots}",
            inline=True
        )
        
        embed.add_field(
            name="🥅 Faceoff Win %",
            value=f"**Panthers:** {fla_fo}\n"
                  f"**{compare_stats['teamFullName']}:** {opp_fo}",
            inline=True
        )
        
        # League rankings (approximate based on points)
        fla_rank = next(i for i, team in enumerate(all_teams, 1) if team['teamId'] == 13)
        opp_rank = next(i for i, team in enumerate(all_teams, 1) if team['teamId'] == compare_stats['teamId'])
        
        embed.add_field(
            name="🏆 League Standing",
            value=f"**Panthers:** #{fla_rank}\n"
                  f"**{compare_stats['teamFullName']}:** #{opp_rank}",
            inline=True
        )
        
        # Add playoff stats note if available
        footer_text = "Regular Season Stats • 2024-25"
        if panthers_playoff and compare_playoff:
            footer_text += " | Includes 2025 Playoff Record"
        
        embed.set_footer(text=footer_text)
        return embed
import discord
import datetime
import pytz
import random
import logging

logger = logging.getLogger('urmom-bot')

class PanthersCommands:
    """Handles all Panthers-related commands"""
    
    def __init__(self, config, panthers_manager, live_monitor, team_comparison):
        self.config = config
        self.panthers_manager = panthers_manager
        self.live_monitor = live_monitor
        self.team_comparison = team_comparison
    
    async def handle_cats_main(self, ctx):
        """Main cats command - team overview"""
        await ctx.send("🐾 Fetching Panthers info...")
        
        # Get team info and current/next game
        team_info = await self.panthers_manager.get_team_info()
        current_game = await self.panthers_manager.get_current_game()
        
        embed = discord.Embed(
            title="🐾 Florida Panthers",
            color=0xC8102E,  # Panthers red
            timestamp=datetime.datetime.now()
        )
        
        if team_info:
            record = f"{team_info.get('wins', 0)}-{team_info.get('losses', 0)}-{team_info.get('otLosses', 0)}"
            points = team_info.get('points', 0)
            games_played = team_info.get('gamesPlayed', 0)
            
            embed.add_field(name="Record", value=record, inline=True)
            embed.add_field(name="Points", value=f"{points} pts", inline=True)
            embed.add_field(name="Games Played", value=games_played, inline=True)
            
            # Division/Conference standing
            division_rank = team_info.get('divisionSequence', 'N/A')
            conference_rank = team_info.get('conferenceSequence', 'N/A')
            league_rank = team_info.get('leagueSequence', 'N/A')
            
            embed.add_field(name="Atlantic Division", value=f"#{division_rank}", inline=True)
            embed.add_field(name="Eastern Conference", value=f"#{conference_rank}", inline=True)
            embed.add_field(name="League", value=f"#{league_rank}", inline=True)
        
        # Add game info
        await self._add_game_info_to_embed(embed, current_game)
        
        embed.add_field(
            name="Commands", 
            value="`!cats quote` - Random player quote\n`!cats game` - Detailed game info\n`!cats recent` - Recent games\n`!cats vs <team>` - Team comparison\n`!cats player <n>` - Player stats\n`!cats live on/off/status` - 🚨 Live updates\n`!cats help` - All commands", 
            inline=False
        )
        embed.set_footer(text="Go Panthers! 🐾")
        
        await ctx.send(embed=embed)
    
    async def _add_game_info_to_embed(self, embed, current_game):
        """Add current/next game info to embed"""
        if current_game:
            home_team = current_game.get('homeTeam', {})
            away_team = current_game.get('awayTeam', {})
            game_state = current_game.get('gameState', '')
            venue = current_game.get('venue', {}).get('default', '')
            
            series_status = current_game.get('seriesStatus', {})
            series_title = series_status.get('seriesTitle', '')
            
            if game_state in ['LIVE', 'CRIT']:
                home_score = home_team.get('score', 0)
                away_score = away_team.get('score', 0)
                period = current_game.get('periodDescriptor', {}).get('number', '')
                time_remaining = current_game.get('clock', {}).get('timeRemaining', '')
                
                game_info = f"🔴 **LIVE GAME**"
                if series_title:
                    game_info += f" - {series_title}"
                game_info += f"\n{away_team.get('abbrev', 'AWAY')} {away_score} - {home_score} {home_team.get('abbrev', 'HOME')}\n"
                game_info += f"Period {period} - {time_remaining}"
                if venue:
                    game_info += f"\n📍 {venue}"
                
                embed.add_field(name="Current Game", value=game_info, inline=False)
            else:
                # Format upcoming game
                game_info = self._format_upcoming_game(current_game, home_team, away_team, series_title, venue)
                embed.add_field(name="Game Info", value=game_info, inline=False)
        else:
            # Get next game
            next_game = await self.panthers_manager.get_next_game()
            if next_game:
                home_team = next_game.get('homeTeam', {})
                away_team = next_game.get('awayTeam', {})
                venue = next_game.get('venue', {}).get('default', '')
                series_status = next_game.get('seriesStatus', {})
                series_title = series_status.get('seriesTitle', '')
                
                game_info = self._format_upcoming_game(next_game, home_team, away_team, series_title, venue)
                embed.add_field(name="Upcoming", value=game_info, inline=False)
    
    def _format_upcoming_game(self, game, home_team, away_team, series_title, venue):
        """Format upcoming game information"""
        game_date_str = game.get('gameDate', '')
        game_time = game.get('startTimeUTC', '')
        today_est = datetime.datetime.now(pytz.timezone('US/Eastern'))
        formatted_date_time = "Today"
        
        if game_date_str:
            try:
                if 'T' in game_date_str:
                    game_date = datetime.datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
                else:
                    date_part = datetime.datetime.strptime(game_date_str, '%Y-%m-%d')
                    game_date = pytz.utc.localize(date_part)
                
                est_date = game_date.astimezone(pytz.timezone('US/Eastern'))
                is_today = est_date.date() == today_est.date()
                
                if is_today:
                    formatted_date_time = "Today"
                else:
                    formatted_date_time = est_date.strftime('%b %d')
            except ValueError:
                formatted_date_time = "Today"
        
        # Add time if available
        if game_time:
            try:
                game_dt = datetime.datetime.fromisoformat(game_time.replace('Z', '+00:00'))
                est_time = game_dt.astimezone(pytz.timezone('US/Eastern'))
                formatted_time = est_time.strftime('%I:%M %p ET')
                formatted_date_time += f" @ {formatted_time}"
            except ValueError:
                pass
        
        opponent = away_team.get('abbrev', '') if home_team.get('id') == self.config.PANTHERS_TEAM_ID else home_team.get('abbrev', '')
        location = "HOME" if home_team.get('id') == self.config.PANTHERS_TEAM_ID else "AWAY"
        
        game_info = f"🏒 **NEXT GAME** - {formatted_date_time}\n"
        
        second_line = ""
        if series_title:
            second_line += f"{series_title} "
        second_line += f"vs {opponent} ({location})"
        game_info += second_line
        
        if venue:
            game_info += f"\n📍 {venue}"
        
        return game_info
    
    async def handle_cats_quote(self, ctx):
        """Random Panthers quote"""
        quote = random.choice(self.config.PANTHERS_QUOTES)
        embed = discord.Embed(
            title="🐾 Panthers Quote",
            description=quote,
            color=0xC8102E
        )
        await ctx.send(embed=embed)
    
    async def handle_cats_game(self, ctx):
        """Detailed game information"""
        current_game = await self.panthers_manager.get_current_game()
        
        if not current_game:
            next_game = await self.panthers_manager.get_next_game()
            if next_game:
                await self._show_next_game_details(ctx, next_game)
            else:
                await ctx.send("No upcoming games found!")
            return
        
        await self._show_current_game_details(ctx, current_game)
    
    async def _show_next_game_details(self, ctx, next_game):
        """Show detailed next game information"""
        embed = discord.Embed(
            title="🏒 Next Panthers Game",
            color=0xC8102E
        )
        
        # Parse game date and time
        game_date_str = next_game.get('gameDate', '')
        formatted_date = "Date TBD"
        formatted_date_short = "TBD"
        
        if game_date_str:
            try:
                if 'T' in game_date_str:
                    game_date = datetime.datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
                else:
                    date_part = datetime.datetime.strptime(game_date_str, '%Y-%m-%d')
                    game_date = pytz.utc.localize(date_part)
                
                est_date = game_date.astimezone(pytz.timezone('US/Eastern'))
                formatted_date = est_date.strftime('%A, %B %d at %I:%M %p ET')
                formatted_date_short = est_date.strftime('%B %d, %Y')
                
                today_est = datetime.datetime.now(pytz.timezone('US/Eastern')).date()
                if est_date.date() == today_est:
                    formatted_date_short = "Today"
            except ValueError:
                pass
        
        home_team = next_game.get('homeTeam', {})
        away_team = next_game.get('awayTeam', {})
        opponent = away_team.get('abbrev', '') if home_team.get('id') == self.config.PANTHERS_TEAM_ID else home_team.get('abbrev', '')
        location = "🏠 HOME" if home_team.get('id') == self.config.PANTHERS_TEAM_ID else "✈️ AWAY"
        venue = next_game.get('venue', {}).get('default', '')
        
        series_status = next_game.get('seriesStatus', {})
        series_title = series_status.get('seriesTitle', '')
        
        embed.add_field(name="Date", value=formatted_date_short, inline=True)
        embed.add_field(name="Opponent", value=f"vs {opponent}", inline=True)
        embed.add_field(name="Location", value=location, inline=True)
        
        if series_title:
            embed.add_field(name="Series", value=series_title, inline=False)
        
        embed.add_field(name="Game Time", value=formatted_date, inline=False)
        if venue:
            embed.add_field(name="Venue", value=f"📍 {venue}", inline=False)
        
        await ctx.send(embed=embed)
    
    async def _show_current_game_details(self, ctx, current_game):
        """Show detailed current game information"""
        embed = discord.Embed(
            title="🏒 Panthers Game",
            color=0xC8102E
        )
        
        home_team = current_game.get('homeTeam', {})
        away_team = current_game.get('awayTeam', {})
        game_state = current_game.get('gameState', '')
        
        opponent = away_team.get('abbrev', '') if home_team.get('id') == self.config.PANTHERS_TEAM_ID else home_team.get('abbrev', '')
        location = "🏠 HOME" if home_team.get('id') == self.config.PANTHERS_TEAM_ID else "✈️ AWAY"
        
        series_status = current_game.get('seriesStatus', {})
        series_title = series_status.get('seriesTitle', '')
        
        # Determine date display
        formatted_date_short = self._get_game_date_display(current_game)
        
        embed.add_field(name="Date", value=formatted_date_short, inline=True)
        embed.add_field(name="Opponent", value=f"vs {opponent}", inline=True)
        embed.add_field(name="Location", value=location, inline=True)
        
        if series_title:
            embed.add_field(name="Series", value=series_title, inline=False)
        
        if game_state in ['LIVE', 'CRIT']:
            home_score = home_team.get('score', 0)
            away_score = away_team.get('score', 0)
            period = current_game.get('periodDescriptor', {}).get('number', '')
            
            score_display = f"{away_team.get('abbrev', 'AWAY')} {away_score} - {home_score} {home_team.get('abbrev', 'HOME')}"
            embed.add_field(name="🔴 LIVE SCORE", value=score_display, inline=False)
            embed.add_field(name="Period", value=period, inline=True)
            
            # Add shots if available
            home_shots = home_team.get('sog', 0)
            away_shots = away_team.get('sog', 0)
            if home_shots or away_shots:
                shots_display = f"{away_team.get('abbrev', 'AWAY')} {away_shots} - {home_shots} {home_team.get('abbrev', 'HOME')}"
                embed.add_field(name="Shots on Goal", value=shots_display, inline=False)
        else:
            # Pre-game - show game time
            game_time = current_game.get('startTimeUTC', '')
            if game_time:
                try:
                    formatted_time = est_time.strftime('%I:%M %p ET')
                    embed.add_field(name="Game Time", value=formatted_time, inline=True)
                except ValueError:
                    embed.add_field(name="Game Time", value="Time TBD", inline=True)
            else:
                embed.add_field(name="Game Time", value="Time TBD", inline=True)
        
        venue = current_game.get('venue', {}).get('default', '')
        if venue:
            embed.add_field(name="Venue", value=f"📍 {venue}", inline=False)
        
        await ctx.send(embed=embed)
    
    def _get_game_date_display(self, game):
        """Get formatted game date display"""
        game_date_str = game.get('gameDate', '')
        today_est = datetime.datetime.now(pytz.timezone('US/Eastern'))
        
        if game_date_str:
            try:
                if 'T' in game_date_str:
                    game_date = datetime.datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
                else:
                    date_part = datetime.datetime.strptime(game_date_str, '%Y-%m-%d')
                    game_date = pytz.utc.localize(date_part)
                
                est_date = game_date.astimezone(pytz.timezone('US/Eastern'))
                
                if est_date.date() == today_est.date():
                    return "Today"
                else:
                    return est_date.strftime('%B %d, %Y')
            except ValueError:
                return "Today"
        else:
            return "Today"
    
    async def handle_cats_recent(self, ctx):
        """Recent Panthers games"""
        await ctx.send("📊 Getting recent Panthers games...")
        
        recent_games = await self.panthers_manager.get_recent_games()
        
        if not recent_games:
            await ctx.send("No recent games found!")
            return
        
        embed = discord.Embed(
            title="🐾 Recent Panthers Games",
            color=0xC8102E
        )
        
        for game in recent_games[:5]:  # Last 5 games
            home_team = game.get('homeTeam', {})
            away_team = game.get('awayTeam', {})
            
            game_date = datetime.datetime.fromisoformat(game.get('gameDate', '').replace('Z', '+00:00'))
            formatted_date = game_date.strftime('%m/%d')
            
            home_score = home_team.get('score', 0)
            away_score = away_team.get('score', 0)
            
            # Determine if Panthers won
            panthers_home = home_team.get('id') == self.config.PANTHERS_TEAM_ID
            panthers_score = home_score if panthers_home else away_score
            opponent_score = away_score if panthers_home else home_score
            opponent = away_team.get('abbrev', '') if panthers_home else home_team.get('abbrev', '')
            
            result = "W" if panthers_score > opponent_score else "L"
            result_emoji = "✅" if result == "W" else "❌"
            location = "vs" if panthers_home else "@"
            
            game_summary = f"{result_emoji} {result} {panthers_score}-{opponent_score} {location} {opponent}"
            embed.add_field(name=formatted_date, value=game_summary, inline=False)
        
        await ctx.send(embed=embed)
    
    async def handle_cats_live(self, ctx, action):
        """Handle live game updates toggle"""
        if not action:
            await ctx.send("Usage: `!cats live on/off/status`\n"
                          "- `!cats live on` - Enable live score updates in this channel\n"
                          "- `!cats live off` - Disable live score updates\n"
                          "- `!cats live status` - Check current status")
            return
        
        channel_id = ctx.channel.id
        
        if action.lower() == 'on':
            self.live_monitor.add_channel(channel_id)
            embed = discord.Embed(
                title="🚨 Live Updates Enabled!",
                description="This channel will now receive live Panthers game updates including:\n"
                           "• Goal notifications 🚨\n"
                           "• Period changes 🏒\n"
                           "• Game end results 🎉\n\n"
                           "Use `!cats live off` to disable.",
                color=0xC8102E
            )
            await ctx.send(embed=embed)
            
        elif action.lower() == 'off':
            self.live_monitor.remove_channel(channel_id)
            embed = discord.Embed(
                title="🔇 Live Updates Disabled",
                description="This channel will no longer receive live Panthers game updates.\n"
                           "Use `!cats live on` to re-enable.",
                color=0x808080
            )
            await ctx.send(embed=embed)
            
        elif action.lower() == 'status':
            is_enabled = self.live_monitor.is_channel_subscribed(channel_id)
            status = "🟢 **ENABLED**" if is_enabled else "🔴 **DISABLED**"
            
            embed = discord.Embed(
                title="📊 Live Updates Status",
                description=f"Live Panthers updates: {status}\n\n"
                           f"Total channels with live updates: {len(self.live_monitor.live_channels)}",
                color=0xC8102E if is_enabled else 0x808080
            )
            
            # Show when next game monitoring will be active
            current_game = await self.panthers_manager.get_current_game()
            if current_game:
                game_state = current_game.get('gameState', '')
                if game_state in ['LIVE', 'CRIT']:
                    embed.add_field(name="🔴 Current Status", value="Game is LIVE - monitoring active!", inline=False)
                else:
                    embed.add_field(name="🏒 Current Status", value="Game today but not started - ready to monitor!", inline=False)
            else:
                next_game = await self.panthers_manager.get_next_game()
                if next_game:
                    embed.add_field(name="⏰ Next Monitoring", value="Will activate when next Panthers game goes live", inline=False)
            
            await ctx.send(embed=embed)
            
        else:
            await ctx.send("Invalid option. Use `on`, `off`, or `status`.")
    
    async def handle_cats_help(self, ctx):
        """Panthers commands help"""
        embed = discord.Embed(
            title="🐾 Panthers Commands",
            color=0xC8102E,
            description="All available Panthers commands"
        )
        
        commands_info = [
            ("`!cats`", "Team overview, standings, and next/current game"),
            ("`!cats quote`", "Random player or coach quote"),
            ("`!cats game`", "Detailed current or next game information"),
            ("`!cats recent`", "Last 5 Panthers games with results"),
            ("`!cats vs <team>`", "Team comparison with detailed stats"),
            ("`!cats player <name>`", "NHL player stats lookup"),
            ("`!cats live on/off/status`", "🚨 Toggle live game updates"),
            ("`!cats help`", "This help message")
        ]
        
        for cmd, desc in commands_info:
            embed.add_field(name=cmd, value=desc, inline=False)
        
        embed.set_footer(text="Go Panthers! 🐾")
        await ctx.send(embed=embed)
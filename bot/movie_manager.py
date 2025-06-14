import os
import aiohttp
import discord
import logging
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger('urmom-bot')

class MovieManager:
    """Handles movie search functionality"""
    
    def __init__(self, config):
        self.config = config
        self.movie_selections = {}  # Store user movie selections
        self.selection_timestamps = {}  # Track when selections were made
        self.omdb_api_key = os.getenv('OMDB_API_KEY')
        self.session = None  # Reusable aiohttp session
        self.selection_timeout = 300  # 5 minutes timeout for selections
    
    async def search_movie(self, ctx, query):
        """Search for a movie"""
        if not self.omdb_api_key:
            await ctx.send("OMDB API key is not configured. Please set the OMDB_API_KEY environment variable.")
            return
        
        # Clean up expired selections before processing
        self._cleanup_expired_selections()
        
        # Validate input
        if not self._validate_query(query):
            await ctx.send("Please provide a valid movie title (2-100 characters, no special characters).")
            return
            
        session = await self._get_session()
        try:
            params = {
                'apikey': self.omdb_api_key,
                's': query.strip(),
                'type': 'movie'
            }
            timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout
            async with session.get(self.config.OMDB_API_URL, params=params, timeout=timeout) as response:
                if response.status != 200:
                    await ctx.send(f"Error: Could not fetch movie data (Status code: {response.status})")
                    return
                
                data = await response.json()
                
                if data.get('Response') == 'False':
                    error_msg = data.get('Error', 'No movies found')
                    await ctx.send(f"No movies found for '{query}': {error_msg}")
                    return
                
                results = data.get('Search', [])
                if len(results) == 1:
                    # Single result, get detailed info
                    movie = results[0]
                    await self.send_movie_details(ctx, movie['imdbID'])
                else:
                    # Multiple results, show selection
                    await self._show_movie_selection(ctx, session, results)
        
        except asyncio.TimeoutError:
            await ctx.send("⏰ Request timed out. Please try again.")
        except aiohttp.ClientError as e:
            logger.error(f"Network error in movie search: {e}")
            await ctx.send("❌ Network error occurred. Please try again later.")
        except Exception as e:
            logger.error(f"Unexpected error in movie search: {e}")
            await ctx.send("❌ An unexpected error occurred. Please try again.")
    
    async def _show_movie_selection(self, ctx, session, results):
        """Show movie selection menu"""
        selection_msg = "**Found multiple movies. Please select one by number:**\n\n"
        
        # Get more details for each movie
        detailed_results = []
        for movie in results[:10]:  # Limit to 10 results
            movie_id = movie['imdbID']
            params = {
                'apikey': self.omdb_api_key,
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
            
            selection_msg += f"**{i+1}.** {movie['Title']} ({year})\n"
            selection_msg += f"   Actors: {actors_str}\n"
            selection_msg += f"   Director: {director}\n\n"
        
        # Store the results for selection with timestamp
        self.movie_selections[ctx.author.id] = [movie['imdbID'] for movie in results[:10]]
        self.selection_timestamps[ctx.author.id] = datetime.now()
        await ctx.send(selection_msg)
    
    async def handle_movie_selection(self, message):
        """Handle movie selection from user"""
        # Clean up expired selections
        self._cleanup_expired_selections()
        
        if message.author.id in self.movie_selections and message.content.isdigit():
            try:
                selection = int(message.content)
                if 1 <= selection <= len(self.movie_selections[message.author.id]):
                    movie_id = self.movie_selections[message.author.id][selection-1]
                    await self.send_movie_details(message.channel, movie_id)
                    # Clean up this user's selection
                    self._cleanup_user_selection(message.author.id)
                    return True
            except (ValueError, IndexError):
                pass
        return False
    
    async def send_movie_details(self, channel, imdb_id):
        """Send detailed information about a movie"""
        if not self.omdb_api_key:
            await channel.send("OMDB API key is not configured.")
            return
            
        session = await self._get_session()
        try:
            params = {
                'apikey': self.omdb_api_key,
                'i': imdb_id,
                'plot': 'full'
            }
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(self.config.OMDB_API_URL, params=params, timeout=timeout) as response:
                if response.status != 200:
                    await channel.send(f"Error: Could not fetch movie details (Status code: {response.status})")
                    return
                
                data = await response.json()
                
                if data.get('Response') == 'False':
                    error_msg = data.get('Error', 'Could not find movie details')
                    await channel.send(f"Could not find movie details: {error_msg}")
                    return
                
                # Create an embed for the movie
                embed = self._create_movie_embed(data)
                await channel.send(embed=embed)
        
        except asyncio.TimeoutError:
            await channel.send("⏰ Request timed out. Please try again.")
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching movie details: {e}")
            await channel.send("❌ Network error occurred. Please try again later.")
        except Exception as e:
            logger.error(f"Unexpected error fetching movie details: {e}")
            await channel.send("❌ An unexpected error occurred. Please try again.")
    
    def _create_movie_embed(self, data):
        """Create Discord embed for movie data"""
        embed = discord.Embed(
            title=data.get('Title', 'Unknown Title'),
            description=data.get('Plot', 'No plot available'),
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
        
        # Truncate writer field if too long
        writer = data.get('Writer', 'N/A')
        if len(writer) > 1024:
            writer = writer[:1021] + '...'
        embed.add_field(name="Writer", value=writer, inline=True)
        
        embed.add_field(name="Actors", value=data.get('Actors', 'N/A'), inline=True)
        embed.add_field(name="Language", value=data.get('Language', 'N/A'), inline=True)
        embed.add_field(name="Country", value=data.get('Country', 'N/A'), inline=True)
        
        # Add ratings
        ratings = data.get('Ratings', [])
        if ratings:
            ratings_text = ""
            for rating in ratings:
                source = rating.get('Source', 'Unknown')
                value = rating.get('Value', 'N/A')
                ratings_text += f"{source}: {value}\n"
            embed.add_field(name="Ratings", value=ratings_text, inline=False)
        
        # Add footer with IMDB ID
        embed.set_footer(text=f"IMDB ID: {data.get('imdbID', 'Unknown')} | Powered by OMDB API")
        
        return embed
    
    async def _get_session(self):
        """Get or create reusable aiohttp session"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'User-Agent': 'urmom-bot/1.0'}
            )
        return self.session
    
    def _validate_query(self, query):
        """Validate movie search query"""
        if not query or not isinstance(query, str):
            return False
        
        query = query.strip()
        if len(query) < 2 or len(query) > 100:
            return False
        
        # Allow letters, numbers, spaces, and basic punctuation
        import re
        if not re.match(r"^[a-zA-Z0-9\s\-\.,!?\':&]+$", query):
            return False
        
        return True
    
    def _cleanup_expired_selections(self):
        """Remove expired movie selections to prevent memory leaks"""
        current_time = datetime.now()
        expired_users = []
        
        for user_id, timestamp in self.selection_timestamps.items():
            if current_time - timestamp > timedelta(seconds=self.selection_timeout):
                expired_users.append(user_id)
        
        for user_id in expired_users:
            self._cleanup_user_selection(user_id)
    
    def _cleanup_user_selection(self, user_id):
        """Clean up a specific user's movie selection"""
        self.movie_selections.pop(user_id, None)
        self.selection_timestamps.pop(user_id, None)
    
    async def cleanup(self):
        """Clean up resources when shutting down"""
        if self.session and not self.session.closed:
            await self.session.close()
        self.movie_selections.clear()
        self.selection_timestamps.clear()
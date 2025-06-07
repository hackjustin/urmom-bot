import os
import aiohttp
import discord
import logging

logger = logging.getLogger('urmom-bot')

class MovieManager:
    """Handles movie search functionality"""
    
    def __init__(self, config):
        self.config = config
        self.movie_selections = {}  # Store user movie selections
        self.omdb_api_key = os.getenv('OMDB_API_KEY')
    
    async def search_movie(self, ctx, query):
        """Search for a movie"""
        if not self.omdb_api_key:
            await ctx.send("OMDB API key is not configured. Please set the OMDB_API_KEY environment variable.")
            return
            
        async with aiohttp.ClientSession() as session:
            params = {
                'apikey': self.omdb_api_key,
                's': query,
                'type': 'movie'
            }
            async with session.get(self.config.OMDB_API_URL, params=params) as response:
                if response.status != 200:
                    await ctx.send(f"Error: Could not fetch movie data (Status code: {response.status})")
                    return
                
                data = await response.json()
                
                if data.get('Response') == 'False':
                    await ctx.send(f"No movies found for '{query}'.")
                    return
                
                results = data.get('Search', [])
                if len(results) == 1:
                    # Single result, get detailed info
                    movie = results[0]
                    await self.send_movie_details(ctx, movie['imdbID'])
                else:
                    # Multiple results, show selection
                    await self._show_movie_selection(ctx, session, results)
    
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
        
        # Store the results for selection
        self.movie_selections[ctx.author.id] = [movie['imdbID'] for movie in results[:10]]
        await ctx.send(selection_msg)
    
    async def handle_movie_selection(self, message):
        """Handle movie selection from user"""
        if message.author.id in self.movie_selections and message.content.isdigit():
            selection = int(message.content)
            if 1 <= selection <= len(self.movie_selections[message.author.id]):
                movie_id = self.movie_selections[message.author.id][selection-1]
                await self.send_movie_details(message.channel, movie_id)
                del self.movie_selections[message.author.id]
                return True
        return False
    
    async def send_movie_details(self, channel, imdb_id):
        """Send detailed information about a movie"""
        if not self.omdb_api_key:
            await channel.send("OMDB API key is not configured.")
            return
            
        async with aiohttp.ClientSession() as session:
            params = {
                'apikey': self.omdb_api_key,
                'i': imdb_id,
                'plot': 'full'
            }
            async with session.get(self.config.OMDB_API_URL, params=params) as response:
                if response.status != 200:
                    await channel.send(f"Error: Could not fetch movie details (Status code: {response.status})")
                    return
                
                data = await response.json()
                
                if data.get('Response') == 'False':
                    await channel.send(f"Could not find movie details.")
                    return
                
                # Create an embed for the movie
                embed = discord.Embed(
                    title=data.get('Title'),
                    description=data.get('Plot'),
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
                embed.add_field(name="Writer", value=data.get('Writer', 'N/A')[:1024] if data.get('Writer') else 'N/A', inline=True)
                embed.add_field(name="Actors", value=data.get('Actors', 'N/A'), inline=True)
                embed.add_field(name="Language", value=data.get('Language', 'N/A'), inline=True)
                embed.add_field(name="Country", value=data.get('Country', 'N/A'), inline=True)
                
                # Add ratings
                ratings = data.get('Ratings', [])
                ratings_text = ""
                for rating in ratings:
                    ratings_text += f"{rating.get('Source')}: {rating.get('Value')}\n"
                
                if ratings_text:
                    embed.add_field(name="Ratings", value=ratings_text, inline=False)
                
                # Add footer with IMDB ID
                embed.set_footer(text=f"IMDB ID: {data.get('imdbID')} | Powered by OMDB API")
                
                await channel.send(embed=embed)
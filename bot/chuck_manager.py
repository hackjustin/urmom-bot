import aiohttp
import logging

logger = logging.getLogger('urmom-bot')

CHUCK_API_BASE = "https://api.chucknorris.io"


class ChuckManager:
    """Manager for Chuck Norris joke commands using the chucknorris.io API."""

    def __init__(self):
        self._categories = None

    async def fetch_categories(self):
        """Fetch and cache available joke categories."""
        if self._categories is not None:
            return self._categories
        try:
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(f"{CHUCK_API_BASE}/jokes/categories", timeout=timeout) as resp:
                    if resp.status == 200:
                        self._categories = await resp.json()
                        return self._categories
        except Exception as e:
            logger.error(f"Error fetching Chuck Norris categories: {e}")
        return None

    async def fetch_random_joke(self, category=None):
        """Fetch a random Chuck Norris joke, optionally filtered by category."""
        try:
            params = {}
            if category:
                params["category"] = category.lower().strip()
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(f"{CHUCK_API_BASE}/jokes/random", params=params, timeout=timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("value")
                    elif resp.status == 404:
                        return None
        except Exception as e:
            logger.error(f"Error fetching Chuck Norris joke: {e}")
        return None

    async def handle_chuck(self, ctx, subcommand=None):
        """Handle the !chuck command."""
        if subcommand and subcommand.lower() == "help":
            await self.handle_help(ctx)
            return

        # Treat subcommand as a category if provided
        category = subcommand
        if category:
            categories = await self.fetch_categories()
            if categories and category.lower().strip() not in categories:
                cats = ", ".join(f"`{c}`" for c in sorted(categories))
                await ctx.send(f"Unknown category `{category}`. Available categories:\n{cats}")
                return

        joke = await self.fetch_random_joke(category)
        if joke:
            await ctx.send(joke)
        else:
            await ctx.send("Chuck Norris is too powerful for the API right now. Try again later.")

    async def handle_help(self, ctx):
        """Show help for the !chuck command."""
        categories = await self.fetch_categories()
        cats = ", ".join(f"`{c}`" for c in sorted(categories)) if categories else "_Could not load categories._"
        help_text = (
            "**!chuck** - Get a random Chuck Norris joke\n"
            "**!chuck <category>** - Get a joke from a specific category\n"
            "**!chuck help** - Show this help message\n\n"
            f"**Available categories:** {cats}"
        )
        await ctx.send(help_text)

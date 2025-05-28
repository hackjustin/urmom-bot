# Urmom Discord Bot

A feature-rich Discord bot that responds to specific phrases with GIFs and reactions, provides movie information, offers a reminder system, and delivers real-time Florida Panthers NHL updates.

## Features

### Core Features
- Responds to "ur mom" or "your mom" mentions with a GIF
- Reacts to messages containing "alot" with emoji letters spelling "ALOT"
- Responds to `!mom` command with text
- Movie lookup via IMDB/OMDB API with the `!movie` command
- Reminder system that lets users set reminders with the `!remind` command

### 🐾 Florida Panthers Features
- **Team Overview**: Current standings, record, and next/live game info
- **Live Game Updates**: Real-time scores, period information, and game status
- **Game Details**: Comprehensive current and upcoming game information
- **Recent Games**: Last 5 Panthers games with results
- **Player Quotes**: Random inspirational quotes from Panthers players and coaches

## Setup

### Prerequisites
- Docker and Docker Compose installed
- A Discord bot token (from Discord Developer Portal)
- OMDB API key (from OMDB API) for movie lookups

### Configuration
1. Edit the `.env` file with your credentials:
```env
DISCORD_TOKEN=your_discord_token_here
OMDB_API_KEY=your_omdb_api_key_here
```

2. Configure bot behavior in the `BotConfig` class in `urmom-bot.py`

### Building and Running with Docker
```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

## Project Structure
```
.
├── gifs/                  # Directory for GIF files
│   ├── alot.gif
│   └── ur-mom.gif
├── urmom-bot.py          # Main bot code
├── .env                  # Environment variables
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker build instructions
└── docker-compose.yml   # Docker Compose configuration
```

## Commands

### General Commands

#### `!mom`
A simple command that responds with "what...?"

#### `!movie [title]`
Searches for movies matching the given title. If multiple matches are found, displays a list with details including actors, director, and studio for selection.

**Example:**
```
!movie The Matrix
```

#### `!remind [time] [message]`
Sets a reminder for the specified time.

**Time formats:**
- Relative time: `5 minutes`, `2 hours`, `1 day`, etc.
- Absolute time: `at 5pm`, `tomorrow at 9am`, etc.

If replying to another message, the reminder will include that message.

**Examples:**
```
!remind 15 minutes Check the oven
!remind at 5pm Call mom
!remind tomorrow at 9am Team meeting
```

### 🐾 Panthers Commands

#### `!cats`
Shows comprehensive team overview including:
- Current season record (W-L-OT)
- Points and standings in Atlantic Division, Eastern Conference, and League
- **Live game status** with current score and period (if game is active)
- **Next game details** with opponent, date, time, and venue (if no live game)
- Quick access to other Panthers commands

#### `!cats quote`
Displays a random inspirational quote from Panthers players or coaches.

#### `!cats game`
Provides detailed information about:
- **Current game**: Live score, period, time remaining, shots on goal
- **Next game**: Opponent, date/time, venue, home/away status

#### `!cats recent`
Shows the last 5 Panthers games with:
- Game date
- Final score
- Win/Loss result
- Opponent and home/away status

#### `!cats help`
Lists all available Panthers commands with descriptions.

## API Integration

### NHL API
The bot uses the official NHL API to provide:
- Real-time game scores and statistics
- Team standings and records
- Schedule information
- Player and team data

**No API key required** - the NHL API is free to use.

### OMDB API
Used for movie lookups. Requires a free API key from [OMDB API](http://www.omdbapi.com/).

## Adding New Features

### For new commands:
Add them with the `@self.command()` decorator in the `add_commands()` method:

```python
@self.command(name='newcommand')
async def new_command(ctx):
    """Description of the command"""
    await ctx.send("Your response here")
```

### For configuration options:
Add them to the `BotConfig` class:

```python
class BotConfig:
    # Your new configuration option
    NEW_FEATURE_ENABLED = True
```

### For new automatic responses:
Add them in the `on_message` event handler:

```python
if "some phrase" in message.content.lower():
    await message.channel.send("Your response here")
```

### Expanding Panthers Features

#### Adding More Quotes
Add new quotes to the `PANTHERS_QUOTES` list in the `BotConfig` class:

```python
PANTHERS_QUOTES = [
    "\"Your new quote here.\" - Player Name",
    # ... existing quotes
]
```

#### Adding New Panthers Commands
Follow the pattern established in the `cats_command` function to add new subcommands.

## Error Handling

The bot includes comprehensive error handling for:
- API failures (NHL and OMDB)
- Network timeouts
- Invalid user input
- Missing configuration

Errors are logged for debugging while providing user-friendly messages in Discord.

## Time Zone Support

All Panthers game times are automatically converted to Eastern Time (US/Eastern) for accurate Florida-based scheduling.

## Contributing

When adding new features:
1. Follow the existing code structure and patterns
2. Add appropriate error handling
3. Update this README with new commands/features
4. Test thoroughly before deployment

## License

This project is for personal/educational use.
# Urmom Discord Bot

A feature-rich Discord bot that responds to specific phrases with GIFs and reactions, provides movie information, offers a reminder system, and delivers **real-time Florida Panthers NHL updates with live score monitoring**.

## Features

### Core Features
- Responds to "ur mom" or "your mom" mentions with a GIF
- Reacts to messages containing "alot" with emoji letters spelling "ALOT"
- Responds to `!mom` command with text
- Movie lookup via IMDB/OMDB API with the `!movie` command
- Reminder system that lets users set reminders with the `!remind` command

### 🐾 Florida Panthers Features
- **Team Overview**: Current standings, record, and next/live game info
- **🚨 Live Game Monitoring**: Real-time goal notifications, period changes, and game updates
- **Live Score Updates**: Automatic score change announcements during games
- **Game Details**: Comprehensive current and upcoming game information
- **Recent Games**: Last 5 Panthers games with results
- **Player Quotes**: Random inspirational quotes from Panthers players and coaches
- **Channel-Based Controls**: Each Discord channel can independently enable/disable live updates

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

#### `!cats live [on/off/status]` 🚨 **NEW!**
Controls live game updates for the current channel:
- **`!cats live on`** - Enable real-time score updates, goal notifications, and period changes
- **`!cats live off`** - Disable live updates for this channel
- **`!cats live status`** - Check if live updates are enabled and monitoring status

**Live Update Features:**
- 🚨 **Goal Notifications**: Instant alerts when goals are scored (extra excitement for Panthers goals!)
- 🏒 **Period Changes**: Notifications when periods start
- 🎉 **Game Results**: Final score announcements when games end
- ⚡ **Smart Timing**: Only monitors during game hours, checks every 30 seconds during live games

#### `!cats help`
Lists all available Panthers commands with descriptions.

## 🚨 Live Game Monitoring

The bot includes an advanced live game monitoring system that:

### **Automatic Detection**
- Monitors NHL API every 30 seconds during prime game hours (6 PM - 11 PM ET)
- Automatically detects when Panthers games go live
- Tracks score changes, period transitions, and game endings

### **Smart Notifications**
- **Panthers Goals**: `🚨 PANTHERS GOAL! 🚨` with enhanced formatting
- **Opponent Goals**: Standard goal notification
- **Period Changes**: `🏒 Period 2 Starting`
- **Game Endings**: `🎉 PANTHERS WIN!` or `😞 Game Over`

### **Channel Management**
- Each Discord channel controls its own live update preferences
- Multiple channels can have different settings
- Automatic cleanup of invalid channels

### **Example Live Updates**
```
🚨 PANTHERS GOAL! 🚨
FLA 2 - 1 CAR
Period 2 - 15:23

🏒 Period 3 Starting
FLA 2 - 1 CAR

🎉 PANTHERS WIN! 🎉
Final: FLA 3 - 1 CAR
```

## API Integration

### NHL API
The bot uses the official NHL API to provide:
- Real-time game scores and statistics
- Live game state monitoring
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

#### Customizing Live Updates
Modify the live monitoring behavior in the `live_game_monitor()` and related methods:
- Adjust monitoring frequency
- Add new types of notifications
- Customize message formatting
- Add team-specific celebrations

## Background Tasks

The bot runs several background tasks:
- **Reminder System**: Checks for due reminders every 10 seconds
- **Live Game Monitor**: Monitors Panthers games every 30 seconds during game hours
- **Smart Scheduling**: Reduces API calls during off-hours to improve performance

## Error Handling

The bot includes comprehensive error handling for:
- API failures (NHL and OMDB)
- Network timeouts
- Invalid user input
- Missing configuration
- Live monitoring interruptions
- Channel management issues

Errors are logged for debugging while providing user-friendly messages in Discord.

## Time Zone Support

All Panthers game times are automatically converted to Eastern Time (US/Eastern) for accurate Florida-based scheduling. Live monitoring respects EST/EDT transitions.

## Performance Optimization

- **Smart API Usage**: Reduces polling frequency during non-game hours
- **Efficient Channel Management**: Automatically removes invalid channels
- **Memory Management**: Cleans up game state data after games end
- **Error Recovery**: Continues monitoring even if individual API calls fail

## Contributing

When adding new features:
1. Follow the existing code structure and patterns
2. Add appropriate error handling
3. Update this README with new commands/features
4. Test thoroughly, especially live monitoring features
5. Consider performance impact of background tasks

## License

This project is for personal/educational use.

---

## 🏒 Perfect for Panthers Fans!

This bot is specifically designed for Florida Panthers fans who want:
- **Real-time playoff updates** during Conference Finals and Stanley Cup runs
- **Comprehensive team information** at their fingertips
- **Customizable notifications** that don't spam unwilling channels
- **Smart, hockey-aware features** that understand the game

**Ready for Game 5!** 🐾🚨
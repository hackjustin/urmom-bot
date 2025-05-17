Urmom Discord Bot

A simple Discord bot that responds to specific phrases with GIFs and reactions, provides movie information, and offers a reminder system.
Features

    Responds to "ur mom" or "your mom" mentions with a GIF
    Reacts to messages containing "alot" with emoji letters spelling "ALOT"
    Responds to !mom command with text
    Movie lookup via IMDB/OMDB API with the !movie command
    Reminder system that lets users set reminders with the !remind command

Setup
Prerequisites

    Docker and Docker Compose installed
    A Discord bot token (from Discord Developer Portal)
    OMDB API key (from OMDB API) for movie lookups

Configuration

    Edit the .env file with your credentials:

    DISCORD_TOKEN=your_discord_token_here
    OMDB_API_KEY=your_omdb_api_key_here

    Configure bot behavior in the BotConfig class in refactored_urmom_bot.py

Building and Running with Docker

bash

# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down

Project Structure

.
├── gifs/                  # Directory for GIF files
│   ├── alot.gif
│   └── ur-mom.gif
├── refactored_urmom_bot.py # Main bot code
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker build instructions
└── docker-compose.yml     # Docker Compose configuration

Commands
!mom

A simple command that responds with "what...?"
!movie [title]

Searches for movies matching the given title. If multiple matches are found, displays a list with details including actors, director, and studio for selection.

Example:

!movie The Matrix

!remind [time] [message]

Sets a reminder for the specified time.

Time formats:

    Relative time: 5 minutes, 2 hours, 1 day, etc.
    Absolute time: at 5pm, tomorrow at 9am, etc.

If replying to another message, the reminder will include that message.

Examples:

!remind 15 minutes Check the oven
!remind at 5pm Call mom
!remind tomorrow at 9am Team meeting

Adding New Features

To add new features:

    For new commands, add them with the @bot.command() decorator
    For configuration options, add them to the BotConfig class

Example: To implement a new reaction to a specific phrase:

python

if "some phrase" in message.content.lower():
    await message.channel.send("Your response here")
```. For new commands, add them with the `@bot.command()` decorator
3. For configuration options, add them to the `BotConfig` class
. For new commands, add them with the `@bot.command()` decorator
3. For configuration options, add them to the `BotConfig` class

Example: To implement a new reaction to a specific phrase:

```python
if "some phrase" in message.content.lower():
    await message.channel.send("Your response here")


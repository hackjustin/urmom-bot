# Urmom Discord Bot

A simple Discord bot that responds to specific phrases with GIFs and reactions.

## Features

- Responds to "ur mom" or "your mom" mentions with a GIF
- Reacts to messages containing "alot" with emoji letters spelling "ALOT"
- Responds to `!mom` command with text
- Word usage tracking feature (example implementation)

## Setup

### Prerequisites

- Docker and Docker Compose installed
- A Discord bot token (from [Discord Developer Portal](https://discord.com/developers/applications))

### Configuration

1. Copy your Discord bot token to the `.env` file:
   ```
   DISCORD_TOKEN=your_token_here
   ```

2. Configure bot behavior in the `BotConfig` class in `refactored_urmom_bot.py`

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
├── urmom-bot.py           # Main bot code
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker build instructions
└── docker-compose.yml     # Docker Compose configuration
```

## Adding New Features

To add new features:

1. For new response triggers, add handling in the `on_message` event
2. For new commands, add them with the `@bot.command()` decorator
3. For configuration options, add them to the `BotConfig` class

Example: To implement a new reaction to a specific phrase:

```python
if "some phrase" in message.content.lower():
    await message.channel.send("Your response here")
```

FROM python:3.11-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt .

# Modified pip install command to handle discord.py without voice support
RUN pip install --no-cache-dir --upgrade pip && \
    # First install everything except discord.py
    grep -v "discord.py" requirements.txt | pip install --no-cache-dir -r /dev/stdin && \
    # Then install discord.py without dependencies
    pip install --no-cache-dir --no-deps discord.py && \
    # Install essential discord.py dependencies (excluding voice)
    pip install --no-cache-dir aiohttp typing-extensions

# Copy application code
COPY . .

# Run the bot
CMD ["python", "urmom-bot.py"]

FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire bot structure
COPY . .

# Create the bot module directory if it doesn't exist
RUN mkdir -p bot

# Make sure the gifs directory exists
RUN mkdir -p gifs

# Set Python path to include the current directory
ENV PYTHONPATH=/app

CMD ["python", "main.py"]
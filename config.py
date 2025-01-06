import os

# Discord Bot Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = '!'

# Database Configuration
DB_CONFIG = {
    'user': os.getenv('PGUSER'),
    'password': os.getenv('PGPASSWORD'),
    'host': os.getenv('PGHOST'),
    'port': os.getenv('PGPORT'),
    'database': os.getenv('PGDATABASE')
}

# Tweet Colors
COLORS = {
    'text': 0x6B46C1,
    'media': 0x9F7AEA,
    'retweet': 0x4A5568,
    'error': 0xE53E3E,
    'success': 0x48BB78
}

# Refresh interval for checking new tweets (in seconds)
TWEET_CHECK_INTERVAL = 15  # Reduced to 15 seconds for faster updates
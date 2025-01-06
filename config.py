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

# Increased timeouts and more reliable instances
TWEET_CHECK_INTERVAL = 5  # Check every 5 seconds
MAX_CONCURRENT_REQUESTS = 2  # Reduced concurrent requests
REQUEST_TIMEOUT = 10  # Increased timeout to 10 seconds
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.1d4.us",
    "https://nitter.kavin.rocks",
    "https://nitter.unixfox.eu",
    "https://nitter.projectsegfau.lt"
]
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

# Faster refresh interval and timeouts
TWEET_CHECK_INTERVAL = 5  # Check every 5 seconds
MAX_CONCURRENT_REQUESTS = 3  # Maximum number of concurrent tweet checks
REQUEST_TIMEOUT = 2  # 2 second timeout for requests
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.1d4.us",
    "https://nitter.kavin.rocks"
]
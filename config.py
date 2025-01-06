import os

# Discord Bot Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = '!'

# Twitter API Configuration
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')

# Database Configuration
DB_CONFIG = {
    'user': os.getenv('PGUSER'),
    'password': os.getenv('PGPASSWORD'),
    'host': os.getenv('PGHOST'),
    'port': os.getenv('PGPORT'),
    'database': os.getenv('PGDATABASE')
}

# Tweet Colors (Inspired by Hive Builders theme)
COLORS = {
    'text': 0x6B46C1,     # Rich purple for text tweets
    'media': 0x9F7AEA,    # Light purple for media tweets
    'retweet': 0x4A5568,  # Slate gray for retweets
    'error': 0xE53E3E,    # Red for errors
    'success': 0x48BB78   # Green for success messages
}

# Refresh interval for checking new tweets (in seconds)
TWEET_CHECK_INTERVAL = 60
import tweepy
from config import TWITTER_BEARER_TOKEN, TWITTER_API_KEY, TWITTER_API_SECRET

class TwitterClient:
    def __init__(self):
        self.client = tweepy.Client(
            bearer_token=TWITTER_BEARER_TOKEN,
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            wait_on_rate_limit=True
        )

    async def get_user_by_username(self, username):
        try:
            user = self.client.get_user(username=username)
            return user.data if user else None
        except tweepy.TweepyException:
            return None

    async def get_recent_tweets(self, user_id):
        try:
            tweets = self.client.get_users_tweets(
                user_id,
                tweet_fields=['created_at', 'entities', 'public_metrics'],
                expansions=['attachments.media_keys'],
                media_fields=['url', 'preview_image_url'],
                max_results=5
            )
            return tweets.data if tweets else []
        except tweepy.TweepyException:
            return []

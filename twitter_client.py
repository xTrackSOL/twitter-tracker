import feedparser
import re
from datetime import datetime
from urllib.parse import quote

class TwitterClient:
    def __init__(self):
        # Using a reliable Nitter instance
        self.base_url = "https://nitter.net"

    async def get_user_by_username(self, username):
        """Verify if a Twitter user exists by checking their RSS feed"""
        try:
            feed = feedparser.parse(f"{self.base_url}/{username}/rss")
            if feed.entries:
                return {
                    'username': username,
                    'name': feed.feed.title.replace("'s tweets", ""),
                    'id': username,
                    'profile_image_url': self._get_profile_image(feed)
                }
            return None
        except Exception:
            return None

    async def get_recent_tweets(self, user_id):
        """Get recent tweets from user's RSS feed"""
        try:
            feed = feedparser.parse(f"{self.base_url}/{user_id}/rss")
            tweets = []

            for entry in feed.entries[:5]:  # Get last 5 tweets
                tweet = {
                    'id': self._extract_tweet_id(entry.link),
                    'text': self._clean_text(entry.description),
                    'created_at': datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z"),
                    'public_metrics': {
                        'reply_count': 0,  # These metrics aren't available in RSS
                        'retweet_count': 0,
                        'like_count': 0
                    }
                }

                # Check if it's a retweet
                if entry.title.startswith('RT by'):
                    tweet['referenced_tweets'] = [{'type': 'retweeted'}]

                # Extract media if present
                media = self._extract_media(entry.description)
                if media:
                    tweet['attachments'] = {'media': media}

                tweets.append(tweet)

            return tweets
        except Exception:
            return []

    def _extract_tweet_id(self, url):
        """Extract tweet ID from Nitter URL"""
        match = re.search(r'/status/(\d+)', url)
        return match.group(1) if match else None

    def _clean_text(self, html):
        """Clean tweet text from HTML content"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _extract_media(self, html):
        """Extract media URLs from tweet HTML"""
        media = []
        img_matches = re.finditer(r'<img[^>]+src="([^"]+)"', html)
        for match in img_matches:
            if 'tweet_video_thumb' not in match.group(1):  # Exclude video thumbnails
                media.append({
                    'url': match.group(1),
                    'type': 'photo'
                })
        return media

    def _get_profile_image(self, feed):
        """Extract profile image URL from feed data"""
        try:
            # Try to find image in feed metadata
            if 'image' in feed.feed:
                return feed.feed.image.href
            return None
        except AttributeError:
            return None
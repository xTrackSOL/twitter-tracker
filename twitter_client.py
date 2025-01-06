import feedparser
import re
from datetime import datetime
from urllib.parse import quote
import asyncio

class TwitterClient:
    def __init__(self):
        # Using a more reliable Nitter instance
        self.base_urls = [
            "https://nitter.cz",
            "https://nitter.lacontrevoie.fr",
            "https://nitter.fdn.fr"
        ]
        self.current_instance = 0

    async def _try_fetch_feed(self, username):
        """Try fetching feed from different Nitter instances"""
        for _ in range(len(self.base_urls)):
            try:
                url = f"{self.base_urls[self.current_instance]}/{username}/rss"
                feed = feedparser.parse(url)
                if feed.entries and not feed.get('bozo', 1):
                    return feed
            except Exception:
                pass
            # Try next instance
            self.current_instance = (self.current_instance + 1) % len(self.base_urls)
            await asyncio.sleep(1)  # Add delay between retries
        return None

    async def get_user_by_username(self, username):
        """Verify if a Twitter user exists by checking their RSS feed"""
        try:
            feed = await self._try_fetch_feed(username)
            if feed and feed.entries:
                # Extract username and name from feed title
                name = feed.feed.title.split("'")[0].strip()  # Get name before "'s tweets"
                return {
                    'username': username,
                    'name': name,
                    'id': username,
                    'profile_image_url': self._get_profile_image(feed)
                }
            return None
        except Exception as e:
            print(f"Error fetching user {username}: {str(e)}")
            return None

    async def get_recent_tweets(self, user_id):
        """Get recent tweets from user's RSS feed"""
        try:
            feed = await self._try_fetch_feed(user_id)
            if not feed:
                return []

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
        except Exception as e:
            print(f"Error fetching tweets for {user_id}: {str(e)}")
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
        # Decode HTML entities
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
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
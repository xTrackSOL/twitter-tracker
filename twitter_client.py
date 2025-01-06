import feedparser
import re
from datetime import datetime
from urllib.parse import quote
import asyncio
import aiohttp
from typing import Optional, Dict, List

class TwitterClient:
    def __init__(self):
        # Using reliable Nitter instances
        self.base_urls = [
            "https://nitter.net",
            "https://nitter.1d4.us",
            "https://nitter.kavin.rocks",
            "https://nitter.unixfox.eu",
            "https://nitter.poast.org",
            "https://nitter.privacydev.net"
        ]
        self.current_instance = 0
        self.timeout = aiohttp.ClientTimeout(total=10)  # 10 seconds timeout

    async def _try_fetch_feed(self, username: str) -> Optional[feedparser.FeedParserDict]:
        """Try fetching feed from different Nitter instances with timeout"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for _ in range(len(self.base_urls)):
                try:
                    url = f"{self.base_urls[self.current_instance]}/{username}/rss"
                    print(f"Trying {url}...")
                    async with session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            feed = feedparser.parse(content)
                            if feed.entries and not feed.get('bozo', 1):
                                return feed
                except Exception as e:
                    print(f"Error with {self.base_urls[self.current_instance]}: {str(e)}")

                # Try next instance
                self.current_instance = (self.current_instance + 1) % len(self.base_urls)
                await asyncio.sleep(1)  # Add delay between retries
        return None

    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Verify if a Twitter user exists by checking their RSS feed"""
        try:
            print(f"\nLooking up user @{username}")
            feed = await self._try_fetch_feed(username)
            if feed and feed.entries:
                # Extract username and name from feed title
                name = feed.feed.title.split("'")[0].strip()
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

    async def get_recent_tweets(self, user_id: str) -> List[Dict]:
        """Get recent tweets from user's RSS feed"""
        try:
            print(f"\nFetching tweets for @{user_id}")
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
                        'reply_count': self._extract_metrics(entry.description).get('replies', 0),
                        'retweet_count': self._extract_metrics(entry.description).get('retweets', 0),
                        'like_count': self._extract_metrics(entry.description).get('likes', 0)
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

    def _extract_tweet_id(self, url: str) -> Optional[str]:
        """Extract tweet ID from Nitter URL"""
        match = re.search(r'/status/(\d+)', url)
        return match.group(1) if match else None

    def _clean_text(self, html: str) -> str:
        """Clean tweet text from HTML content"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Decode HTML entities
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        return text.strip()

    def _extract_media(self, html: str) -> List[Dict]:
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

    def _get_profile_image(self, feed: feedparser.FeedParserDict) -> Optional[str]:
        """Extract profile image URL from feed data"""
        try:
            if 'image' in feed.feed:
                return feed.feed.image.href
            return None
        except AttributeError:
            return None

    def _extract_metrics(self, html: str) -> Dict[str, int]:
        """Extract engagement metrics from tweet HTML"""
        metrics = {'replies': 0, 'retweets': 0, 'likes': 0}
        try:
            # Look for metrics in the HTML
            metrics_match = re.search(r'(\d+) replies?, (\d+) retweets?, (\d+) likes?', html)
            if metrics_match:
                metrics['replies'] = int(metrics_match.group(1))
                metrics['retweets'] = int(metrics_match.group(2))
                metrics['likes'] = int(metrics_match.group(3))
        except Exception:
            pass
        return metrics
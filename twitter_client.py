import feedparser
import re
from datetime import datetime
from urllib.parse import quote
import asyncio
import aiohttp
from typing import Optional, Dict, List
import email.utils

class TwitterClient:
    def __init__(self):
        # Updated list of reliable Nitter instances
        self.base_urls = [
            "https://nitter.privacydev.net",
            "https://nitter.poast.org",
            "https://nitter.bird.froth.zone",
            "https://nitter.moomoo.me",
            "https://nitter.woodland.cafe",
            "https://nitter.nicfab.eu"
        ]
        self.current_instance = 0
        self.timeout = aiohttp.ClientTimeout(total=5)

    def _is_valid_username(self, username: str) -> bool:
        """Validate Twitter username format"""
        # Twitter username rules: 4-15 characters, alphanumeric and underscores only
        return bool(re.match(r'^[A-Za-z0-9_]{4,15}$', username))

    async def _try_fetch_feed(self, username: str) -> Optional[feedparser.FeedParserDict]:
        """Try fetching feed from different Nitter instances with timeout"""
        if not self._is_valid_username(username):
            print(f"Invalid username format: {username}")
            return None

        errors = []
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for _ in range(len(self.base_urls)):
                try:
                    url = f"{self.base_urls[self.current_instance]}/{username}/rss"
                    print(f"Trying {url}...")
                    async with session.get(url, ssl=False) as response:
                        if response.status == 200:
                            content = await response.text()
                            feed = feedparser.parse(content)
                            if feed.entries and not feed.get('bozo', 1):
                                return feed
                        elif response.status == 404:
                            print(f"User {username} not found")
                            return None
                except Exception as e:
                    errors.append(f"Error with {self.base_urls[self.current_instance]}: {str(e)}")

                self.current_instance = (self.current_instance + 1) % len(self.base_urls)
                await asyncio.sleep(0.5)

        for error in errors:
            print(error)
        return None

    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Verify if a Twitter user exists by checking their RSS feed"""
        try:
            print(f"\nLooking up user @{username}")
            if not self._is_valid_username(username):
                print(f"Invalid Twitter username format: {username}")
                return None

            feed = await self._try_fetch_feed(username)
            if feed and feed.entries:
                name = feed.feed.title
                if "'" in name:  # Format: "Username's tweets"
                    name = name.split("'")[0].strip()
                elif "/" in name:  # Format: "Username / @handle"
                    name = name.split("/")[0].strip()

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
                try:
                    # Parse the date with multiple fallbacks
                    try:
                        parsed_date = email.utils.parsedate_to_datetime(entry.published)
                    except Exception:
                        try:
                            parsed_date = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
                        except Exception:
                            parsed_date = datetime.now()

                    tweet = {
                        'id': self._extract_tweet_id(entry.link),
                        'text': self._clean_text(entry.description),
                        'created_at': parsed_date,
                        'public_metrics': self._extract_metrics(entry.description)
                    }

                    # Check if it's a retweet
                    if entry.title.startswith('RT by'):
                        tweet['referenced_tweets'] = [{'type': 'retweeted'}]

                    # Extract media if present
                    media = self._extract_media(entry.description)
                    if media:
                        tweet['attachments'] = {'media': media}

                    tweets.append(tweet)
                except Exception as e:
                    print(f"Error parsing tweet: {str(e)}")
                    continue

            return tweets
        except Exception as e:
            print(f"Error fetching tweets for {user_id}: {str(e)}")
            return []

    def _extract_tweet_id(self, url: str) -> str:
        """Extract tweet ID from Nitter URL"""
        match = re.search(r'/status/(\d+)', url)
        return match.group(1) if match else "0"

    def _clean_text(self, html: str) -> str:
        """Clean tweet text from HTML content"""
        text = re.sub(r'<[^>]+>', '', html)
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        return text.strip()

    def _extract_media(self, html: str) -> List[Dict]:
        """Extract media URLs from tweet HTML"""
        media = []
        img_matches = re.finditer(r'<img[^>]+src="([^"]+)"', html)
        for match in img_matches:
            if 'tweet_video_thumb' not in match.group(1):
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
            metrics_match = re.search(r'(\d+) replies?, (\d+) retweets?, (\d+) likes?', html)
            if metrics_match:
                metrics['reply_count'] = int(metrics_match.group(1))
                metrics['retweet_count'] = int(metrics_match.group(2))
                metrics['like_count'] = int(metrics_match.group(3))
        except Exception:
            pass
        return metrics
import feedparser
import re
from datetime import datetime
from urllib.parse import quote
import asyncio
import aiohttp
from typing import Optional, Dict, List
import email.utils
import logging

logger = logging.getLogger('twitter_client')

class TwitterClient:
    def __init__(self):
        # Use only the single most reliable Nitter instance
        self.base_url = "https://nitter.privacydev.net"
        self.timeout = aiohttp.ClientTimeout(total=3)  # Even shorter timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; DiscordBot/2.0; +https://discord.com)',
            'Accept': 'application/rss+xml'
        }

    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user information from their feed"""
        feed = await self._try_fetch_feed(username)
        if not feed or not feed.feed:
            return None

        try:
            name = feed.feed.title.split("'")[0].strip()
            return {
                'username': username.strip('@'),
                'name': name,
                'id': username.strip('@'),
                'profile_image_url': feed.feed.image.href if hasattr(feed.feed, 'image') else None
            }
        except:
            return None

    async def get_recent_tweets(self, username: str) -> List[Dict]:
        """Get recent tweets from user's feed"""
        feed = await self._try_fetch_feed(username)
        if not feed or not feed.entries:
            return []

        tweets = []
        # Only process the most recent tweet to be super fast
        try:
            entry = feed.entries[0]
            tweet = {
                'id': self._extract_tweet_id(entry.link),
                'text': self._clean_text(entry.description),
                'created_at': email.utils.parsedate_to_datetime(entry.published),
                'public_metrics': self._extract_metrics(entry.description),
            }

            # Add media if present
            media = self._extract_media(entry.description)
            if media:
                tweet['attachments'] = {'media': media}

            tweets.append(tweet)
        except Exception as e:
            logger.error(f"Error parsing tweet: {str(e)}")

        return tweets

    async def _try_fetch_feed(self, username: str) -> Optional[feedparser.FeedParserDict]:
        """Try fetching feed from Nitter instance"""
        try:
            username = username.strip('@').strip()
            url = f"{self.base_url}/{quote(username)}/rss"

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, ssl=False, headers=self.headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        if not content or 'Error' in content:
                            return None
                        feed = feedparser.parse(content)
                        if feed and feed.entries:
                            return feed
            return None
        except Exception as e:
            logger.error(f"Error fetching feed for @{username}: {str(e)}")
            return None

    def _extract_tweet_id(self, url: str) -> str:
        """Extract tweet ID from URL"""
        match = re.search(r'/status/(\d+)', url)
        return match.group(1) if match else "0"

    def _clean_text(self, html: str) -> str:
        """Clean tweet text from HTML"""
        text = re.sub(r'<[^>]+>', '', html)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _extract_media(self, html: str) -> List[Dict]:
        """Extract media URLs from tweet HTML"""
        media = []
        img_matches = re.finditer(r'<img[^>]+src="([^"]+)"', html)
        for match in img_matches:
            url = match.group(1)
            if 'tweet_video_thumb' not in url and 'emoji' not in url:
                media.append({'url': url, 'type': 'photo'})
        return media

    def _extract_metrics(self, html: str) -> Dict[str, int]:
        """Extract engagement metrics from tweet HTML"""
        metrics = {'reply_count': 0, 'retweet_count': 0, 'like_count': 0}
        try:
            metrics_match = re.search(r'(\d+) replies?, (\d+) retweets?, (\d+) likes?', html)
            if metrics_match:
                metrics['reply_count'] = int(metrics_match.group(1))
                metrics['retweet_count'] = int(metrics_match.group(2))
                metrics['like_count'] = int(metrics_match.group(3))
        except:
            pass
        return metrics
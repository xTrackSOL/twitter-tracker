import feedparser
import re
from datetime import datetime
from urllib.parse import quote
import asyncio
import aiohttp
from typing import Optional, Dict, List
import email.utils
import logging
import random
from config import NITTER_INSTANCES, REQUEST_TIMEOUT, MAX_CONCURRENT_REQUESTS

logger = logging.getLogger('twitter_client')

class TwitterClient:
    def __init__(self):
        self.instances = NITTER_INSTANCES
        self.timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT, connect=1)
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; DiscordBot/2.0; +https://discord.com)',
            'Accept': 'application/rss+xml'
        }
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with connection pooling"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                connector=aiohttp.TCPConnector(limit=10, force_close=True)
            )
        return self.session

    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user information from their feed"""
        async with self.semaphore:  # Limit concurrent requests
            try:
                feed = await self._try_fetch_feed(username)
                if not feed or not feed.feed:
                    return None

                name = feed.feed.title.split("'")[0].strip()
                return {
                    'username': username.strip('@'),
                    'name': name,
                    'id': username.strip('@'),
                    'profile_image_url': feed.feed.image.href if hasattr(feed.feed, 'image') else None
                }
            except Exception as e:
                logger.error(f"Error getting user {username}: {str(e)}")
                return None

    async def get_recent_tweets(self, username: str) -> List[Dict]:
        """Get most recent tweet only with fallback instances"""
        async with self.semaphore:  # Limit concurrent requests
            try:
                feed = await self._try_fetch_feed(username)
                if not feed or not feed.entries:
                    return []

                tweets = []
                # Only process the most recent tweet
                try:
                    entry = feed.entries[0]
                    tweet = {
                        'id': self._extract_tweet_id(entry.link),
                        'text': self._clean_text(entry.description),
                        'created_at': email.utils.parsedate_to_datetime(entry.published),
                        'public_metrics': self._extract_metrics(entry.description),
                    }

                    media = self._extract_media(entry.description)
                    if media:
                        tweet['attachments'] = {'media': media}

                    tweets.append(tweet)
                except Exception as e:
                    logger.error(f"Error parsing tweet: {str(e)}")

                return tweets
            except Exception as e:
                logger.error(f"Error getting tweets for {username}: {str(e)}")
                return []

    async def _try_fetch_feed(self, username: str) -> Optional[feedparser.FeedParserDict]:
        """Try fetching feed from multiple Nitter instances with fallback"""
        username = username.strip('@').strip()

        # Try each instance in random order until one works
        instances = random.sample(self.instances, len(self.instances))

        for base_url in instances:
            try:
                url = f"{base_url}/{quote(username)}/rss"
                session = await self._get_session()

                async with session.get(url, ssl=False, headers=self.headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        if not content or 'Error' in content:
                            continue
                        feed = feedparser.parse(content)
                        if feed and feed.entries:
                            return feed
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on {base_url} for @{username}")
                continue
            except Exception as e:
                logger.warning(f"Error on {base_url} for @{username}: {str(e)}")
                continue

        logger.error(f"All instances failed for @{username}")
        return None

    def _extract_tweet_id(self, url: str) -> str:
        """Extract tweet ID from URL"""
        try:
            match = re.search(r'/status/(\d+)', url)
            return match.group(1) if match else "0"
        except:
            return "0"

    def _clean_text(self, html: str) -> str:
        """Clean tweet text from HTML"""
        try:
            text = re.sub(r'<[^>]+>', '', html)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        except:
            return ""

    def _extract_media(self, html: str) -> List[Dict]:
        """Extract media URLs from tweet HTML"""
        try:
            media = []
            img_matches = re.finditer(r'<img[^>]+src="([^"]+)"', html)
            for match in img_matches:
                url = match.group(1)
                if 'tweet_video_thumb' not in url and 'emoji' not in url:
                    media.append({'url': url, 'type': 'photo'})
            return media
        except:
            return []

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

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
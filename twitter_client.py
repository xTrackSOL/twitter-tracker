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
            "https://nitter.net",
            "https://nitter.privacydev.net",
            "https://nitter.esmailelbob.xyz",
            "https://nitter.d420.de",
            "https://nitter.foss.wtf",
            "https://nitter.privacy.com.de",
            "https://nitter.poast.org",
            "https://nitter.cz",
            "https://nitter.unixfox.eu",
            "https://nitter.salastil.com"
        ]
        self.timeout = aiohttp.ClientTimeout(total=30)  # Increased timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; DiscordBot/2.0; +https://discord.com)',
            'Accept': 'application/rss+xml, application/xml, text/xml, application/atom+xml',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

    async def _try_fetch_feed(self, username: str) -> Optional[feedparser.FeedParserDict]:
        """Try fetching feed from different Nitter instances with improved error handling"""
        username = username.strip('@').strip()
        print(f"\nTrying to fetch feed for @{username}")

        errors = []
        for instance_url in self.base_urls:
            for attempt in range(2):  # Try each instance twice
                try:
                    encoded_username = quote(username)
                    url = f"{instance_url}/{encoded_username}/rss"
                    print(f"Trying {url}... (attempt {attempt + 1})")

                    async with aiohttp.ClientSession(timeout=self.timeout) as session:
                        try:
                            async with session.get(url, ssl=False, headers=self.headers) as response:
                                if response.status == 200:
                                    content = await response.text()

                                    # Check for various error indicators
                                    error_indicators = [
                                        'Error loading profile',
                                        'User not found',
                                        'This account has been suspended',
                                        'This account doesn\'t exist',
                                    ]

                                    if not content or any(indicator in content for indicator in error_indicators):
                                        print(f"Error content from {instance_url}")
                                        break  # Try next instance

                                    feed = feedparser.parse(content)
                                    if feed and not feed.get('bozo', 0) and feed.entries:
                                        print(f"Successfully fetched feed from {instance_url}")
                                        return feed

                                elif response.status == 429:  # Rate limit
                                    print(f"Rate limited by {instance_url}")
                                    await asyncio.sleep(2 * (attempt + 1))  # Exponential backoff
                                    continue
                                else:
                                    print(f"Got status {response.status} from {instance_url}")
                                    break  # Try next instance

                        except asyncio.TimeoutError:
                            print(f"Timeout with {instance_url}")
                            continue
                        except Exception as e:
                            print(f"Connection error with {instance_url}: {str(e)}")
                            continue

                except Exception as e:
                    errors.append(f"Error with {instance_url}: {str(e)}")
                    continue

                await asyncio.sleep(1)  # Rate limiting delay between attempts

            await asyncio.sleep(0.5)  # Small delay between instances

        if errors:
            print("All Nitter instances failed:")
            for error in errors:
                print(error)
        return None

    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user information from their RSS feed"""
        try:
            feed = await self._try_fetch_feed(username)
            if feed and feed.feed:
                # Extract user information from feed
                name = feed.feed.title
                if "'" in name:  # Format: "Username's tweets"
                    name = name.split("'")[0].strip()
                elif "/" in name:  # Format: "Username / @handle"
                    name = name.split("/")[0].strip()

                return {
                    'username': username.strip('@'),
                    'name': name,
                    'id': username.strip('@'),
                    'profile_image_url': self._get_profile_image(feed)
                }
            return None

        except Exception as e:
            print(f"Error fetching user {username}: {str(e)}")
            return None

    async def get_recent_tweets(self, username: str) -> List[Dict]:
        """Get recent tweets from user's RSS feed"""
        try:
            print(f"\nFetching tweets for @{username}")
            feed = await self._try_fetch_feed(username)
            if not feed or not feed.entries:
                return []

            tweets = []
            for entry in feed.entries[:5]:  # Get last 5 tweets
                try:
                    # Parse the date
                    try:
                        parsed_date = email.utils.parsedate_to_datetime(entry.published)
                    except Exception:
                        try:
                            parsed_date = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
                        except Exception:
                            parsed_date = datetime.now()

                    # Create tweet object
                    tweet = {
                        'id': self._extract_tweet_id(entry.link),
                        'text': self._clean_text(entry.description),
                        'created_at': parsed_date,
                        'public_metrics': self._extract_metrics(entry.description),
                        'referenced_tweets': [{'type': 'retweeted'}] if 'RT by' in entry.title else []
                    }

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
            print(f"Error fetching tweets for {username}: {str(e)}")
            return []

    def _extract_tweet_id(self, url: str) -> str:
        """Extract tweet ID from URL"""
        match = re.search(r'/status/(\d+)', url)
        return match.group(1) if match else "0"

    def _clean_text(self, html: str) -> str:
        """Clean tweet text from HTML content"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Fix whitespace
        text = re.sub(r'\s+', ' ', text)
        # Decode HTML entities
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
            if hasattr(feed.feed, 'image') and feed.feed.image:
                return feed.feed.image.href
            return None
        except AttributeError:
            return None

    def _extract_metrics(self, html: str) -> Dict[str, int]:
        """Extract engagement metrics from tweet HTML"""
        metrics = {'reply_count': 0, 'retweet_count': 0, 'like_count': 0}
        try:
            metrics_match = re.search(r'(\d+) replies?, (\d+) retweets?, (\d+) likes?', html)
            if metrics_match:
                metrics['reply_count'] = int(metrics_match.group(1))
                metrics['retweet_count'] = int(metrics_match.group(2))
                metrics['like_count'] = int(metrics_match.group(3))
        except Exception:
            pass
        return metrics
import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
from database import Database
from twitter_client import TwitterClient
from utils import create_tweet_embed, format_error_message
from config import TWEET_CHECK_INTERVAL
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('twitter_commands')

class TwitterCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.twitter = TwitterClient()
        self.checking_tweets = False
        self.command_lock = asyncio.Lock()
        logger.info("TwitterCommands cog initialized")
        self.check_tweets.start()

    def cog_unload(self):
        self.check_tweets.cancel()
        asyncio.create_task(self.cleanup())

    async def cleanup(self):
        """Cleanup resources"""
        await self.twitter.close()
        self.db.close()

    def _extract_username(self, input_text: str) -> str:
        """Extract username from either a URL or direct input"""
        # Remove any whitespace and @ symbol
        input_text = input_text.strip().lstrip('@')

        # Check if it's a URL
        url_patterns = [
            r'(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)/?$',
            r'(?:https?://)?(?:www\.)?t\.co/([a-zA-Z0-9_]+)/?$'
        ]

        for pattern in url_patterns:
            match = re.match(pattern, input_text)
            if match:
                return match.group(1)

        # If no URL pattern matches, return the cleaned input
        return input_text

    @app_commands.command(
        name="track",
        description="Track a Twitter account by username or profile URL"
    )
    @app_commands.describe(
        twitter_input="Twitter username (e.g. @username) or profile URL (e.g. https://x.com/username)"
    )
    async def track(self, interaction: discord.Interaction, twitter_input: str):
        async with self.command_lock:
            try:
                username = self._extract_username(twitter_input)
                if not username:
                    await interaction.response.send_message(
                        "Please provide a valid Twitter username or profile URL",
                        ephemeral=True
                    )
                    return

                await interaction.response.send_message(
                    f"Setting up tracking for @{username}...",
                    ephemeral=True
                )

                # Quick check if user exists before adding to database
                user = await self.twitter.get_user_by_username(username)
                if not user:
                    await interaction.edit_original_response(
                        content=f"❌ Could not find Twitter user @{username}. Please check the username/URL and try again."
                    )
                    return

                # Add to database
                result = self.db.add_twitter_account(username, interaction.channel_id)

                if result:
                    # Fetch initial tweet immediately
                    tweets = await self.twitter.get_recent_tweets(username)
                    if tweets:
                        self.db.update_last_tweet_id(
                            username,
                            interaction.channel_id,
                            str(tweets[0]['id'])
                        )

                    await interaction.edit_original_response(
                        content=f"✅ Started tracking @{username} in this channel!"
                    )
                else:
                    await interaction.edit_original_response(
                        content=f"ℹ️ @{username} is already being tracked in this channel!"
                    )

            except asyncio.TimeoutError:
                await interaction.edit_original_response(
                    content="❌ Request timed out. Please try again."
                )
            except Exception as e:
                logger.error(f"Error in track command: {str(e)}", exc_info=True)
                await interaction.edit_original_response(
                    content="An error occurred. Please try again in a few moments."
                )

    @app_commands.command(name="untrack", description="Stop tracking a Twitter account in this channel")
    async def untrack(self, interaction: discord.Interaction, username: str):
        async with self.command_lock:
            try:
                username = username.lstrip('@')
                logger.info(f"Untrack command received for @{username}")
                await interaction.response.send_message(f"Removing tracking for @{username}...", ephemeral=True)

                if self.db.remove_twitter_account(username, interaction.channel_id):
                    logger.info(f"Successfully stopped tracking @{username}")
                    await interaction.edit_original_response(
                        content=f"✅ Stopped tracking @{username} in this channel"
                    )
                else:
                    logger.info(f"@{username} was not being tracked")
                    await interaction.edit_original_response(
                        content=f"❌ @{username} was not being tracked in this channel"
                    )
            except Exception as e:
                logger.error(f"Error in untrack command: {str(e)}", exc_info=True)
                await interaction.edit_original_response(
                    content="An error occurred. Please try again."
                )

    @app_commands.command(name="list", description="List all tracked Twitter accounts in this channel")
    async def list_tracked(self, interaction: discord.Interaction):
        async with self.command_lock:
            try:
                logger.info(f"List command received for channel {interaction.channel_id}")
                await interaction.response.send_message("Fetching tracked accounts...", ephemeral=True)
                accounts = self.db.get_channel_accounts(interaction.channel_id)

                if not accounts:
                    logger.info("No accounts being tracked")
                    await interaction.edit_original_response(
                        content="No accounts are being tracked in this channel"
                    )
                    return

                account_list = "\n".join([f"• @{account}" for account in accounts])
                logger.info(f"Found tracked accounts: {accounts}")
                await interaction.edit_original_response(
                    content=f"📋 Tracked Accounts:\n{account_list}"
                )
            except Exception as e:
                logger.error(f"Error in list command: {str(e)}", exc_info=True)
                await interaction.edit_original_response(
                    content="An error occurred. Please try again."
                )

    @tasks.loop(seconds=TWEET_CHECK_INTERVAL)
    async def check_tweets(self):
        """Check for new tweets from tracked accounts"""
        if self.checking_tweets:
            return

        try:
            self.checking_tweets = True
            accounts = self.db.get_tracked_accounts()
            logger.info(f"Checking tweets for {len(accounts)} tracked accounts")

            for account in accounts:
                try:
                    # Get recent tweets (optimized to fetch only the latest)
                    tweets = await self.twitter.get_recent_tweets(account['twitter_handle'])
                    if not tweets:
                        continue

                    channel = self.bot.get_channel(account['channel_id'])
                    if not channel:
                        continue

                    last_tweet_id = account['last_tweet_id']
                    if not last_tweet_id:
                        # First time tracking, just store the latest tweet ID
                        latest_id = str(tweets[0]['id'])
                        self.db.update_last_tweet_id(
                            account['twitter_handle'],
                            account['channel_id'],
                            latest_id
                        )
                        continue

                    # Compare with latest tweet
                    tweet = tweets[0]
                    if int(tweet['id']) > int(last_tweet_id):
                        try:
                            user = await self.twitter.get_user_by_username(account['twitter_handle'])
                            if user:
                                embed = create_tweet_embed(tweet, user)
                                await channel.send(embed=embed)
                                self.db.update_last_tweet_id(
                                    account['twitter_handle'],
                                    account['channel_id'],
                                    str(tweet['id'])
                                )
                        except Exception as e:
                            logger.error(f"Error sending tweet: {str(e)}", exc_info=True)

                except Exception as e:
                    logger.error(f"Error checking {account['twitter_handle']}: {str(e)}", exc_info=True)
                    continue

                # Very small delay between accounts to prevent flooding
                await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Error in check_tweets: {str(e)}", exc_info=True)
        finally:
            self.checking_tweets = False

    @check_tweets.before_loop
    async def before_check_tweets(self):
        await self.bot.wait_until_ready()
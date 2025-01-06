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

    def _extract_username(self, input_text: str) -> str:
        """Extract username from either a URL or direct input"""
        # Remove any whitespace and @ symbol
        input_text = input_text.strip().lstrip('@')

        # URL patterns for both x.com and twitter.com
        url_patterns = [
            r'(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)(?:/.*)?$',
            r'(?:https?://)?(?:www\.)?t\.co/([a-zA-Z0-9_]+)(?:/.*)?$'
        ]

        for pattern in url_patterns:
            match = re.match(pattern, input_text)
            if match:
                username = match.group(1)
                logger.info(f"Extracted username '{username}' from URL: {input_text}")
                return username

        # If no URL pattern matches, return the cleaned input
        return input_text

    @app_commands.command()
    @app_commands.describe(twitter_input="Twitter handle (@username) or profile URL")
    async def track(self, interaction: discord.Interaction, twitter_input: str):
        """Track tweets from a Twitter/X account in this channel"""
        async with self.command_lock:
            try:
                await interaction.response.defer(ephemeral=True)

                username = self._extract_username(twitter_input)
                if not username:
                    await interaction.followup.send("❌ Please provide a valid Twitter username or profile URL.")
                    return

                # Verify user exists
                user = await self.twitter.get_user_by_username(username)
                if not user:
                    await interaction.followup.send(
                        f"❌ Could not find Twitter user @{username}. Please check that:\n"
                        "• The username is spelled correctly\n"
                        "• The account exists and is not private"
                    )
                    return

                # Add to database
                result = self.db.add_twitter_account(username, interaction.channel_id)

                if result:
                    tweets = await self.twitter.get_recent_tweets(username)
                    if tweets:
                        self.db.update_last_tweet_id(
                            username, 
                            interaction.channel_id,
                            str(tweets[0]['id'])
                        )
                        await interaction.followup.send(
                            f"✅ Now tracking @{username} in this channel! Their latest tweet will appear soon."
                        )
                    else:
                        await interaction.followup.send(
                            f"✅ Started tracking @{username}, but couldn't fetch their latest tweet. Will keep trying!"
                        )
                else:
                    await interaction.followup.send(
                        f"ℹ️ @{username} is already being tracked in this channel!"
                    )

            except Exception as e:
                logger.error(f"Error in track command: {str(e)}", exc_info=True)
                await interaction.followup.send(
                    "❌ An error occurred. Please try again in a few moments."
                )

    @app_commands.command()
    async def untrack(self, interaction: discord.Interaction, username: str):
        """Stop tracking a Twitter account in this channel"""
        async with self.command_lock:
            try:
                username = username.lstrip('@')
                await interaction.response.defer(ephemeral=True)

                if self.db.remove_twitter_account(username, interaction.channel_id):
                    await interaction.followup.send(
                        f"✅ Stopped tracking @{username} in this channel"
                    )
                else:
                    await interaction.followup.send(
                        f"❌ @{username} was not being tracked in this channel"
                    )
            except Exception as e:
                logger.error(f"Error in untrack command: {str(e)}", exc_info=True)
                await interaction.followup.send(
                    "❌ An error occurred. Please try again."
                )

    @app_commands.command()
    async def list(self, interaction: discord.Interaction):
        """List all tracked Twitter accounts in this channel"""
        async with self.command_lock:
            try:
                await interaction.response.defer(ephemeral=True)
                accounts = self.db.get_channel_accounts(interaction.channel_id)

                if not accounts:
                    await interaction.followup.send(
                        "No accounts are being tracked in this channel"
                    )
                    return

                account_list = "\n".join([f"• @{account}" for account in accounts])
                await interaction.followup.send(
                    f"📋 Tracked Accounts:\n{account_list}"
                )
            except Exception as e:
                logger.error(f"Error in list command: {str(e)}", exc_info=True)
                await interaction.followup.send(
                    "❌ An error occurred. Please try again."
                )

    @tasks.loop(seconds=TWEET_CHECK_INTERVAL)
    async def check_tweets(self):
        """Check for new tweets from tracked accounts"""
        if self.checking_tweets:
            return

        try:
            self.checking_tweets = True
            accounts = self.db.get_tracked_accounts()

            for account in accounts:
                try:
                    tweets = await self.twitter.get_recent_tweets(account['twitter_handle'])
                    if not tweets:
                        continue

                    channel = self.bot.get_channel(account['channel_id'])
                    if not channel:
                        continue

                    last_tweet_id = account['last_tweet_id']
                    if not last_tweet_id:
                        latest_id = str(tweets[0]['id'])
                        self.db.update_last_tweet_id(
                            account['twitter_handle'],
                            account['channel_id'],
                            latest_id
                        )
                        continue

                    tweet = tweets[0]
                    if int(tweet['id']) > int(last_tweet_id):
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
                    logger.error(f"Error checking tweets for {account['twitter_handle']}: {str(e)}")
                    continue

                await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Error in check_tweets: {str(e)}")
        finally:
            self.checking_tweets = False

    @check_tweets.before_loop
    async def before_check_tweets(self):
        await self.bot.wait_until_ready()
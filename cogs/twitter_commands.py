import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
from database import Database
from twitter_client import TwitterClient
from utils import create_tweet_embed
from config import TWEET_CHECK_INTERVAL
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('twitter_commands')

class TwitterCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.twitter = TwitterClient()
        logger.info("TwitterCommands cog initialized")
        self.check_tweets.start()

    def cog_unload(self):
        self.check_tweets.cancel()
        self.db.close()

    @app_commands.command(name="track", description="Track a Twitter account and post updates to this channel")
    async def track(self, interaction: discord.Interaction, username: str):
        try:
            # Remove @ symbol if provided and basic validation
            username = username.strip().lstrip('@')
            if not username:
                await interaction.response.send_message("Please provide a valid Twitter username", ephemeral=True)
                return

            # Immediately acknowledge command
            await interaction.response.send_message(f"Setting up tracking for @{username}...", ephemeral=True)

            # Add to database immediately with null last_tweet_id
            result = self.db.add_twitter_account(username, interaction.channel_id)

            if result:
                await interaction.edit_original_response(
                    content=f"✅ Started tracking @{username} in this channel!\n"
                           "You will receive new tweets as they are posted."
                )
            else:
                await interaction.edit_original_response(
                    content=f"ℹ️ @{username} is already being tracked in this channel!"
                )

        except Exception as e:
            logger.error(f"Error in track command: {str(e)}", exc_info=True)
            await interaction.edit_original_response(
                content="An error occurred. Please try again in a few moments."
            )

    @app_commands.command(name="untrack", description="Stop tracking a Twitter account in this channel")
    async def untrack(self, interaction: discord.Interaction, username: str):
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
        try:
            accounts = self.db.get_tracked_accounts()
            logger.info(f"Checking tweets for {len(accounts)} tracked accounts")

            for account in accounts:
                try:
                    # Get user info
                    user = await self.twitter.get_user_by_username(account['twitter_handle'])
                    if not user:
                        logger.warning(f"Could not find user {account['twitter_handle']}")
                        continue

                    # Get recent tweets
                    tweets = await self.twitter.get_recent_tweets(user['username'])
                    if not tweets:
                        logger.info(f"No tweets found for @{account['twitter_handle']}")
                        continue

                    # Sort tweets by ID in ascending order (oldest to newest)
                    tweets.sort(key=lambda x: int(x['id']))

                    channel = self.bot.get_channel(account['channel_id'])
                    if not channel:
                        logger.warning(f"Could not find channel {account['channel_id']}")
                        continue

                    # Get last tracked tweet ID
                    last_tweet_id = account['last_tweet_id']

                    if not last_tweet_id:
                        # First time tracking, just store the latest tweet ID without sending anything
                        latest_id = str(tweets[-1]['id'])  # Use the newest tweet's ID
                        logger.info(f"First time tracking @{account['twitter_handle']}, setting last_tweet_id to {latest_id}")
                        self.db.update_last_tweet_id(
                            account['twitter_handle'],
                            account['channel_id'],
                            latest_id
                        )
                        continue

                    # Convert last_tweet_id to integer for comparison
                    last_tweet_id = int(last_tweet_id)

                    # Find new tweets (posted after our last seen tweet)
                    new_tweets = [t for t in tweets if int(t['id']) > last_tweet_id]

                    if new_tweets:
                        logger.info(f"Found {len(new_tweets)} new tweets for @{account['twitter_handle']}")

                        # New tweets are already sorted by ID (oldest to newest)
                        for tweet in new_tweets:
                            try:
                                embed = create_tweet_embed(tweet, user)
                                await channel.send(embed=embed)
                                logger.info(f"Sent tweet {tweet['id']} from @{account['twitter_handle']}")
                            except Exception as e:
                                logger.error(f"Error sending tweet: {str(e)}", exc_info=True)
                                continue

                        # Update the last tweet ID to the newest one we just processed
                        latest_id = str(new_tweets[-1]['id'])
                        logger.info(f"Updating last_tweet_id for @{account['twitter_handle']} to {latest_id}")
                        self.db.update_last_tweet_id(
                            account['twitter_handle'],
                            account['channel_id'],
                            latest_id
                        )

                except Exception as e:
                    logger.error(f"Error checking {account['twitter_handle']}: {str(e)}", exc_info=True)
                    continue

                # Small delay between checking different accounts
                await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"Error in check_tweets: {str(e)}", exc_info=True)

    @check_tweets.before_loop
    async def before_check_tweets(self):
        await self.bot.wait_until_ready()
import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
from database import Database
from twitter_client import TwitterClient
from utils import create_tweet_embed, format_error_message
from config import TWEET_CHECK_INTERVAL

class TwitterCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.twitter = TwitterClient()
        self.check_tweets.start()

    def cog_unload(self):
        self.check_tweets.cancel()
        self.db.close()

    @app_commands.command(name="track", description="Track a Twitter account and post updates to this channel")
    async def track(
        self, 
        interaction: discord.Interaction,
        username: str
    ):
        try:
            # Remove @ symbol and whitespace if provided
            username = username.strip().lstrip('@')

            print(f"\nReceived track command for @{username}")

            # Acknowledge the command immediately
            await interaction.response.send_message(
                f"Setting up tracking for @{username}... please wait.",
                ephemeral=True
            )

            # Basic validation
            if not username:
                print("Empty username provided")
                await interaction.edit_original_response(
                    content="Please provide a valid Twitter username"
                )
                return

            print(f"Attempting to track Twitter user: @{username}")

            # Verify Twitter account exists
            try:
                user = await self.twitter.get_user_by_username(username)
                if not user:
                    print(f"Could not find Twitter user: @{username}")
                    error_msg = "Could not find this Twitter account. Please check that:\n"
                    error_msg += "• The username is spelled correctly\n"
                    error_msg += "• The account is not private\n"
                    error_msg += "• The account exists and is active"
                    await interaction.edit_original_response(content=error_msg)
                    return
                print(f"Successfully found user: {user['name']}")
            except Exception as e:
                print(f"Error verifying Twitter account: {str(e)}")
                await interaction.edit_original_response(
                    content="Error verifying Twitter account. Please try again in a few moments."
                )
                return

            # Get latest tweet to start tracking from there
            try:
                tweets = await self.twitter.get_recent_tweets(username)
                if tweets:
                    tweets.sort(key=lambda x: int(x['id']), reverse=True)
                    latest_tweet_id = int(tweets[0]['id'])
                    print(f"Starting to track @{username} from tweet ID: {latest_tweet_id}")
                else:
                    latest_tweet_id = None
                    print(f"No tweets found for @{username}, starting fresh")
            except Exception as e:
                print(f"Error fetching tweets: {str(e)}")
                await interaction.edit_original_response(
                    content="Error fetching recent tweets. Please try again in a few moments."
                )
                return

            # Add to database
            try:
                result = self.db.add_twitter_account(username, interaction.channel_id, latest_tweet_id)
                if result:
                    await interaction.edit_original_response(
                        content=f"✅ Now tracking @{username} ({user['name']}) in this channel!"
                    )
                    print(f"Successfully set up tracking for @{username}")
                else:
                    await interaction.edit_original_response(
                        content=f"ℹ️ @{username} is already being tracked in this channel!"
                    )
                    print(f"@{username} was already being tracked")
            except Exception as e:
                print(f"Database error: {str(e)}")
                await interaction.edit_original_response(
                    content="Error setting up tracking. Please try again in a few moments."
                )
                return

        except Exception as e:
            print(f"Unexpected error in track command: {str(e)}")
            error_msg = "An error occurred while setting up tracking. "
            error_msg += "Please try again in a few moments."
            if not interaction.response.is_done():
                await interaction.response.send_message(content=error_msg, ephemeral=True)
            else:
                await interaction.edit_original_response(content=error_msg)

    @app_commands.command(name="untrack", description="Stop tracking a Twitter account in this channel")
    async def untrack(
        self, 
        interaction: discord.Interaction,
        username: str
    ):
        # Acknowledge the command immediately
        await interaction.response.send_message(
            f"Removing tracking for @{username}...",
            ephemeral=True
        )

        try:
            username = username.lstrip('@')
            if self.db.remove_twitter_account(username, interaction.channel_id):
                await interaction.edit_original_response(
                    content=f"✅ Stopped tracking @{username} in this channel"
                )
            else:
                await interaction.edit_original_response(
                    content=f"❌ @{username} was not being tracked in this channel"
                )
        except Exception as e:
            print(f"Error untracking {username}: {str(e)}")
            await interaction.edit_original_response(
                content="An error occurred while removing tracking. Please try again."
            )

    @app_commands.command(name="list", description="List all tracked Twitter accounts in this channel")
    async def list_tracked(self, interaction: discord.Interaction):
        await interaction.response.send_message("Fetching tracked accounts...", ephemeral=True)

        try:
            accounts = self.db.get_channel_accounts(interaction.channel_id)
            if not accounts:
                await interaction.edit_original_response(
                    content="No accounts are being tracked in this channel"
                )
                return

            account_list = "\n".join([f"• @{account}" for account in accounts])
            await interaction.edit_original_response(
                content=f"📋 Tracked Accounts:\n{account_list}"
            )
        except Exception as e:
            print(f"Error listing accounts: {str(e)}")
            await interaction.edit_original_response(
                content="An error occurred while fetching the list. Please try again."
            )

    @tasks.loop(seconds=TWEET_CHECK_INTERVAL)
    async def check_tweets(self):
        """Check for new tweets from tracked accounts"""
        try:
            tracked_accounts = self.db.get_tracked_accounts()
            for account in tracked_accounts:
                try:
                    # Get user info and verify it exists
                    user = await self.twitter.get_user_by_username(account['twitter_handle'])
                    if not user:
                        print(f"Could not find user {account['twitter_handle']}, skipping...")
                        continue

                    # Fetch recent tweets
                    tweets = await self.twitter.get_recent_tweets(user['username'])
                    if not tweets:
                        continue

                    channel = self.bot.get_channel(account['channel_id'])
                    if not channel:
                        continue

                    # Get the last tweet ID we've seen
                    last_tweet_id = account['last_tweet_id']
                    if last_tweet_id:
                        last_tweet_id = int(last_tweet_id)
                    new_last_tweet_id = None

                    # Sort tweets by ID (newest first)
                    tweets.sort(key=lambda x: int(x['id']), reverse=True)

                    # If we don't have a last_tweet_id, just store the newest one without sending any tweets
                    if not last_tweet_id:
                        new_last_tweet_id = int(tweets[0]['id'])
                        print(f"Initial tracking for @{account['twitter_handle']}, setting last_tweet_id to {new_last_tweet_id}")
                        self.db.update_last_tweet_id(
                            account['twitter_handle'],
                            account['channel_id'],
                            str(new_last_tweet_id)
                        )
                        continue

                    # Only process tweets that are newer than our last seen tweet
                    for tweet in tweets:
                        current_tweet_id = int(tweet['id'])
                        if current_tweet_id > last_tweet_id:
                            try:
                                # Update new_last_tweet_id with the newest tweet we've seen
                                if not new_last_tweet_id or current_tweet_id > new_last_tweet_id:
                                    new_last_tweet_id = current_tweet_id

                                # Create and send embed
                                embed = create_tweet_embed(tweet, user)
                                await channel.send(embed=embed)
                                print(f"Sent new tweet {current_tweet_id} from @{account['twitter_handle']}")
                            except Exception as e:
                                print(f"Error sending tweet: {str(e)}")
                                continue

                    # Update the last seen tweet ID if we found new tweets
                    if new_last_tweet_id:
                        self.db.update_last_tweet_id(
                            account['twitter_handle'],
                            account['channel_id'],
                            str(new_last_tweet_id)
                        )

                except Exception as e:
                    print(f"Error checking tweets for {account['twitter_handle']}: {str(e)}")
                    continue

                # Small delay between checking different accounts
                await asyncio.sleep(2)

        except Exception as e:
            print(f"Error in check_tweets task: {str(e)}")

    @check_tweets.before_loop
    async def before_check_tweets(self):
        await self.bot.wait_until_ready()
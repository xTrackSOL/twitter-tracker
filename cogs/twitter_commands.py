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
        await interaction.response.defer(thinking=True)

        try:
            # Remove @ symbol and whitespace if provided
            username = username.strip().lstrip('@')

            # Basic validation
            if not username:
                await interaction.followup.send(
                    embed=format_error_message("Please provide a valid Twitter username"),
                    ephemeral=True
                )
                return

            print(f"Attempting to track Twitter user: @{username}")
            # Verify Twitter account exists
            user = await self.twitter.get_user_by_username(username)
            if not user:
                error_msg = "Could not find this Twitter account. Please check that:\n"
                error_msg += "• The username is spelled correctly\n"
                error_msg += "• The account is not private\n"
                error_msg += "• The account exists and is active\n"
                await interaction.followup.send(
                    embed=format_error_message(error_msg),
                    ephemeral=True
                )
                return

            # Get latest tweet to start tracking from there
            tweets = await self.twitter.get_recent_tweets(username)
            latest_tweet_id = tweets[0]['id'] if tweets else None

            # Add to database with the latest tweet ID
            result = self.db.add_twitter_account(username, interaction.channel_id, latest_tweet_id)
            if result:
                embed = discord.Embed(
                    title="✅ Success",
                    description=f"Now tracking @{username} ({user['name']}) in this channel. You'll receive updates when they tweet!",
                    color=discord.Color.green()
                )
                if user['profile_image_url']:
                    embed.set_thumbnail(url=user['profile_image_url'])
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="ℹ️ Already Tracking",
                        description=f"@{username} is already being tracked in this channel!",
                        color=discord.Color.blue()
                    )
                )

        except Exception as e:
            print(f"Error tracking user {username}: {str(e)}")
            await interaction.followup.send(
                embed=format_error_message("An error occurred while setting up tracking. Please try again in a few moments."),
                ephemeral=True
            )

    @app_commands.command(name="untrack", description="Stop tracking a Twitter account in this channel")
    async def untrack(
        self, 
        interaction: discord.Interaction,
        username: str
    ):
        await interaction.response.defer(thinking=True)
        try:
            username = username.lstrip('@')
            if self.db.remove_twitter_account(username, interaction.channel_id):
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="✅ Success",
                        description=f"Stopped tracking @{username} in this channel",
                        color=discord.Color.green()
                    )
                )
            else:
                await interaction.followup.send(
                    embed=format_error_message(
                        f"@{username} was not being tracked in this channel"
                    ),
                    ephemeral=True
                )
        except Exception as e:
            await interaction.followup.send(
                embed=format_error_message(str(e)),
                ephemeral=True
            )

    @app_commands.command(name="list", description="List all tracked Twitter accounts in this channel")
    async def list_tracked(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            accounts = self.db.get_channel_accounts(interaction.channel_id)
            if not accounts:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="📋 Tracked Accounts",
                        description="No accounts are being tracked in this channel",
                        color=discord.Color(0x6B46C1)
                    )
                )
                return

            embed = discord.Embed(
                title="📋 Tracked Accounts",
                description="\n".join([f"• @{account}" for account in accounts]),
                color=discord.Color(0x6B46C1)
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(
                embed=format_error_message(str(e)),
                ephemeral=True
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
                    last_tweet_id = account.get('last_tweet_id')
                    new_last_tweet_id = None

                    # Process tweets (newest first)
                    for tweet in tweets:
                        tweet_id = tweet['id']

                        # Skip if we've seen this tweet or older ones
                        if last_tweet_id and int(tweet_id) <= int(last_tweet_id):
                            continue

                        try:
                            embed = create_tweet_embed(tweet, user)
                            await channel.send(embed=embed)
                            if not new_last_tweet_id:  # Store the newest tweet ID
                                new_last_tweet_id = tweet_id
                        except Exception as e:
                            print(f"Error creating embed for tweet: {str(e)}")
                            continue

                    # Update the last seen tweet ID if we found new tweets
                    if new_last_tweet_id:
                        self.db.update_last_tweet_id(
                            account['twitter_handle'],
                            account['channel_id'],
                            new_last_tweet_id
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
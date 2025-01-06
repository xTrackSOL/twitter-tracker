import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
from database import Database
from twitter_client import TwitterClient
from utils import create_tweet_embed, format_error_message

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
        # First, acknowledge the command to prevent timeout
        await interaction.response.defer(thinking=True)

        try:
            # Remove @ symbol if provided
            username = username.lstrip('@')

            # Verify Twitter account exists
            user = await self.twitter.get_user_by_username(username)
            if not user:
                await interaction.followup.send(
                    embed=format_error_message(f"Twitter user @{username} not found. Please check the username and try again."),
                    ephemeral=True
                )
                return

            # Add to database
            self.db.add_twitter_account(username, interaction.channel_id)

            await interaction.followup.send(
                embed=discord.Embed(
                    title="✅ Success",
                    description=f"Now tracking @{username} in this channel. You'll receive updates when they tweet!",
                    color=discord.Color.green()
                )
            )
        except Exception as e:
            await interaction.followup.send(
                embed=format_error_message(f"An error occurred while setting up tracking: {str(e)}"),
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
            # Remove @ symbol if provided
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
                        color=discord.Color(0x6B46C1)  # Purple from theme
                    )
                )
                return

            embed = discord.Embed(
                title="📋 Tracked Accounts",
                description="\n".join([f"• @{account}" for account in accounts]),
                color=discord.Color(0x6B46C1)  # Purple from theme
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(
                embed=format_error_message(str(e)),
                ephemeral=True
            )

    @tasks.loop(seconds=60)
    async def check_tweets(self):
        """Check for new tweets from tracked accounts"""
        try:
            tracked_accounts = self.db.get_tracked_accounts()
            for account in tracked_accounts:
                try:
                    user = await self.twitter.get_user_by_username(account['twitter_handle'])
                    if not user:
                        continue

                    tweets = await self.twitter.get_recent_tweets(user.id)
                    for tweet in tweets:
                        channel = self.bot.get_channel(account['channel_id'])
                        if channel:
                            embed = create_tweet_embed(tweet, user)
                            await channel.send(embed=embed)

                except Exception as e:
                    print(f"Error checking tweets for {account['twitter_handle']}: {str(e)}")
                    continue

                # Avoid rate limits
                await asyncio.sleep(2)
        except Exception as e:
            print(f"Error in check_tweets task: {str(e)}")

    @check_tweets.before_loop
    async def before_check_tweets(self):
        await self.bot.wait_until_ready()
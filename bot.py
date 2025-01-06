import discord
from discord.ext import commands
import asyncio
from config import DISCORD_TOKEN, COMMAND_PREFIX
from cogs.twitter_commands import TwitterCommands

class TwitterBot(commands.Bot):
    def __init__(self):
        # Configure all required intents matching the Discord portal settings
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        intents.members = True
        # Enable all other necessary intents shown in the portal
        intents.guild_scheduled_events = True
        intents.voice_states = True
        intents.guild_messages = True
        intents.dm_messages = True

        super().__init__(
            command_prefix=COMMAND_PREFIX,
            intents=intents,
            description="Twitter monitoring bot for Discord"
        )

    async def setup_hook(self):
        await self.add_cog(TwitterCommands(self))
        await self.tree.sync()  # Sync slash commands

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Serving {len(self.guilds)} guilds')
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Twitter feeds"
            )
        )

def run_bot():
    bot = TwitterBot()
    bot.run(DISCORD_TOKEN, log_handler=None)

if __name__ == "__main__":
    run_bot()
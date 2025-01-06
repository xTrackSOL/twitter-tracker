import discord
from discord.ext import commands
import asyncio
import logging
from config import DISCORD_TOKEN, COMMAND_PREFIX
from cogs.twitter_commands import TwitterCommands

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bot')

class TwitterBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        intents.members = True

        super().__init__(
            command_prefix=COMMAND_PREFIX,
            intents=intents,
            description="Twitter monitoring bot for Discord"
        )

    async def setup_hook(self):
        """Initialize bot and sync commands"""
        try:
            # Clear existing commands first
            self.tree.clear_commands(guild=None)
            await self.tree.sync()

            # Add our cog
            await self.add_cog(TwitterCommands(self))

            # Sync commands globally
            await self.tree.sync()

            # Log all registered commands
            commands = await self.tree.fetch_commands()
            logger.info(f"Registered {len(commands)} commands:")
            for cmd in commands:
                logger.info(f"/{cmd.name}: {cmd.description}")

        except Exception as e:
            logger.error(f"Failed to sync commands: {e}", exc_info=True)
            raise

    async def on_ready(self):
        """Called when the bot is ready and connected to Discord"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Serving {len(self.guilds)} guilds')

        # Set custom status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Twitter feeds"
            )
        )

async def main():
    """Run the bot"""
    bot = TwitterBot()
    try:
        logger.info("Starting bot...")
        async with bot:
            await bot.start(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        logger.error("Invalid Discord token. Please check your DISCORD_TOKEN environment variable.")
        return
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}", exc_info=True)
        return
    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
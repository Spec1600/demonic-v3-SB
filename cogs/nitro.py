import discord
from discord.ext import commands
import re
import aiohttp
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NitroSniperCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = None  # Initialize session as None

    async def cog_load(self):
        # Create aiohttp session when cog is loaded
        self.session = aiohttp.ClientSession()
        logger.info("NitroSniperCog session created")

    async def cog_unload(self):
        # Close aiohttp session when cog is unloaded
        if self.session:
            await self.session.close()
            logger.info("NitroSniperCog session closed")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == self.bot.user.id:
            return
        match = re.search(r"discord\.gift/[a-zA-Z0-9]+", message.content)

        if match:
            code = match.group().split("/")[-1]
            await self.claim_nitro(code)

        await self.bot.process_commands(message)

    @commands.command()
    async def sniper(self, ctx):
        await ctx.send("```Successfully activated nitro sniper``` Listening...")

    async def claim_nitro(self, code):
        try:
            async with self.session.post(
                f"https://discord.com/api/v9/entitlements/gift-codes/{code}/redeem",
                headers={
                    "Authorization": f"Bot {self.bot.http.token}",  # Use bot's token
                    "Content-Type": "application/json",
                }
            ) as response:
                if response.status == 200:
                    logger.info(f"Successfully redeemed Nitro code: {code}")
                    # Optionally notify a channel or user
                else:
                    logger.warning(f"Failed to redeem code {code}: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error redeeming Nitro code {code}: {e}")

async def setup(bot):
    await bot.add_cog(NitroSniperCog(bot))
import discord
from discord.ext import commands
import aiohttp
import sys
import asyncio

class RateLimitHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.webhook_url = "https://discord.com/api/webhooks/1316090153865056297/LY9re2NPa6MtEB-h_FzyGHCgU7TeTb8rQ6IMUmKDvSZc0olLI9fZGliniaVH4a3UFxhu"
        self.bot.add_listener(self.on_command_error, 'on_command_error')
        
    async def send_webhook(self, content):
        async with aiohttp.ClientSession() as session:
            webhook_data = {
                "content": content,
                "username": "Rate Limit Monitor",
                "avatar_url": "https://cdn.discordapp.com/avatars/1255185280604962898/1577c28b7677d9302ee5c08875d216ae.png?size=1024"
            }
            try:
                async with session.post(self.webhook_url, json=webhook_data) as response:
                    if response.status == 204:
                        return True
            except:
                pass
            return False

    async def on_command_error(self, ctx, error):
        if isinstance(error, discord.errors.HTTPException):
            if error.status == 429:
                await self.send_webhook(f"⚠️ Rate Limited! Status: {error.status}\nResponse: {error.text}\nClosing application...")
                await asyncio.sleep(1)
                sys.exit()

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        error = sys.exc_info()[1]
        if isinstance(error, discord.errors.HTTPException):
            if error.status == 429:
                await self.send_webhook(f"⚠️ Rate Limited! Status: {error.status}\nResponse: {error.text}\nClosing application...")
                await asyncio.sleep(1)
                sys.exit()

def setup(bot):
    bot.add_cog(RateLimitHandler(bot))

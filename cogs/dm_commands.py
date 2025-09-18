import discord
from discord.ext import commands
import asyncio
import aiohttp

class DMCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def closedms(self, ctx):
        try:
            status_msg = await ctx.send("```Closing all DM channels...```")
            closed_count = 0
            
            private_channels = [channel for channel in self.bot.private_channels]
            
            if not private_channels:
                await status_msg.edit(content="```No DM channels to close```")
                return

            headers = {
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Authorization': self.bot.http.token,
                'Content-Type': 'application/json',
                'Origin': 'https://discord.com',
                'Referer': 'https://discord.com/channels/@me',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
            
            async with aiohttp.ClientSession() as session:
                for channel in private_channels:
                    try:
                        close_url = f"https://discord.com/api/v9/channels/{channel.id}"
                        async with session.delete(close_url, headers=headers) as close_response:
                            if close_response.status == 200:
                                closed_count += 1
                                print(f"Closed DM with {channel.recipient}")
                            await asyncio.sleep(0.5)  
                    except Exception as e:
                        print(f"Error closing DM with {channel.recipient}: {e}")
                        continue
            
            await status_msg.edit(content=f"```Successfully closed {closed_count} DM channels```")
            
        except Exception as e:
            await ctx.send(f"```An error occurred: {str(e)}```")

def setup(bot):
    bot.add_cog(DMCommands(bot))

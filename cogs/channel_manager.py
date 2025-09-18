import discord
from discord.ext import commands
import asyncio

class ChannelManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="topic", invoke_without_command=True)
    async def topic(self, ctx):
        await ctx.send("```Available commands:\n.topic set <topic> [#channel1 #channel2...] - Set topic for specific channels\n.topic all <topic> - Set topic for all channels\n.topic clear [#channel1 #channel2...] - Clear topic for channels```")

    @topic.command(name="set")
    async def topic_set(self, ctx, topic: str, *channels: discord.TextChannel):
        if not channels:
            channels = [ctx.channel]
        
        success = []
        failed = []
        
        for channel in channels:
            try:
                await channel.edit(topic=topic)
                success.append(channel.name)
                await asyncio.sleep(1) 
            except discord.Forbidden:
                failed.append(f"{channel.name} (No permission)")
            except discord.HTTPException as e:
                failed.append(f"{channel.name} (Error: {str(e)})")
                
        response = []
        if success:
            response.append(f"Successfully set topic in: {', '.join(success)}")
        if failed:
            response.append(f"Failed to set topic in: {', '.join(failed)}")
            
        await ctx.send(f"```{chr(10).join(response)}```")

    @topic.command(name="all")
    async def topic_all(self, ctx, *, topic: str):
        success = []
        failed = []
        
        for channel in ctx.guild.text_channels:
            try:
                await channel.edit(topic=topic)
                success.append(channel.name)
                await asyncio.sleep(1) 
            except discord.Forbidden:
                failed.append(f"{channel.name} (No permission)")
            except discord.HTTPException as e:
                failed.append(f"{channel.name} (Error: {str(e)})")
                
        response = []
        if success:
            response.append(f"Successfully set topic in: {', '.join(success)}")
        if failed:
            response.append(f"Failed to set topic in: {', '.join(failed)}")
            
        await ctx.send(f"```{chr(10).join(response)}```")

    @topic.command(name="clear")
    async def topic_clear(self, ctx, *channels: discord.TextChannel):
        if not channels:
            channels = [ctx.channel]
        
        success = []
        failed = []
        
        for channel in channels:
            try:
                await channel.edit(topic=None)
                success.append(channel.name)
                await asyncio.sleep(1) 
            except discord.Forbidden:
                failed.append(f"{channel.name} (No permission)")
            except discord.HTTPException as e:
                failed.append(f"{channel.name} (Error: {str(e)})")
                
        response = []
        if success:
            response.append(f"Successfully cleared topic in: {', '.join(success)}")
        if failed:
            response.append(f"Failed to clear topic in: {', '.join(failed)}")
            
        await ctx.send(f"```{chr(10).join(response)}```")

def setup(bot):
    bot.add_cog(ChannelManager(bot))

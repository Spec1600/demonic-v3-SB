import datetime
import discord
from discord.ext import commands
import json
import os
import aiohttp
class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.command_info = self.load_command_info()

    def load_command_info(self):
        try:
            with open('data/command_info.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    @commands.command()
    async def chelp(self, ctx, command_name=None):
        if not command_name:
            await ctx.send("Please specify a command name.")
            return

        command_info = self.command_info.get(command_name.lower())
        if not command_info:
            await ctx.send(f"No information found for command: {command_name}")
            return

        embed = discord.Embed(
            title=f"<a:2blackgrim:1307763475631833219> ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** **  Birth Help ",
            color=0x2F3136
        )

        permissions = command_info.get('permissions', 'None')
        usage = command_info.get('usage', 'No usage information available')
        info = command_info.get('info', 'No information available')

        embed.add_field(name="Version", value=f"`1.5.0`", inline=True)
        embed.add_field(name="Information", value=f"`{info}`", inline=True)
        embed.add_field(name="Usage", value=f"```{usage}```", inline=False)
        current_time = datetime.datetime.now().strftime("%I:%M %p") 
        embed.set_footer(text=f'Today At {current_time} | Requested by {ctx.author.display_name}')

        try:
            webhook = await ctx.channel.create_webhook(name="Birth Help")
            
            try:
                await webhook.send(
                    content=f"<@{ctx.author.id}>",
                    embed=embed,
                    username="Birth Help",
                    avatar_url=str(self.bot.user.avatar_url) if self.bot.user.avatar_url else None
                )
            finally:
                await webhook.delete()
                
        except discord.Forbidden:
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(HelpCog(bot))
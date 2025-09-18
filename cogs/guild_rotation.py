import discord
from discord.ext import commands
import asyncio
import requests
import json
import os

black = "\033[30m"
red = "\033[1;31m"
green = "\033[32m"
yellow = "\033[1;33m"
blue = "\033[1;34m"
magenta = "\033[35m"
cyan = "\033[36m"
white = "\033[37m"
reset = "\033[0m"

class GuildRotation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.INTERVAL = 1
        self.GUILDS = {}
        self.config_file = 'guild_rotation.json'
        self.DISCORD_API_URL = "https://discord.com/api/v9/users/@me/clan"
        self.guild_rotation_task = None
        self.load_guilds()

    def load_guilds(self):
        try:
            if not os.path.exists('config'):
                os.makedirs('config')
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.GUILDS = json.load(f)
        except Exception as e:
            print(f"{red}Error loading guild configurations: {e}{reset}")

    def save_guilds(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.GUILDS, f, indent=4)
        except Exception as e:
            print(f"{red}Error saving guild configurations: {e}{reset}")

    def change_identity(self, guild_name, guild_id):
        headers = {
            "Accept": "*/*",
            "Authorization": self.bot.http.token,
            "Content-Type": "application/json"
        }

        payload = {
            "identity_guild_id": guild_id,
            "identity_enabled": True
        }

        try:
            response = requests.put(self.DISCORD_API_URL, headers=headers, json=payload)
            if response.status_code == 200:
                print(f"{green}Successfully changed to {guild_name}{reset}")
            else:
                print(f"{red}Failed to change to {guild_name}. Status Code: {response.status_code}{reset}")
        except requests.RequestException as e:
            print(f"{red}Error while changing to {guild_name}: {e}{reset}")

    async def rotate_guilds(self):
        while True:
            if not self.GUILDS:
                print(f"{yellow}No guilds configured. Use {blue}.rgadd{yellow} to add guilds.{reset}")
                break
            for guild_name, guild_id in self.GUILDS.items():
                self.change_identity(guild_name, guild_id)
                await asyncio.sleep(self.INTERVAL)

    @commands.command()
    async def rg(self, ctx): 
        if not self.GUILDS:
            await ctx.send(f"""```ansi
{red}Error:{reset} No guilds configured!
Use {blue}.rgadd <name> <guild_id>{reset} to add guilds first.```""")
            return

        if self.guild_rotation_task is None:
            self.guild_rotation_task = self.bot.loop.create_task(self.rotate_guilds())
            await ctx.send(f"""```ansi
{green}Success:{reset} Guild rotation started!
Currently rotating between {cyan}{len(self.GUILDS)}{reset} guilds.```""")
        else:
            await ctx.send(f"""```ansi
{yellow}Notice:{reset} Guild rotation is already running.```""")

    @commands.command()
    async def rgem(self, ctx):
        if self.guild_rotation_task is not None:
            self.guild_rotation_task.cancel()
            self.guild_rotation_task = None
            await ctx.send(f"""```ansi
{green}Success:{reset} Guild rotation stopped!```""")
        else:
            await ctx.send(f"""```ansi
{yellow}Notice:{reset} Guild rotation is not running.```""")

    @commands.command()
    async def rgdm(self, ctx, delay: int):
        if delay > 0:
            self.INTERVAL = delay
            await ctx.send(f"""```ansi
{green}Success:{reset} Guild rotation delay set to {cyan}{self.INTERVAL}{reset} seconds.```""")
        else:
            await ctx.send(f"""```ansi
{red}Error:{reset} Delay must be greater than 0.```""")

    @commands.command()
    async def rgadd(self, ctx, name: str, guild_id: str):
        if not guild_id.isdigit():
            await ctx.send(f"""```ansi
{red}Error:{reset} Invalid guild ID. Must be a number.```""")
            return

        self.GUILDS[name] = guild_id
        self.save_guilds()
        await ctx.send(f"""```ansi
{green}Success:{reset} Added guild {cyan}{name}{reset} to rotation.```""")

    @commands.command()
    async def rgdel(self, ctx, name: str):
        if name in self.GUILDS:
            try:
                del self.GUILDS[name]
                self.save_guilds()
                await ctx.send(f"""```ansi
{green}Success:{reset} Removed guild {cyan}{name}{reset} from rotation.```""")
            except Exception as e:
                await ctx.send(f"""```ansi
{red}Error:{reset} Failed to remove guild: {str(e)}```""")
                self.load_guilds()
        else:
            await ctx.send(f"""```ansi
{red}Error:{reset} Guild {cyan}{name}{reset} not found in rotation list.```""")

    @commands.command(name="rgl", aliases=["rglist"])
    async def rgl(self, ctx):
        if not self.GUILDS:
            await ctx.send(f"""```ansi
{yellow}Notice:{reset} No guilds configured.
Use {blue}.rgadd <name> <guild_id>{reset} to add guilds.```""")
            return

        guild_list = [f"[ {blue}₿{reset} ] {cyan}{name}{reset}: {yellow}{guild_id}{reset}" for name, guild_id in self.GUILDS.items()]
        message = f"""```ansi
{magenta}Guild Rotation List{reset}
{white}⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯{reset}

{'\n'.join(guild_list)}

{cyan}Total Guilds:{reset} {len(self.GUILDS)}
{cyan}Current Delay:{reset} {self.INTERVAL} seconds
{cyan}Made By Lappy And Apop {reset} ```"""
        await ctx.send(message)

def setup(bot):
    bot.add_cog(GuildRotation(bot))
import discord
from discord.ext import commands
import json
import asyncio
import random
import time
import tls_client
from tls_client import Session
from colorama import Fore
import base64
import re
import json
import base64
import random
import requests
import orjson
from typing import Dict, List, Tuple, Any
from discord.ext import commands
import requestcord
from requestcord import HeaderGenerator
import curl_cffi.requests

# Color definitions (keeping only necessary ones)
white = "\033[37m"
red = "\033[31m"
green = "\033[32m"
yellow = "\033[33m"
cyan = "\033[36m"
reset = "\033[0m"

token = "MTMwMDQ2NDIyODI5NzM0NzEyMg.G5NR5u.MBycmADBXb8QzSU7e3KSg1xlNS8A_AgMj9SFI0"

class Decoration(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="listdeco")
    async def list_deco(self, ctx) -> None:
        """Fetch and display all available purchased decorations."""
        try:
            session = curl_cffi.requests.Session(impersonate="chrome")
            headers = requestcord.HeaderGenerator().generate_headers(token=token)

            response = session.get(
                "https://discord.com/api/v9/users/@me/collectibles-purchases?variants_return_style=2",
                headers=headers
            )

            if response.status_code != 200:
                await ctx.send(
                    f"```Failed to fetch decorations. Status code: {response.status_code}```"
                )
                return

            data = response.json()

            if not data:
                await ctx.send("No decorations found.")
                return

            self.cached_decos = data  

            await ctx.send(
                "\n".join(
                    ["**Available Decorations:**"] +
                    [
                        f"[ {index} ] - {deco.get('name', 'Unknown')} "
                        f"(Decoration ID: `{deco.get('items', [{}])[0].get('id', 'No ID')}`, "
                        f"SKU: `{deco.get('sku_id', 'No SKU')}`)"
                        for index, deco in enumerate(data)
                    ]
                )
            )

        except Exception as error:
            await ctx.send(
                f"An error occurred while fetching decorations:\n`{str(error)}`"
            )

    @commands.command(name="setdeco")
    async def set_deco(self, ctx, deco_id: int, deco_sku_id: int) -> None:
        """
        Set a new decoration on the account using decoration ID and SKU.
        """
        try:
            session = curl_cffi.requests.Session(impersonate="chrome")
            headers = requestcord.HeaderGenerator().generate_headers(
                token=token
            )

            response = session.patch(
                "https://discord.com/api/v9/users/@me",
                headers=headers,
                json={
                    "avatar_decoration_id": deco_id,
                    "avatar_decoration_sku_id": deco_sku_id
                }
            )

            if response.ok:
                await ctx.send(
                    f"```Successfully changed decoration to {deco_id} (SKU: {deco_sku_id})```"
                )
            else:
                await ctx.send(
                    f"```Failed to change decoration. Status code: {response.status_code}```"
                )

        except Exception as error:
            await ctx.send(
                f"```An error occurred while setting decoration: {str(error)}```"
            )
def setup(bot):
    bot.add_cog(Decoration(bot))
import discord
import aiohttp
import random
from discord.ext import commands

lwmessages = [
    "LOL FAILED LAST Word",
    "last word for apophis",
    "nice failed last word, last word for me",
    "nigga failed a last word LOL"
]

class ALWCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.alw_enabled = False
        self.uid = None
        self.whitelist = self.load_whitelist()

    def load_whitelist(self):
        try:
            with open('wl.txt', 'r') as f:
                return {line.strip() for line in f if line.strip()}
        except FileNotFoundError:
            return set()

    def save_whitelist(self):
        with open('wl.txt', 'w') as f:
            f.writelines(f"{uid}\n" for uid in self.whitelist)

    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.bot.http.token}",
            "Content-Type": "application/json"
        }

    async def leave_gc(self, channel_id):
        """Leave the group chat with the given channel ID."""
        url = f"https://discord.com/api/v9/channels/{channel_id}"
        headers = self.get_headers()
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=headers) as response:
                if response.status == 204:
                    print(f"Left group channel {channel_id} successfully")
                else:
                    print(f"Failed to leave group channel {channel_id}: {response.status} - {await response.text()}")

    async def get_blocked(self, user_id):
        """Block the user with the given user ID."""
        async with aiohttp.ClientSession() as session:
            url = f"https://discord.com/api/v9/users/@me/relationships/{user_id}"
            headers = {
                "Authorization": self.bot.http.token,
                "Content-Type": "application/json",
                "Accept": "*/*",
            }
            async with session.put(url, headers=headers, json={"type": 2}) as response:
                if response.status == 204:
                    print(f"Blocked user {user_id}")
                else:
                    print(f"Failed to block {user_id}: {response.status} - {await response.text()}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.alw_enabled or message.author.id == self.bot.user.id:
            return

        if message.author.id != int(self.uid):
            if str(message.author.id) in self.whitelist:
                return

            random_message = random.choice(lwmessages)
            if isinstance(message.channel, discord.DMChannel):
                if any(term in message.content.lower() for term in ["last word", "lastword", "last", "lw", "lst", "lst word"]):
                    await message.reply(random_message)
                    await self.get_blocked(message.author.id)

            elif isinstance(message.channel, discord.GroupChannel):
                if any(term in message.content.lower() for term in ["last word", "lastword", "last", "lw"]):
                    await message.reply(random_message)
                    await self.get_blocked(message.author.id)
                    await self.leave_gc(message.channel.id)

    @commands.command()
    async def wl(self, ctx, user_id: int):
        """Add a user ID to the whitelist."""
        self.whitelist.add(str(user_id))
        self.save_whitelist()
        await ctx.send(f"User ID {user_id} has been added to the whitelist.")

    @commands.command()
    async def toggle_alw(self, ctx, user_id: int = None):
        """Toggle ALW feature and set optional user ID."""
        self.alw_enabled = not self.alw_enabled
        if user_id:
            self.uid = str(user_id)
        await ctx.send(f"ALW is now {'enabled' if self.alw_enabled else 'disabled'}. User ID set to {self.uid if self.uid else 'None'}.")

async def setup(bot):
    await bot.add_cog(ALWCog(bot))
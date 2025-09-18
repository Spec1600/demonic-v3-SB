import asyncio
import time
from pypresence import Presence
from discord.ext import commands
import random

class RPC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rpc_client = None
        self.running = False

        self.large_images = [
            "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExdXpnazR5aTY5OTNudTRiMzVlOW90d3Y0OTc3NGJqdDB4Y3FsbG5pZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/njH4f6IJ38WnB1L17F/giphy.gif",
            "https://64.media.tumblr.com/ec70eea87ed8a0a2759852cb6971b71e/tumblr_pfuiepJxOU1x6akhpo1_r2_500.gif",
            "https://i.pinimg.com/originals/bf/34/3e/bf343eda8b9c39b757b551000b0356b9.gif",
            "https://i.pinimg.com/originals/8c/aa/a2/8caaa2c787c05f0a6ff31043a619124f.gif",
        ]

        self.details_texts = [
            "Above and beyond all of you",
            "A true demon",
            "Sipping on your blood",
            "Ripping everyone apart",
            "Eternal God",
            "Monster",
            "A real menace",
            "A menace",
            "Above everyone",
        ]

    @commands.command()
    async def rpc(self, ctx):
        """Start the Rich Presence (by yale/yamo)"""
        if self.running:
            await ctx.send("```rpc is already running```")
            return

        self.rpc_client = Presence("1357991058352509049")
        self.running = True

        await ctx.send("```starting ur rpc```")
        await asyncio.to_thread(self.rpc_client.connect)
        await ctx.send("```rpc started```")

        start_time = int(time.time())

        async def cycle():
            while self.running:
                large_image = random.choice(self.large_images)
                details_text = random.choice(self.details_texts)

                presence = {
                    "state": "Above and beyond all of you",
                    "details": details_text,
                    "start": start_time,
                    "large_image": large_image,
                    "large_text": "ur god",
                    "small_image": "demonic",
                    "small_text": "Demonic",
                    "party_id": "demonic-v3",
                    "party_size": [1, 1],
                    "buttons": [
                        {
                            "label": "YouTube",
                            "url": "https://www.youtube.com/@zardexq",
                        },
                        {
                            "label": "Server",
                            "url": "https://discord.gg/Jykge2Ge",
                        },
                    ],
                }

                await asyncio.to_thread(self.rpc_client.update, **presence)
                await asyncio.sleep(3)

        self.bot.loop.create_task(cycle())

    @commands.command()
    async def rpcend(self, ctx):
        """Stop the Rich Presence"""
        if self.rpc_client and self.running:
            await ctx.send("```Stopping ur rpc```")
            self.running = False
            self.rpc_client.close()
            self.rpc_client = None
            await ctx.send("```rpc stopped```")
        else:
            await ctx.send("```rpc isnt running```")




# Setup function to add the cog to the bot
def setup(bot):
    bot.add_cog(RPC(bot))

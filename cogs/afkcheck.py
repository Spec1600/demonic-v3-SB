import discord
from discord.ext import commands
import json
import asyncio
import random
import time
from tls_client import Session

class AFKCheck(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.afkcheck_tasks = {}

    @commands.command()
    async def afkcheck(self, ctx: commands.Context, user: discord.User, count: int):
        """
        AFK checks a user by pinging them and counting up until reaching specified number.
        Stops if user responds with trigger words or count is reached.
        """
        if not (10 <= count <= 1000):
            await ctx.send("```Please provide a count between 10 and 1000```")
            return

        task_key = (user.id, ctx.channel.id)

        if task_key in self.afkcheck_tasks:
            await self._cancel_task(task_key)

        await self._start_afk_check(ctx, user, count, task_key)

    async def _cancel_task(self, task_key: tuple):
        """
        Cancels the running AFK check task for the given user and channel.
        """
        task = self.afkcheck_tasks.pop(task_key, None)
        if task:
            task.cancel()

    async def _start_afk_check(self, ctx: commands.Context, user: discord.User, count: int, task_key: tuple):
        """
        Starts the AFK check process, including response waiting and counter.
        """
        current_count = 1
        running = True

        async def check_response():
            """
            Waits for the user's response to stop the check.
            """
            nonlocal running

            def check(m):
                return m.author.id == user.id and any(trigger in m.content.lower() for trigger in ['here', 'im here', 'here.'])

            try:
                await self.bot.wait_for('message', check=check, timeout=None)
                running = False
                await ctx.send(f"> **stop running outta chat fucktard** {user.mention} ```dirty ass prostitute```")
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                print(f"Error in response checker: {e}")

        async def counter():
            """
            Counts up to the specified limit and pings the user.
            """
            nonlocal current_count, running

            while running and current_count <= count:
                try:
                    await asyncio.sleep(random.uniform(0.5, 0.75))
                    await ctx.send(f"> **afk check** {user.mention} ```{current_count}```")
                    current_count += 1

                    if current_count > count:
                        running = False
                        await ctx.send(f"> **{user.mention} is a fucking loser** ```bitchboy folded to a menance what a low tier```")
                except Exception as e:
                    print(f"Error in counter: {e}")
                    await asyncio.sleep(1)

        response_task = self.bot.loop.create_task(check_response())
        counter_task = self.bot.loop.create_task(counter())

        self.afkcheck_tasks[task_key] = asyncio.gather(response_task, counter_task)
        
        
    @commands.command(description="Hides a ping in a message using an exploit")
    async def hiddenping(
        self,
        ctx,
        user_id: int,
        *,
        message: str
    ):
        await ctx.message.delete()

        hidden_ping = (
            f"{message}||​||" + "||​||" * 300 + f"<@{user_id}>"
        )

        await ctx.channel.send(hidden_ping)
        
def setup(bot):
    bot.add_cog(AFKCheck(bot))
import discord
from discord.ext import commands
import json
import os

class CustomMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.messages_file = "custom_messages.json"
        self.load_messages()

    def load_messages(self):
        try:
            with open(self.messages_file, 'r') as f:
                self.messages = json.load(f)
        except FileNotFoundError:
            self.messages = {
                "kill": [],
                "autoreplies": [],
                "autoreplies_multi": [],
                "outlast_messages": [],
                "protection_messages": []
            }
            self.save_messages()

    def save_messages(self):
        with open(self.messages_file, 'w') as f:
            json.dump(self.messages, f, indent=4)

    @commands.group(invoke_without_command=True)
    async def messages(self, ctx):
        embed = discord.Embed(title="Message Customization", color=discord.Color.blue())
        embed.add_field(name="Available Categories", value="""
        • kill
        • autoreplies
        • autoreplies_multi
        • outlast
        • protection
        """, inline=False)
        embed.add_field(name="Commands", value="""
        • `.messages add <category> <message>` - Add a message
        • `.messages remove <category> <index>` - Remove a message
        • `.messages list <category>` - List messages
        • `.messages clear <category>` - Clear all messages
        """, inline=False)
        await ctx.send(embed=embed)

    @messages.command()
    async def add(self, ctx, category: str, *, message: str):
        category = category.lower()
        if category not in self.messages:
            await ctx.send("Invalid category. Use: kill, autoreplies, autoreplies_multi, outlast, protection")
            return

        self.messages[category].append(message)
        self.save_messages()
        await ctx.send(f"Added message to {category} category.")

    @messages.command()
    async def remove(self, ctx, category: str, index: int):
        category = category.lower()
        if category not in self.messages:
            await ctx.send("Invalid category.")
            return

        try:
            self.messages[category].pop(index)
            self.save_messages()
            await ctx.send(f"Removed message at index {index} from {category}.")
        except IndexError:
            await ctx.send("Invalid index.")

    @messages.command()
    async def list(self, ctx, category: str):
        category = category.lower()
        if category not in self.messages:
            await ctx.send("Invalid category.")
            return

        messages = self.messages[category]
        if not messages:
            await ctx.send(f"No custom messages in {category}.")
            return

        embed = discord.Embed(title=f"{category.title()} Messages", color=discord.Color.blue())
        
        chunks = []
        current_chunk = ""
        
        for i, msg in enumerate(messages):
            message_entry = f"{i}. {msg}\n"
            if len(current_chunk) + len(message_entry) > 1024:
                chunks.append(current_chunk)
                current_chunk = message_entry
            else:
                current_chunk += message_entry
        
        if current_chunk:
            chunks.append(current_chunk)
        
        for i, chunk in enumerate(chunks):
            embed.add_field(name=f"Messages {i+1}", value=chunk, inline=False)
        
        await ctx.send(embed=embed)

    @messages.command()
    async def clear(self, ctx, category: str):
        category = category.lower()
        if category not in self.messages:
            await ctx.send("Invalid category.")
            return

        self.messages[category] = []
        self.save_messages()
        await ctx.send(f"Cleared all messages from {category}.")

    def get_messages(self, category):
        return self.messages.get(category, [])

def setup(bot):
    bot.add_cog(CustomMessages(bot))

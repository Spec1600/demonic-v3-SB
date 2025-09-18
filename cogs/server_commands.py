from discord.ext import commands
from .server_restore import pasteserver
import discord
import asyncio
import re

class ServerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def pasteserver(self, ctx):
        await pasteserver(ctx, self.bot)
        
    @commands.command()
    async def hideall(self, ctx):
        try:
            guild = ctx.guild
            everyone_role = guild.default_role
            hidden_count = 0
            
            status_msg = await ctx.send("```Hiding all channels and categories...```")
            
            deny_view = discord.PermissionOverwrite(view_channel=False)
            
            for category in guild.categories:
                try:
                    await category.set_permissions(everyone_role, overwrite=deny_view)
                    hidden_count += 1
                    await asyncio.sleep(1) 
                except discord.Forbidden:
                    await ctx.send(f"```Cannot hide category {category.name} - Missing permissions```")
                except Exception as e:
                    await ctx.send(f"```Error hiding category {category.name}: {str(e)}```")
            
            for channel in guild.channels:
                try:
                    await channel.set_permissions(everyone_role, overwrite=deny_view)
                    hidden_count += 1
                    await asyncio.sleep(1)  
                except discord.Forbidden:
                    await ctx.send(f"```Cannot hide channel {channel.name} - Missing permissions```")
                except Exception as e:
                    await ctx.send(f"```Error hiding channel {channel.name}: {str(e)}```")
            
            await status_msg.edit(content=f"```Successfully hidden {hidden_count} channels/categories from @everyone```")
            
        except Exception as e:
            await ctx.send(f"```An error occurred: {str(e)}```")
        
    @commands.command()
    async def movebotroles(self, ctx):
        try:
            guild = ctx.guild
            
            bot_identifiers = [
                'bot', 'music', 'mee6', 'dyno', 'mudae', 'rythm', 'groovy', 
                'carl', 'ticket', 'verify', 'auto', 'mod', 'discord', 'tracker',
                'statbot', 'maki', 'cart-bot', 'fmbot', 'owo', 'invite',
                'marriage', 'verification', 'arcane', 'jockie', 'vanity'
            ]
            
            all_roles = sorted([r for r in guild.roles if not r.is_default()], 
                             key=lambda r: r.position, 
                             reverse=True)
            
            def is_bot_role(role):
                name_lower = role.name.lower()
                return (any(identifier in name_lower for identifier in bot_identifiers) or
                       any(m.bot for m in role.members))
            
            bot_roles = []
            non_bot_roles = []
            
            for role in all_roles:
                if is_bot_role(role):
                    bot_roles.append(role)
                else:
                    non_bot_roles.append(role)
            
            if not bot_roles:
                await ctx.send("```No bot roles found to move```")
                return
            
            moved_roles = []
            await ctx.send("```Moving roles... This may take a moment.```")
            
            start_position = 1
            
            for role in reversed(bot_roles):
                try:
                    await role.edit(position=start_position)
                    moved_roles.append(role.name)
                    await asyncio.sleep(1)
                    start_position += 1
                except discord.Forbidden:
                    await ctx.send(f"```Cannot move role {role.name} - Missing permissions```")
                except discord.HTTPException as e:
                    await ctx.send(f"```Error moving role {role.name}: {str(e)}```")
                    continue
            
            if moved_roles:
                roles_list = "\n".join(moved_roles)
                await ctx.send(f"```Successfully moved the following bot roles to the bottom:\n{roles_list}```")
            else:
                await ctx.send("```No roles were moved due to errors```")
            
        except Exception as e:
            await ctx.send(f"```An error occurred: {str(e)}```")

def setup(bot):
    bot.add_cog(ServerCommands(bot))

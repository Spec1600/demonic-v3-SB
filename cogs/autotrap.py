import discord
from discord.ext import commands
import aiohttp
import asyncio

class AutoTrap(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.noleave_users = {}
        self.monitor_tasks = {}

    async def monitor_group_chats(self, ctx, group_chat_id):
        await self.bot.wait_until_ready()

        headers = {
            'Authorization': f'{self.bot.http.token}',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        while not self.bot.is_closed():
            try:
                if group_chat_id in self.noleave_users and self.noleave_users[group_chat_id]:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f'https://discord.com/api/v9/channels/{group_chat_id}', headers=headers) as resp:
                            if resp.status == 200:
                                group_data = await resp.json()
                                current_member_ids = {int(recip['id']) for recip in group_data.get('recipients', [])}
                                
                                for member in list(self.noleave_users[group_chat_id]):
                                    if member.id not in current_member_ids:
                                        try:
                                            if member.id == ctx.author.id:
                                                continue
                                                
                                            print(f"Attempting to re-add {member.username} (ID: {member.id}) to group {group_chat_id}")
                                            
                                            add_url = f'https://discord.com/api/v9/channels/{group_chat_id}/recipients/{member.id}'
                                            async with session.put(add_url, headers=headers, json={}) as add_resp:
                                                response_text = await add_resp.text()
                                                print(f"Add response status: {add_resp.status}, Response: {response_text}")
                                                
                                                if add_resp.status == 204:
                                                    print(f"Successfully re-added {member.username} to group chat")
                                                elif add_resp.status == 429:
                                                    retry_after = int(add_resp.headers.get('Retry-After', 1))
                                                    print(f"Rate limited, waiting {retry_after} seconds")
                                                    await asyncio.sleep(retry_after)
                                                else:
                                                    print(f"Failed to add {member.username}. Status: {add_resp.status}")
                                                    
                                        except Exception as e:
                                            print(f"Error adding user {member.username}: {str(e)}")
                            else:
                                print(f"Failed to get group data. Status: {resp.status}")
                                
            except Exception as e:
                print(f"Error in monitor_group_chats: {str(e)}")
                
            await asyncio.sleep(1)  

    class SimpleUser:
        def __init__(self, data):
            self.id = int(data['id'])
            self.username = data['username']
            self.discriminator = data.get('discriminator', '0')

    @commands.command(name="autotrap")
    async def autotrap(self, ctx, action: str, user_input: str = None):
        group_chat_id = ctx.channel.id

        if group_chat_id not in self.noleave_users:
            self.noleave_users[group_chat_id] = set()

        if action == "toggle":
            if user_input:
                user_id = user_input.strip()
                if user_id.startswith('<@') and user_id.endswith('>'):
                    user_id = ''.join(filter(str.isdigit, user_id))
                elif user_id.startswith('<@!') and user_id.endswith('>'):
                    user_id = ''.join(filter(str.isdigit, user_id))

                try:
                    user_id = int(user_id)
                    
                    member_obj = None
                    
                    member = ctx.guild.get_member(user_id) if ctx.guild else None
                    if member:
                        member_obj = self.SimpleUser({
                            'id': str(member.id),
                            'username': member.name,
                            'discriminator': member.discriminator
                        })
                    
                    if not member_obj:
                        try:
                            user = await self.bot.fetch_user(user_id)
                            member_obj = self.SimpleUser({
                                'id': str(user.id),
                                'username': user.name,
                                'discriminator': user.discriminator
                            })
                        except discord.NotFound:
                            pass
                        except discord.HTTPException:
                            pass
                    
                    if not member_obj:
                        for guild in self.bot.guilds:
                            member = guild.get_member(user_id)
                            if member:
                                member_obj = self.SimpleUser({
                                    'id': str(member.id),
                                    'username': member.name,
                                    'discriminator': member.discriminator
                                })
                                break
                    
                    if member_obj:
                        if member_obj.id in [u.id for u in self.noleave_users[group_chat_id]]:
                            self.noleave_users[group_chat_id] = {u for u in self.noleave_users[group_chat_id] if u.id != member_obj.id}
                            await ctx.send(f"```{member_obj.username} is now allowed to leave.```")
                        else:
                            self.noleave_users[group_chat_id].add(member_obj)
                            await ctx.send(f"```{member_obj.username} cannot leave this group chat.```")
                    else:
                        await ctx.send("```User not found. Make sure the user is in a mutual server with the bot.```")

                except ValueError:
                    await ctx.send("```Invalid user ID format. Please use a user ID or mention.```")
                except Exception as e:
                    await ctx.send(f"```Error: {str(e)}```")
                    import traceback
                    print(f"Error in autotrap: {traceback.format_exc()}")
            else:
                await ctx.send("```Please specify a user (mention or ID).```")

        elif action == "list":
            if self.noleave_users[group_chat_id]:
                user_list = ", ".join([f"<@{user.id}>" for user in self.noleave_users[group_chat_id]])
                await ctx.send(f"```Users prevented from leaving: \n{user_list}```")
            else:
                await ctx.send("```No users are prevented from leaving this group chat.```")

        elif action == "clear":
            self.noleave_users[group_chat_id].clear()
            await ctx.send("```All users are now allowed to leave this group chat.```")
        else:
            await ctx.send("```Invalid action. Use `toggle`, `list`, or `clear`.```")

        if group_chat_id not in self.monitor_tasks:
            self.monitor_tasks[group_chat_id] = self.bot.loop.create_task(self.monitor_group_chats(ctx, group_chat_id))

    @commands.command(name="autotrap_debug")
    async def autotrap_debug(self, ctx):
        group_chat_id = ctx.channel.id
        
        if group_chat_id not in self.noleave_users:
            await ctx.send("```No autotrap data for this chat```")
            return
            
        users = self.noleave_users[group_chat_id]
        if not users:
            await ctx.send("```No users are being monitored in this chat```")
            return
            
        user_list = "\n".join([f"- {user.username} (ID: {user.id})" for user in users])
        monitor_task = "Running" if group_chat_id in self.monitor_tasks else "Not running"
        
        debug_info = f"""```
Autotrap Debug Info:
Chat ID: {group_chat_id}
Monitor Task: {monitor_task}
Monitored Users:
{user_list}
```"""
        await ctx.send(debug_info)

def setup(bot):
    bot.add_cog(AutoTrap(bot))

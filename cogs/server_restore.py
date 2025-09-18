import discord
from discord.ext import commands
import json
import os
import asyncio
import aiohttp


from discord.ext import commands

class ServerRestore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

default_colors = {
    "text": "\u001b[0;37m",  
    "highlight": "\u001b[1;37m",  
    "accent": "\u001b[0;36m",  
}
@commands.command()
async def pasteserver(ctx, bot):
    try:
        text_color = default_colors["text"]
        highlight_color = default_colors["highlight"]
        accent_color = default_colors["accent"]
        white = "\u001b[0;37m"
        blue = "\u001b[0;34m"

        guild = ctx.guild
        any_text_channel = None

        try:
            backup_files = [f for f in os.listdir() if f.endswith("_backup.json")]
        except Exception as e:
            await ctx.send(f"```Error reading backup files: {str(e)}```")
            return

        await ctx.send("```Attempting to restore server.```")

        if not backup_files:
            await ctx.send("```No backup file found. Please run `.restoreserver` first.```")
            return

        backup_file = None
        if len(backup_files) > 1:
            try:
                backup_file_list = "\n".join([f"{i + 1}: {file}" for i, file in enumerate(backup_files)])
                await ctx.send(f"```Multiple backup files found:\n{backup_file_list}\nPlease select a file by typing the number.```")
                
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit() and 1 <= int(m.content) <= len(backup_files)
                
                try:
                    msg = await bot.wait_for('message', timeout=30.0, check=check)
                    selected_index = int(msg.content) - 1
                    backup_file = backup_files[selected_index]
                except Exception:
                    await ctx.send("```No valid selection made. Aborting the restore operation.```")
                    return
            except Exception as e:
                await ctx.send(f"```Error during file selection: {str(e)}```")
                return
        else:
            backup_file = backup_files[0]

        try:
            with open(backup_file, "r") as f:
                server_data = json.load(f)
        except json.JSONDecodeError:
            await ctx.send("```Backup file is empty or invalid JSON. Please create a valid backup first.```")
            return
        except Exception as e:
            await ctx.send(f"```Error reading backup file: {str(e)}```")
            return

        for role in guild.roles:
            if role.name != "@everyone":
                try:
                    await role.delete()
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"Failed to delete role {role.name}: {e}")
                    continue

        for channel in guild.channels:
            try:
                await channel.delete()
                await asyncio.sleep(1)
            except Exception:
                continue

        try:
            if server_data.get("name"):
                await guild.edit(name=server_data["name"])
            if server_data.get("icon_url"):
                async with aiohttp.ClientSession() as session:
                    async with session.get(server_data["icon_url"]) as resp:
                        if resp.status == 200:
                            icon_bytes = await resp.read()
                            await guild.edit(icon=icon_bytes)
        except Exception as e:
            print(f"Failed to update server name/icon: {e}")

        role_map = {}
        sorted_roles = sorted(
            server_data.get("roles", {}).items(),
            key=lambda x: x[1].get("position", 0),
            reverse=True
        )

        for role_id, role_data in sorted_roles:
            try:
                role = await guild.create_role(
                    name=role_data["name"],
                    permissions=discord.Permissions(role_data["permissions"]),
                    color=discord.Color(role_data["color"]),
                    hoist=role_data["hoist"],
                    mentionable=role_data["mentionable"]
                )
                role_map[role_id] = role
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Failed to create role {role_data['name']}: {e}")
                continue

        for category_data in server_data.get("categories", []):
            try:
                overwrites = {}
                for perm in category_data.get("permissions", []):
                    try:
                        target_id = perm["id"]
                        target = role_map.get(target_id) or guild.get_member(int(target_id))
                        if target:
                            overwrites[target] = discord.PermissionOverwrite.from_pair(
                                discord.Permissions(perm["allow"]),
                                discord.Permissions(perm["deny"])
                            )
                    except Exception:
                        continue

                await guild.create_category(
                    name=category_data["name"],
                    overwrites=overwrites,
                    position=category_data.get("position", 0)
                )
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Failed to create category {category_data['name']}: {e}")
                continue


        for channel_data in server_data.get("channels", []):
            try:
                category = discord.utils.get(guild.categories, name=channel_data.get("category"))
                
                overwrites = {}
                for perm in channel_data.get("permissions", []):
                    try:
                        target_id = perm["id"]
                        target = role_map.get(target_id) or guild.get_member(int(target_id))
                        if target:
                            overwrites[target] = discord.PermissionOverwrite.from_pair(
                                discord.Permissions(perm["allow"]),
                                discord.Permissions(perm["deny"])
                            )
                    except Exception:
                        continue

                channel_settings = {
                    "name": channel_data["name"],
                    "overwrites": overwrites,
                    "category": category,
                    "position": channel_data.get("position", 0),
                    "topic": channel_data.get("topic"),
                    "nsfw": channel_data.get("nsfw", False),
                    "slowmode_delay": channel_data.get("slowmode_delay", 0)
                }

                await guild.create_text_channel(**channel_settings)
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Failed to create text channel {channel_data['name']}: {e}")
                continue

        for channel_data in server_data.get("voice_channels", []):
            try:
                category = discord.utils.get(guild.categories, name=channel_data.get("category"))
                
                overwrites = {}
                for perm in channel_data.get("permissions", []):
                    try:
                        target_id = perm["id"]
                        target = role_map.get(target_id) or guild.get_member(int(target_id))
                        if target:
                            overwrites[target] = discord.PermissionOverwrite.from_pair(
                                discord.Permissions(perm["allow"]),
                                discord.Permissions(perm["deny"])
                            )
                    except Exception:
                        continue

                channel_settings = {
                    "name": channel_data["name"],
                    "overwrites": overwrites,
                    "category": category,
                    "position": channel_data.get("position", 0),
                    "bitrate": channel_data.get("bitrate", 64000),
                    "user_limit": channel_data.get("user_limit", 0)
                }

                await guild.create_voice_channel(**channel_settings)
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Failed to create voice channel {channel_data['name']}: {e}")
                continue

        restored_role_count = len(server_data.get("roles", []))
        restored_channel_count = len(server_data.get("channels", []))
        restored_category_count = len(server_data.get("categories", []))
        restored_voice_channel_count = len(server_data.get("voice_channels", []))

        if any_text_channel is None:
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    any_text_channel = channel
                    break

        if any_text_channel is not None:
            try:
                await any_text_channel.send(f"""```ansi
                {blue}───────────────────────────────────────────────────────────────────────────────────────────────────────────── 
                                                            {highlight_color}RESTORE COMPLETE
                                            
                                            {text_color}Server configuration has been {white}restored
                                            {text_color}Roles restored: {white}{restored_role_count}
                                            {text_color}Channels restored: {white}{restored_channel_count}
                                            {text_color}Categories restored: {white}{restored_category_count} 
                                            {text_color}Voice Channels restored: {white}{restored_voice_channel_count}.

                {blue}───────────────────────────────────────────────────────────────────────────────────────────────────────────── 
```""")
            except Exception as e:
                print(f"Failed to send completion message: {e}")
                
    except Exception as e:
        await ctx.send(f"```An unexpected error occurred: {str(e)}```")
        

def setup(bot):
    bot.add_cog(ServerRestore(bot))

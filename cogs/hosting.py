import discord
from discord.ext import commands
import json
import os
import shutil
import subprocess
from datetime import datetime
import aiohttp
import asyncio

class Hosting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_hosts_file = "active_hosts.json"
        self.history_file = "hosting_history.json"
        self.processes = {}
        self.load_active_hosts()
        self.load_history()

    def load_active_hosts(self):
        try:
            with open(self.active_hosts_file, 'r') as f:
                self.active_hosts = json.load(f)
        except FileNotFoundError:
            self.active_hosts = {}
            self.save_active_hosts()

    def save_active_hosts(self):
        with open(self.active_hosts_file, 'w') as f:
            json.dump(self.active_hosts, f, indent=4)

    def load_history(self):
        try:
            with open(self.history_file, 'r') as f:
                self.hosting_data = json.load(f)
        except FileNotFoundError:
            self.hosting_data = {"history": []}
            self.save_history()

    def save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.hosting_data, f, indent=4)

    async def get_username_from_token(self, token):
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json'
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('https://discord.com/api/v9/users/@me', headers=headers) as resp:
                    if resp.status == 200:
                        user_data = await resp.json()
                        return user_data.get('username')
                    else:
                        return None
            except Exception:
                return None

    @commands.command()
    async def host(self, ctx, host_type: str, new_folder: str, token: str):
        try:
            await ctx.message.delete()
            current_dir = os.getcwd()
            
            username = await self.get_username_from_token(token)
            if not username:
                await ctx.send("```Invalid token or could not fetch username```", delete_after=3)
                return
            
            # Create new directory for the user
            new_host_path = os.path.join(current_dir, f"hosts/{new_folder}")
            os.makedirs(new_host_path, exist_ok=True)
            
            # Create config.json in the new directory
            config = {"token": token}
            config_path = os.path.join(new_host_path, "config.json")
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            # Check if ProjectB.py exists in the current directory
            projectb_path = os.path.join(current_dir, "main.py")
            if not os.path.exists(projectb_path):
                await ctx.send("```Error: main.py not found in the bot's directory```", delete_after=3)
                return
            
            # Copy ProjectB.py to the new directory
            shutil.copy(projectb_path, new_host_path)
            
            # Create a log file for output
            log_file = os.path.join(new_host_path, "process.log")
            
            # Start the process
            os.chdir(new_host_path)
            with open(log_file, 'w') as log:
                process = subprocess.Popen(
                    ["python", "main.py"],
                    cwd=new_host_path,
                    stdout=log,
                    stderr=log,
                    text=True
                )
            os.chdir(current_dir)
            
            # Check if process started successfully
            try:
                await asyncio.sleep(1)  # Give the process a moment to start
                if process.poll() is not None:
                    with open(log_file, 'r') as log:
                        error = log.read() or "Unknown error"
                    await ctx.send(f"```Error starting process: {error}```", delete_after=10)
                    return
            except Exception as e:
                await ctx.send(f"```Error checking process: {str(e)}```", delete_after=3)
                return
            
            self.processes[username] = {
                "process": process,
                "path": new_host_path,
                "status": "running"
            }
            
            timestamp = datetime.now().isoformat()
            self.active_hosts[username] = {
                "started_at": timestamp,
                "host_type": host_type,
                "path": new_host_path,
                "status": "running"
            }
            self.save_active_hosts()
            
            self.hosting_data["history"].append({
                "username": username,
                "action": "started",
                "timestamp": timestamp,
                "host_type": host_type
            })
            self.save_history()
            
            await ctx.send(f"```Successfully started host for {username} in {new_folder}```")
            
        except Exception as e:
            await ctx.send(f"```Error: {str(e)}```", delete_after=3)

    @commands.command()
    async def stop(self, ctx, username: str):
        try:
            if username in self.processes:
                process_info = self.processes[username]
                if process_info["status"] == "running":
                    process_info["process"].terminate()
                    process_info["status"] = "stopped"
                    
                    timestamp = datetime.now().isoformat()
                    self.hosting_data["history"].append({
                        "username": username,
                        "action": "stopped",
                        "timestamp": timestamp
                    })
                    
                    if username in self.active_hosts:
                        del self.active_hosts[username]
                        self.save_active_hosts()
                    
                    self.save_history()
                    await ctx.send(f"```Stopped host for {username}```")
                else:
                    await ctx.send(f"```Host for {username} is already stopped```")
            else:
                await ctx.send(f"```No active host found for {username}```")
        except Exception as e:
            await ctx.send(f"```Error: {str(e)}```", delete_after=3)

    @commands.command()
    async def pause(self, ctx, username: str):
        try:
            if username in self.processes:
                process_info = self.processes[username]
                if process_info["status"] == "running":
                    import psutil
                    process = psutil.Process(process_info["process"].pid)
                    process.suspend()
                    process_info["status"] = "paused"
                    
                    if username in self.active_hosts:
                        self.active_hosts[username]["status"] = "paused"
                        self.save_active_hosts()
                    
                    timestamp = datetime.now().isoformat()
                    self.hosting_data["history"].append({
                        "username": username,
                        "action": "paused",
                        "timestamp": timestamp
                    })
                    self.save_history()
                    
                    await ctx.send(f"```Paused host for {username}```")
                else:
                    await ctx.send(f"```Host for {username} is not running```")
            else:
                await ctx.send(f"```No active host found for {username}```")
        except Exception as e:
            await ctx.send(f"```Error: {str(e)}```", delete_after=3)

    @commands.command()
    async def resume(self, ctx, username: str):
        try:
            if username in self.processes:
                process_info = self.processes[username]
                if process_info["status"] == "paused":
                    import psutil
                    process = psutil.Process(process_info["process"].pid)
                    process.resume()
                    process_info["status"] = "running"
                    
                    if username in self.active_hosts:
                        self.active_hosts[username]["status"] = "running"
                        self.save_active_hosts()
                    
                    timestamp = datetime.now().isoformat()
                    self.hosting_data["history"].append({
                        "username": username,
                        "action": "resumed",
                        "timestamp": timestamp
                    })
                    self.save_history()
                    
                    await ctx.send(f"```Resumed host for {username}```")
                else:
                    await ctx.send(f"```Host for {username} is not paused```")
            else:
                await ctx.send(f"```No active host found for {username}```")
        except Exception as e:
            await ctx.send(f"```Error: {str(e)}```", delete_after=3)

    @commands.command(name="hosts")
    async def list_hosts(self, ctx):
        try:
            if not self.active_hosts:
                await ctx.send("```No active hosts```")
                return

            message = "```\n=== Active Hosts ===\n"
            for username, data in self.active_hosts.items():
                status = data.get('status', 'running')
                started = data.get('started_at', 'Unknown')
                message += f"• {username} (Started: {started}) - {status}\n"
            message += "```"
            await ctx.send(message)
            
        except Exception as e:
            await ctx.send(f"```Error: {str(e)}```", delete_after=3)

    @commands.command(name="hosting_history")
    async def show_history(self, ctx, page: int = 1):
        try:
            entries_per_page = 10
            history = self.hosting_data["history"]
            
            if not history:
                await ctx.send("```No hosting history available```")
                return
                
            total_pages = (len(history) + entries_per_page - 1) // entries_per_page
            page = min(max(1, page), total_pages)
            
            start_idx = (page - 1) * entries_per_page
            end_idx = start_idx + entries_per_page
            
            message = f"```\n=== Hosting History (Page {page}/{total_pages}) ===\n"
            for entry in reversed(history[start_idx:end_idx]):
                message += f"• {entry['username']} - {entry['action']} at {entry['timestamp']}\n"
            message += "```"
            
            await ctx.send(message)
            
        except Exception as e:
            await ctx.send(f"```Error: {str(e)}```", delete_after=3)

def setup(bot):
    bot.add_cog(Hosting(bot))
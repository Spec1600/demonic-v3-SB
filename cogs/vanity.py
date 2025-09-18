import discord
from discord.ext import commands
import aiohttp
import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
black = "\033[30m"
red = "\033[31m"
green = "\033[32m"
yellow = "\033[33m"
blue = "\033[34m"
magenta = "\033[35m"
cyan = "\033[36m"
white = "\033[37m"
reset = "\033[0m"  
pink = "\033[38;2;255;192;203m"
white = "\033[37m"
blue = "\033[34m"
black = "\033[30m"
light_green = "\033[92m" 
light_yellow = "\033[93m" 
light_magenta = "\033[95m" 
light_cyan = "\033[96m"  
light_red = "\033[91m"  
light_blue = "\033[94m"  

class VanitySniperCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'data/vanity_config.json'
        self.load_config()
        self.sniping = False
        self.headers = {
            'Authorization': self.bot.http.token,
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.check_task = None
        self.main_config = self.load_main_config()
        self.last_check = datetime.now()
        self.backoff_time = 1.0  
        self.max_backoff = 30.0  

    def load_main_config(self):
        try:
            config_path = Path('config.json')
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading main config: {e}")
            return {}

    def load_config(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'target_vanity': None,
                'guild_id': None,
                'webhook_url': None,
                'check_delay': 1.0
            }
            self.save_config()

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    async def check_vanity(self, vanity):
        try:
            now = datetime.now()
            time_passed = (now - self.last_check).total_seconds()
            if time_passed < self.backoff_time:
                await asyncio.sleep(self.backoff_time - time_passed)

            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': self.bot.http.token,
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                
                async with session.get(
                    f'https://canary.discord.com/api/v9/invites/{vanity}',
                    headers=headers
                ) as resp:
                    self.last_check = datetime.now()
                    
                    if resp.status == 429:  
                        data = await resp.json()
                        retry_after = data.get('retry_after', 5)
                        print(f"Rate limited. Waiting {retry_after} seconds...")
                        
                        self.backoff_time = min(self.backoff_time * 2, self.max_backoff)
                        await asyncio.sleep(retry_after)
                        return False
                        
                    elif resp.status == 404:  
                        self.backoff_time = max(1.0, self.backoff_time / 2)  
                        return True
                        
                    elif resp.status == 200:  
                        self.backoff_time = max(1.0, self.backoff_time / 2)  
                        return False
                        
                    else:
                        print(f"Unexpected status checking vanity: {resp.status}")
                        return False
                        
        except Exception as e:
            print(f"Error checking vanity: {e}")
            return False

    async def submit_2fa(self, ticket, password):
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "ticket": ticket,
                    "password": password
                }
                
                async with session.post(
                    'https://canary.discord.com/api/v9/auth/mfa/ticket',
                    headers=self.headers,
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get('token')
                    else:
                        error = await resp.text()
                        print(f"2FA Error: {error}")
                        return None
        except Exception as e:
            print(f"2FA submission error: {e}")
            return None

    async def claim_vanity(self, guild_id, vanity):
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': self.bot.http.token,
                    'Content-Type': 'application/json',
                    'X-Audit-Log-Reason': 'Vanity URL Sniper'
                }
                
                payload = {
                    'code': vanity
                }
                
                async with session.patch(
                    f'https://canary.discord.com/api/v9/guilds/{guild_id}/vanity-url',
                    headers=headers,
                    json=payload
                ) as resp:
                    if resp.status in (200, 201):
                        return True
                    elif resp.status == 401:
                        error_data = await resp.json()
                        if error_data.get('code') == 60003:  
                            password = self.main_config.get('password')
                            if not password:
                                print("Password not found in config.json")
                                return False
                                
                            ticket = error_data['mfa']['ticket']
                            mfa_token = await self.submit_2fa(ticket, password)
                            
                            if mfa_token:
                                headers['Authorization'] = mfa_token
                                async with session.patch(
                                    f'https://canary.discord.com/api/v9/guilds/{guild_id}/vanity-url',
                                    headers=headers,
                                    json=payload
                                ) as mfa_resp:
                                    return mfa_resp.status in (200, 201)
                            else:
                                print("Failed to get MFA token")
                                return False
                    else:
                        error_text = await resp.text()
                        print(f"Failed to claim vanity. Status: {resp.status}, Error: {error_text}")
                        return False
        except Exception as e:
            print(f"Error claiming vanity: {e}")
            return False

    async def send_webhook(self, content):
        if not self.config['webhook_url']:
            return
            
        async with aiohttp.ClientSession() as session:
            await session.post(
                self.config['webhook_url'],
                json={
                    'content': content,
                    'username': 'Vanity Sniper',
                    'avatar_url': 'https://i.imgur.com/your_image.png'
                }
            )

    async def sniper_task(self):
        while self.sniping:
            try:
                is_available = await self.check_vanity(self.config['target_vanity'])
                
                if is_available:
                    print(f"Vanity {self.config['target_vanity']} is available! Attempting to claim...")
                    
                    if await self.claim_vanity(self.config['guild_id'], self.config['target_vanity']):
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        success_msg = f"🎯 **Vanity Sniped!**\n```\nVanity: {self.config['target_vanity']}\nGuild ID: {self.config['guild_id']}\nTimestamp: {timestamp}\n```"
                        await self.send_webhook(success_msg)
                        self.sniping = False
                        break
                    else:
                        print("Failed to claim vanity despite it being available")
                
                await asyncio.sleep(self.config['check_delay'])
                
            except Exception as e:
                print(f"Error in sniper task: {e}")
                await asyncio.sleep(self.config['check_delay'])

    @commands.group(invoke_without_command=True)
    async def vanity(self, ctx):
        await ctx.send(f"""```ansi
{magenta}Vanity Sniper Commands{reset}
{red}⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯{reset}
{white}.vanity set <vanity> <guild_id>    - Set target vanity and guild
.vanity webhook <url>             - Set webhook for notifications
.vanity delay <seconds>           - Set check delay (default: 1s)
.vanity start                     - Start sniping
.vanity stop                      - Stop sniping
.vanity status                    - Show current config{reset}```""")

    @vanity.command(name='set')
    async def set_vanity(self, ctx, vanity: str, guild_id: int):
        self.config['target_vanity'] = vanity.lower()
        self.config['guild_id'] = guild_id
        self.save_config()
        await ctx.send(f"""```ansi
{green}Success{reset}
{red}⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯{reset}
{white}Set target vanity to: {vanity}
For guild ID: {guild_id}{reset}```""")

    @vanity.command(name='webhook')
    async def set_webhook(self, ctx, url: str):
        self.config['webhook_url'] = url
        self.save_config()
        await ctx.send(f"""```ansi
{green}Success{reset}
{red}⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯{reset}
{white}Webhook URL has been set{reset}```""")

    @vanity.command(name='delay')
    async def set_delay(self, ctx, delay: float):
        if delay < 0.5:
            await ctx.send(f"""```ansi
{red}Error{reset}
{red}⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯{reset}
{white}Delay must be at least 0.5 seconds{reset}```""")
            return
            
        self.config['check_delay'] = delay
        self.save_config()
        await ctx.send(f"""```ansi
{green}Success{reset}
{red}⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯{reset}
{white}Check delay set to {delay} seconds{reset}```""")

    @vanity.command(name='start')
    async def start_sniper(self, ctx):
        if not all([self.config['target_vanity'], self.config['guild_id']]):
            await ctx.send(f"""```ansi
{red}Error{reset}
{red}⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯{reset}
{white}Please set vanity and guild ID first{reset}```""")
            return

        if self.sniping:
            await ctx.send(f"""```ansi
{red}Error{reset}
{red}⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯{reset}
{white}Sniper is already running{reset}```""")
            return

        self.sniping = True
        self.check_task = asyncio.create_task(self.sniper_task())
        await ctx.send(f"""```ansi
{green}Success{reset}
{red}⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯{reset}
{white}Vanity sniper started
Target: {self.config['target_vanity']}
Guild ID: {self.config['guild_id']}
Check Delay: {self.config['check_delay']}s{reset}```""")

    @vanity.command(name='stop')
    async def stop_sniper(self, ctx):
        if not self.sniping:
            await ctx.send(f"""```ansi
{red}Error{reset}
{red}⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯{reset}
{white}Sniper is not running{reset}```""")
            return

        self.sniping = False
        if self.check_task:
            self.check_task.cancel()
        await ctx.send(f"""```ansi
{green}Success{reset}
{red}⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯{reset}
{white}Vanity sniper stopped{reset}```""")

    @vanity.command(name='status')
    async def sniper_status(self, ctx):
        await ctx.send(f"""```ansi
{magenta}Vanity Sniper Status{reset}
{red}⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯{reset}
{white}Status: {'Running' if self.sniping else 'Stopped'}
Target Vanity: {self.config['target_vanity'] or 'Not Set'}
Guild ID: {self.config['guild_id'] or 'Not Set'}
Check Delay: {self.config['check_delay']}s
Webhook: {'Set' if self.config['webhook_url'] else 'Not Set'}{reset}```""")

def setup(bot):
    bot.add_cog(VanitySniperCog(bot))
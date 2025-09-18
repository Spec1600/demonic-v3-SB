import discord
from discord.ext import commands
import json
import asyncio
import random
import time
from tls_client import Session

class MarriageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def marry(self, ctx, partner: discord.User, partner_name: str, partner_gender: str):
        """Marry a user after they confirm with an affirmative response and store the info in config.json."""
        user = ctx.author

        # Prevent marrying yourself
        if partner.id == user.id:
            await ctx.send(f"{user.mention}, you can't marry yourself!")
            return

        valid_genders = ['male', 'female', 'other']
        if partner_gender.lower() not in valid_genders:
            await ctx.send(f"Invalid gender '{partner_gender}'. Please use 'male', 'female', or 'other'.")
            return

        # Define valid responses
        yes_responses = ['yes', 'yep', 'heck yeah', 'hell yeah', 'yepppie']
        no_responses = ['no', 'nope', 'hell no', 'heck no', 'fuck no', 'nigga no']

        # Send proposal message mentioning only "yes" or "no"
        proposal_message = await ctx.send(f"{partner.mention}, {user.mention} has proposed to you! 💍\n"
                                        f"Please respond with **yes** to accept or **no** to decline.")

        def check_response(m):
            return m.author.id == partner.id and m.channel.id == ctx.channel.id and m.content.lower() in yes_responses + no_responses

        try:
            # Wait for partner's response (timeout after 60 seconds)
            response = await self.bot.wait_for('message', check=check_response, timeout=60.0)
        except asyncio.TimeoutError:
            await proposal_message.edit(content=f"{partner.mention} did not respond in time. The proposal has been canceled.")
            return

        # Check if the response is a decline
        if response.content.lower() in no_responses:
            await ctx.send(f"{partner.mention} declined the proposal from {user.mention}. 😔")
            return

        # If the response is affirmative, proceed with marriage
        with open('marryconfig.json', 'r') as f:
            config = json.load(f)

        config['marriage'] = {
            'user': str(user.id),
            'partner': str(partner.id),
            'partner_name': partner_name,
            'partner_gender': partner_gender
        }

        with open('marryconfig.json', 'w') as f:
            json.dump(config, f, indent=4)

        gif_urls = [
            "https://tenor.com/view/casados-gif-20051399",
            "https://tenor.com/view/anime-wedding-marriage-wedlock-gif-10799171",
            "https://tenor.com/view/%D1%81%D0%B2%D0%B0%D0%B4%D1%8C%D0%B1%D0%B0-%D0%B0%D0%BD%D0%B8%D0%BC%D0%B5-gif-11590914524301350558",
            "https://tenor.com/view/anime-couple-gif-21171654",
            "https://tenor.com/view/anime-kiss-marry-me-gif-20818687",
            "https://tenor.com/view/umineko-shannon-propose-engagement-ring-anime-gif-7487871130289617126"
        ]

        marriage_gif = random.choice(gif_urls)

        marriage_message = (f"{user.mention} married {partner.mention}! 💍\n"
                           f"**Partner's Name:** {partner_name}\n"
                           f"**Partner's Gender:** {partner_gender}\n"
                           f"**Wedding:** [Your MARRIAGE]({marriage_gif})")
        await ctx.send(marriage_message)

    @commands.command()
    async def divorce(self, ctx):
        """Divorce the current user."""
        with open('marryconfig.json', 'r') as f:
            config = json.load(f)

        if 'marriage' in config and config['marriage']:
            config['marriage'] = {}

            with open('marryconfig.json', 'w') as f:
                json.dump(config, f, indent=4)

            await ctx.send(f"{ctx.author.mention} ```is now divorced```")
        else:
            await ctx.send(f"{ctx.author.mention}, ```you are not married yet!```")

    @commands.command()
    async def marryinfo(self, ctx):
        """Display the information about the current user's marriage."""
        with open('marryconfig.json', 'r') as f:
            config = json.load(f)

        if 'marriage' in config and config['marriage']:
            marriage_info = config['marriage']

            info_message = (f"Marriage Info from config.json:\n"
                            f"**User ID:** {marriage_info['user']}\n"
                            f"**Partner ID:** {marriage_info['partner']}\n"
                            f"**Partner's Name:** {marriage_info['partner_name']}\n"
                            f"**Partner's Gender:** {marriage_info['partner_gender']}")
            await ctx.send(info_message)
        else:
            await ctx.send(f"{ctx.author.mention} ```you are not married yet!```")
            
            
    
        
    

def setup(bot):
    bot.add_cog(MarriageCog(bot))
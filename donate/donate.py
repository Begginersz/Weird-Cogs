import asyncio
import random
import os
import time
import discord
from discord.ext import commands
from .utils import checks
from .utils.dataIO import dataIO
from __main__ import send_cmd_help

icon="https://cdn3.iconfinder.com/data/icons/avatars-15/64/_Ninja-2-512.png"
credits="Bot by Weirdo914"

class donate:
    """My custom cog that does stuff!"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/donate/donate.json"
        self.config = dataIO.load_json(self.file_path)
        self.system = {}

    @commands.group(pass_context=True, no_pm=True)
    async def setdonate(self, ctx):
        """Used To Set donate info"""

        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @setdonate.command(name="title", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _title_donate(self, ctx):
        """Used To change tile of donate.
        What would you Like to change the tile of Donate to?
        (Reply in 100 seconds)"""
        author = ctx.message.author
        cancel = ctx.prefix + "cancel"
        settings = self.check_server_settings(author.server)
        title = await self.bot.wait_for_message(timeout=100, author=author)
        settings["Title"] = str (title.content)
        self.save_system()
        end = await self.bot.say("The title of Donate has been changed")
        await asyncio.sleep(1)
        for msg in [end]:
            await self.bot.delete_message(msg)
            
        def save_system(self):
            dataIO.save_json(self.file_path, self.system)

    def check_config(self, server):
        if server.id in self.config['Servers']:
            return self.config['Servers'][server.id]
        else:
            self.config['Servers'][server.id] = {"Title": "Help Support My Server",
                    "Text": ":point_right:Donate money:point_left:",
                    "Link": "https://bit.ly/1Lcouww",
                    "Colour": "Green",}
            self.save_settings()
            return self.config['Servers'][server.id]
        
        
    @commands.command()
    async def donate(self):
        """Donate message"""

        #Embed Code
        embed = discord.Embed(colour=0x00ff00)
        embed.add_field(name=":point_right:Donate money:point_left:", value="https://bit.ly/2EJK7sV")
        embed.title = "Help support CRZA Esports"
        embed.set_footer(text=credits,  icon_url=icon)
        await self.bot.say(embed=embed)
        
    def check_folders():
        if not os.path.exists('data/donate'):
            print("Creating data/donate folder...")
            os.makedirs('data/donate')

    def check_files():
        system = {"Servers": {}}

    f = "data/donate/donate.json"

    if not dataIO.is_valid_json(f):
        print("Adding donate.json to data/donate/")
        dataIO.save_json(f, system)
        
def setup(bot):
    bot.add_cog(donate(bot))

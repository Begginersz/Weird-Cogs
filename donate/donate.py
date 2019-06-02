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
credit="Bot by Weirdo914"

class donate:
    """Cog to help support your server with a donate command."""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/donate/donate.json"
        self.system = dataIO.load_json(self.file_path)

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
        
    @commands.command(pass_context=True, no_pm=True)
    async def donate(self, ctx):
        """Donate message"""
        server = ctx.message.server
        settings = self.check_server_settings(server)
        title = settings["Title"]

        #Embed Code
        embed = discord.Embed(colour=0x00ff00)
        embed.add_field(name=":point_right:Donate money:point_left:", value="https://bit.ly/2EJK7sV")
        embed.title = title
        embed.set_footer(text=credit,  icon_url=icon)
        await self.bot.say(embed=embed)
        
def check_server_settings(self, server):
    if server.id not in self.system["Servers"]:
        default = {
            "Title": "Help Support My Server",
            "Text": ":point_right:Donate money:point_left:",
            "Link": "https://bit.ly/1Lcouww",
            "Colour": "Green"
        }
        self.system["Servers"][server.id] = default
        self.save_system()
        path = self.system["Servers"][server.id]
        return path
    else:
        path = self.system["Servers"][server.id]
        return path
        
def check_folders():
    if not os.path.exists('data/donate'):
        print("Creating data/donate folder...")
        os.makedirs('data/donate')

def check_files():
    default = {"Servers": {}}

    f = "data/donate/donate.json"

    if not dataIO.is_valid_json(f):
        print("Adding donate.json to data/donate/")
        dataIO.save_json(f, default)
        
def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(donate(bot))

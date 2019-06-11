import asyncio
import os
import discord
import random
from discord.ext import commands
from .utils import checks
from .utils.dataIO import dataIO
from __main__ import send_cmd_help

icon = "https://cdn3.iconfinder.com/data/icons/avatars-15/64/_Ninja-2-512.png"
credit = "Bot by Weirdo914"

def returnhex():
    return random.randint(0, 0xFFFFFF)

class donate:
    """Cog to help support your server with a donate command."""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/donate/donate.json"
        self.system = dataIO.load_json(self.file_path)
        self.colours = { "red" : discord.Color.red,
                         "dark red" : discord.Color.dark_red,
                         "blue" : discord.Color.blue,
                         "dark blue" : discord.Color.dark_blue,
                         "teal" : discord.Color.teal,
                         "dark teal" :discord.Color.dark_teal,
                         "green" : discord.Color.green,
                         "dark green" : discord.Color.dark_green,
                         "purple" : discord.Color.purple,
                         "dark purple" :discord.Color.dark_purple,
                         "magenta" : discord.Color.magenta,
                         "dark magenta" : discord.Color.dark_magenta,
                         "gold" :discord.Color.gold,
                         "dark gold" : discord.Color.dark_gold,
                         "orange" :discord.Color.orange,
                         "dark orange" :discord.Color.dark_orange,
                         "random" : returnhex
                         }

    @commands.group(pass_context=True, no_pm=True)
    async def setdonate(self, ctx):
        """Used To Set donate info"""

        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @setdonate.command(name="title", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _title_donate(self, ctx):
        """Used To change tile of donate message."""
        await self.bot.say("```What would you Like to change the tile of your Donate Message to?\n(Reply in 1 minute.)```")
        author = ctx.message.author
        cancel = ctx.prefix + "cancel"
        settings = self.check_server_settings(author.server)
        title = await self.bot.wait_for_message(timeout=60, author=author)
        if title is None:
            await self.bot.say("You took too long. Canceling the edit process.")
            await asyncio.sleep(1)
        else:
            settings["Title"] = str(title.content)
            self.save_system()
            await self.bot.say("The title of your Donate Message has been changed")
            await asyncio.sleep(1)

    @setdonate.command(name="text", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _text_donate(self, ctx):
        """Used To change text of donate message."""
        await self.bot.say("```What would you Like to change the text in your Donate Message to?\n(Reply in 2 minutes.)```")
        author = ctx.message.author
        cancel = ctx.prefix + "cancel"
        settings = self.check_server_settings(author.server)
        text = await self.bot.wait_for_message(timeout=120, author=author)
        if text is None:
            await self.bot.say("You took too long. Canceling the edit process.")
            await asyncio.sleep(1)
        else:
            settings["Text"] = str(text.content)
            self.save_system()
            await self.bot.say("The text in your Donate Message has been changed")
            await asyncio.sleep(1)

    @setdonate.command(name="link", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _link_donate(self, ctx):
        """Used To set the link in donate message."""
        await self.bot.say(
            "```Please enter the link where your server members can donate to you. Better use a bit.ly shortened link\n(Reply in 1 minute.)```")
        author = ctx.message.author
        cancel = ctx.prefix + "cancel"
        settings = self.check_server_settings(author.server)
        link = await self.bot.wait_for_message(timeout=60, author=author)
        if link is None:
            await self.bot.say("You took too long. Canceling the edit process.")
            await asyncio.sleep(1)
        else:
            settings["Link"] = str(link.content)
            self.save_system()
        await self.bot.say("The link in your Donate Message has been changed")
        await asyncio.sleep(1)

    @setdonate.command(name="colour", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _colour_donate(self, ctx):
        """Used To set the colour of donate message."""
        await self.bot.say(
            "```What would you like to set the colour of Donate Message to?\nSee available colours using {}embedcolours .\n(Reply in 1 minute.)```".format(ctx.prefix))
        author = ctx.message.author
        cancel = ctx.prefix + "cancel"
        settings = self.check_server_settings(author.server)
        color = await self.bot.wait_for_message(timeout=60, author=author)
        if color is None:
            await self.bot.say("You took too long. Canceling the edit process.")
            await asyncio.sleep(1)
        else:
            colour = str(color.content)
            if colour.lower() not in self.colours:
                await self.bot.say("```Enter a valid colour. See available colours using {}embedcolours .```".format(ctx.prefix))
                await asyncio.sleep(1)
            else:
                settings["Colour"] = colour
                self.save_system()
                await self.bot.say("The colour of your Donate Message has been changed")
                await asyncio.sleep(1)

    @commands.command(pass_context=True, no_pm=True)
    async def donate(self, ctx):
        """Donate message"""
        settings = self.check_server_settings(ctx.message.server)
        title = settings["Title"]
        msg = settings["Text"]
        link = settings["Link"].format(ctx.prefix)
        color = settings["Colour"]
        embed_color = self.colours[color.lower()]()

        # Embed Code
        embed = discord.Embed(colour=embed_color)
        embed.add_field(name=msg, value=link)
        embed.title = title
        embed.set_footer(text=credit, icon_url=icon)
        await self.bot.say(embed=embed)

    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_server=True)
    async def embedcolours(self, ctx):
        """Shows available colours for Embed Message"""
        await self.bot.say("""```fix
Available Colours-
```
```css
\nRed\nDark Red\nBlue\nDark Blue\nTeal\nDark Teal\nGreen\nDark Green\nPurple\nDark Purple\nMagenta\nDark Magenta\nGold\nDark Gold\nOrange\nDark Orange\nRandom
```""")
        await asyncio.sleep(1)


    def save_system(self):
        dataIO.save_json(self.file_path, self.system)

    def check_server_settings(self, server):
        if server.id not in self.system["Servers"]:
            default = {
                "Title": "Help Support My Server",
                "Text": ":point_right:Donate money:point_left:",
                "Link": "Set the link using {}setdonate link",
                "Colour": "Random"
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

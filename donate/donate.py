import asyncio
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
        cancel = ctx.prefix + "cancel"
        settings = self.check_server_settings(ctx.massage.author.server)
        title = await self.bot.wait_for_message(timeout=100, author=author)
        settings["Title"] = str (title.content)
        self.save_system()
        end = await self.bot.say("The title of Donate has been changed")
        await asyncio.sleep(1)
        for msg in [end]:
            await self.bot.delete_message(msg)


    @commands.command()
    async def donate(self):
        """Donate message"""

        #Embed Code
        embed = discord.Embed(colour=0x00ff00)
        embed.add_field(name=":point_right:Donate money:point_left:", value="https://bit.ly/2EJK7sV")
        embed.title = "Help support CRZA Esports"
        embed.set_footer(text=credits,  icon_url=icon)
        await self.bot.say(embed=embed)

def setup(bot):
    bot.add_cog(Mycog(bot))

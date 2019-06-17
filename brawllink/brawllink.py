import discord
from discord.ext import commands
from .utils import checks
from __main__ import send_cmd_help, settings
from cogs.utils.dataIO import dataIO
import os
import asyncio


class brawllink:
    """Makes embed on and brawlstars Room link"""

    def __init__(self, bot):
        self.bot = bot
        self.location = 'data/brawllink/settings.json'
        self.json = dataIO.load_json(self.location)

    @commands.group(pass_context=True, no_pm=True)
    async def brawllinkset(self, ctx):
        """Manages the settings for Brawllink."""
        serverid = ctx.message.server.id
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
        if serverid not in self.json:
            self.json[serverid] = {'toggle': False, 'excluded_channels': []}

    @brawllinkset.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def toggle(self, ctx):
        """Enable/disables brawllink in the server"""
        serverid = ctx.message.server.id
        if self.json[serverid]['toggle'] is True:
            self.json[serverid]['toggle'] = False
            await self.bot.say('Now, embeds will be created for room invites.')
        elif self.json[serverid]['toggle'] is False:
            self.json[serverid]['toggle'] = True
            await self.bot.say('Now, embeds will not be created for room invites.')
        dataIO.save_json(self.location, self.json)

    @brawllinkset.group(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def exclude(self, ctx):
        """Exclude the channels where brawllink will be active"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
        if "excluded_channels" not in self.json[ctx.message.server.id]:
            self.json[ctx.message.server.id]["excluded_channels"] = []

    @exclude.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def add(self, ctx, channel: discord.Channel):
        """Add a channel to the exclusion list"""
        serverid = ctx.message.server.id
        if channel.id not in self.json[serverid]["excluded_channels"]:
            self.json[serverid]["excluded_channels"].append(channel.id)
            await self.bot.say('Added {} to the exclusion list.'.format(channel.name))
            dataIO.save_json(self.location, self.json)
        else:
            await self.bot.say('This channel is already in the exclusion list')

    @exclude.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def remove(self, ctx, channel: discord.Channel):
        """Remove a channel from the exclusion list"""
        serverid = ctx.message.server.id
        if channel.id in self.json[serverid]["excluded_channels"]:
            self.json[serverid]["excluded_channels"].remove(channel.id)
            await self.bot.say('Removed {} from the exclusion list'.format(channel.name))
            dataIO.save_json(self.location, self.json)
        else:
            await self.bot.say('This channel is not in the exclusion list')

    async def _new_message(self, message):
        """Finds the message and checks it for regex"""
        user = message.author
        name = user.display_name
        icon = user.avatar_url
        link = message.content
        pattern = "https://link.brawlstars.com/invite/gameroom/en?tag="
        title = "**Join {}'s Room**".format(name)
        channel = message.channel

        if link.startswith("https://"):
            if pattern in link:
                tag_raw = link.replace('https://link.brawlstars.com/invite/gameroom/en?tag=', '')
                tag = ":arrow_up: " + tag_raw + " :arrow_up:"
                char = len(tag_raw)
                if char == 8:
                    if tag_raw.isalnum():
                        if tag_raw.isupper():
                            asyncio.sleep(0.5)
                            await self.bot.delete_message(message)
                            embed = discord.Embed(title=title, url=link, description=tag, color=0xff0000)
                            embed.set_footer(text=user, icon_url=icon)
                            await self.bot.send_message(channel, embed=embed)


def check_folder():
    if not os.path.exists('data/brawllink'):
        os.makedirs('data/brawllink')


def check_file():
    f = 'data/brawllink/settings.json'
    if dataIO.is_valid_json(f) is False:
        dataIO.save_json(f, {})


def setup(bot):
    check_folder()
    check_file()
    n = brawllink(bot)
    bot.add_cog(n)
    bot.add_listener(n._new_message, 'on_message')

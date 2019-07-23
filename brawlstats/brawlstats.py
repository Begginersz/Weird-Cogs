import discord
from discord.ext import commands
from .utils import checks
from __main__ import send_cmd_help, settings
from cogs.utils.dataIO import dataIO, fileIO
import os
import asyncio
import re
import brawlstats

BOTCOMMANDER_ROLES = ["Mod", "admin"]

creditIcon = "https://cdn3.iconfinder.com/data/icons/avatars-15/64/_Ninja-2-512.png"
credits = "Cog by Weirdo914"


tags_path = "data/brawlstats/tags.json"
auth_path = "data/brawlstats/auth.json"


class tags:
    """Tags Management"""

    def __init__(self, path):
        self.tags_bs = dataIO.load_json(path)

    async def verifyTag(self, tag):
        """Check if a player/can tag is valid"""
        check = ['P', 'Y', 'L', 'Q', 'G', 'R', 'J', 'C', 'U', 'V', '0', '2', '8', '9']

        if any(i not in check for i in tag):
            return False

        return True

    async def formatTag(self, tag):
        """Sanitize and format CR Tag"""
        return tag.strip('#').upper().replace('O', '0')
        return True

    async def formatName(self, name):
        """Sanitize player Name"""
        p = re.sub(r'<c\d>(.*)<\/c>', r'\1', name)
        return p or name

    async def linkTag(self, tag, userID):
        """Link a BS player tag to a discord User"""
        tag = await self.formatTag(tag)

        self.tags_bs.update({userID: {'tag': tag}})
        dataIO.save_json(tags_path, self.tags_bs)

    async def unlinkTag(self, userID):
        """Unlink a BS player tag to a discord User"""
        if self.tags_bs.pop(str(userID), None):
            dataIO.save_json(tags_path, self.tags_bs)
            return True
        return False

    async def getTag(self, userID):
        """Get a user's BS Tag"""
        return self.tags_bs[userID]['tag']

    async def getUser(self, serverUsers, tag):
        """Get User from BS Tag"""
        for user in serverUsers:
            if user.id in self.tags_bs:
                player_tag = self.tags_bs[user.id]['tag']
                if player_tag == await self.formatTag(tag):
                    return user
        return None


class auth:

    def __init__(self, path):
        self.auth = dataIO.load_json(path)

    async def addToken(self, key):
        """Add a BrawlAPI.cf Token"""
        self.auth['Token'] = key
        dataIO.save_json(auth_path, self.auth)

    def getToken(self):
        """Get brawlstars-api Token"""
        return self.auth['Token']


class BrawlStats:
    """Live statistics for Brawl Stars"""

    def __init__(self, bot):
        self.bot = bot
        self.location = 'data/brawlstats/settings.json'
        self.json = dataIO.load_json(self.location)
        self.auth = auth(auth_path)
        self.tags = tags(tags_path)
        self.brawl = brawlstats.Client(self.auth.getToken(), is_async=False)

    def emoji(self, name):
        """Emoji by name."""
        for emoji in self.bot.get_all_emojis():
            if emoji.name == name.replace(" ", "").replace("-", "").replace(".", ""):
                return '<:{}:{}>'.format(emoji.name, emoji.id)
        return ''

    def getLeagueEmoji(self, trophies):
        """Get clan war League Emoji"""
        mapLeagues = {
            "starLeague": [10000, 90000],
            "masterLeague": [8000, 9999],
            "crystalLeague": [6000, 7999],
            "diamondLeague": [4000, 5999],
            "goldLeague": [3000, 3999],
            "silverLeague": [2000, 2999],
            "bronzeLeague": [1000, 1999],
            "woodLeague": [0, 999]
        }
        for league in mapLeagues.keys():
            if mapLeagues[league][0] <= trophies <= mapLeagues[league][1]:
                return self.emoji(league)

    async def getClubLeader(self, members):
        """Return clan leader from a list of members"""
        for member in members:
            if member.role == "President":
                return "{} {}".format(self.getLeagueEmoji(member.trophies), await self.tags.formatName(member.name))

    def getbrawlers(self, profile):
        """Returns Brawlers with Power"""
        brw = profile.brawlers
        out = ""
        pl = 0
        for brawlers in brw:
            nm = brawlers.name
            power = brawlers.power
            try:
                emo = self.emoji(nm)
                pl += 1
                if pl % 6 == 0:
                    out = out + str(emo) + "`" + str(power) + "`" + "\n"
                else:
                    out = out + str(emo) + "`" + str(power) + "`"
            except:
                pass
        return str(out)

    def trophyrange(self, members):
        lst = []
        for m in members:
            tro = m.trophies
            lst.append(tro)
        minimum = min(lst)
        maximum = max(lst)
        return minimum, maximum

    def numbers(self, members):
        mem = 0
        sen = 0
        co = 0
        for m in members:
            if m.role == "Member":
                mem += 1
            elif m.role == "Senior":
                sen += 1
            elif m.role == "Vice President":
                co += 1
        return mem, sen, co

    def top(self, members):
        topmem = ""
        mem = 0
        topsen = ""
        sen = 0
        topco = ""
        co = 0
        for m in members:
            if m.role == "Member":
                mem += 1
                if mem <= 5:
                    info = "`" + str(m.trophies) + "` " + m.name + "\n"
                    topmem = topmem + info
            elif m.role == "Senior":
                sen += 1
                if sen <= 5:
                    info = "`" + str(m.trophies) + "` " + m.name + "\n"
                    topsen = topsen + info
            else:
                co += 1
                if co <= 5:
                    info = "`" + str(m.trophies) + "` " + m.name + "\n"
                    topco = topco + info
        return topmem, topsen, topco

    def trophysum(self, members):
        mem = 0
        tromem = 0
        sen = 0
        trosen = 0
        co = 0
        troco = 0
        for m in members:
            if m.role == "Member":
                mem += 1
                tromem += m.trophies
            elif m.role == "Senior":
                sen += 1
                trosen += m.trophies
            else:
                co += 1
                troco += m.trophies
        avgmem = round(tromem/mem)
        avgsen = round(trosen/sen)
        avgco = round(troco/co)
        return avgmem, avgsen, avgco

    def eventtime(self, time: int):
        if time >= 86400:
            hrsrem = time % 86400
            days = round((time - hrsrem)/86400)
            if days > 1:
                day = "**" + str(days) + "** days"
            else:
                day = "**" + str(days) + "** day"
        else:
            day = ""
            hrsrem = time
        if hrsrem >= 3600:
            minrem = hrsrem % 3600
            hrs = round((hrsrem - minrem)/3600)
            if hrs > 1:
                hr = "**" + str(hrs) + "** hours"
            else:
                hr = "**" + str(hrs) + "** hour"
            if not day == "":
                hr = ", " + hr
        else:
            hr = ""
            minrem = hrsrem
        if minrem >= 60:
            secrem = minrem % 60
            mins = round((minrem - secrem)/60)
            if mins > 1:
                minut = "**" + str(mins) + "** minutes"
            else:
                minut = "**" + str(mins) + "** minute"
            if not hr == "":
                minut = ", " + minut
        else:
            minut = ""
            secrem = minrem
        if day == "" and hr == "":
            secs = secrem
            if secs > 1:
                sec = ", **" + str(secs) + "** seconds"
            else:
                sec = ", **" + str(secs) + "** second"
            if not minut == "":
                sec = ", " + sec
        else:
            sec = ""
        final = day + hr + minut + sec
        return str(final)

    @commands.group(pass_context=True, no_pm=True)
    async def bs(self, ctx):
        """Brawl Stars Commands"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @bs.command(pass_context=True, aliases=['brawlprofile'])
    async def profile(self, ctx, member: discord.Member = None):
        """View your Brawl Stars Profile Data and Statstics."""

        member = member or ctx.message.author

        await self.bot.type()
        try:
            profiletag = await self.tags.getTag(member.id)
            profiledata = self.brawl.get_player(profiletag)
        except brawlstats.RequestError as e:
            return await self.bot.say('```\n{}: {}\n```'.format(e.code, e.error))
        except KeyError:
            return await self.bot.say("You need to first save your profile using ``{}bs save #GAMETAG``".format(ctx.prefix))

        brawlers = self.getbrawlers(profiledata)
        embed = discord.Embed(color=0xFAA61A)
        embed.set_author(name="{} (#{})".format(await self.tags.formatName(profiledata.name), profiledata.tag),
                         icon_url=profiledata.avatar_url,
                         url="https://brawlstats.com/profile/" + profiledata.tag)
        embed.add_field(name="Trophies", value="{} {:,}".format(self.getLeagueEmoji(profiledata.trophies), profiledata.trophies), inline=True)
        embed.add_field(name="Highest Trophies", value="{} {:,}".format(self.getLeagueEmoji(profiledata.highest_trophies), profiledata.highest_trophies), inline=True)
        embed.add_field(name="Level", value="{} `{}` - `{}`".format(self.emoji("xp"), profiledata.exp_level, profiledata.exp_fmt), inline=True)
        if profiledata.club is not None:
            embed.add_field(name="Club {}".format(profiledata.club.role),
                            value=self.emoji("band") + profiledata.club.name, inline=True)
        embed.add_field(name="Solo SD Victories", value="{} {}".format(self.emoji("Showdown"), profiledata.solo_showdown_victories), inline=True)
        embed.add_field(name="Duo SD Victories", value="{} {}".format(self.emoji("duoshowdown"), profiledata.duo_showdown_victories), inline=True)
        embed.add_field(name="3 vs 3 Victories", value="{} {}".format(self.emoji("win"), profiledata.victories), inline=True)
        embed.add_field(name="Best Time as Big Brawler", value="{} {}".format(self.emoji("BigGame"), profiledata.best_time_as_big_brawler), inline=True)
        embed.add_field(name="Best Robo Rumble Time", value="{} {}".format(self.emoji("RoboRumble"), profiledata.best_robo_rumble_time), inline=True)
        embed.add_field(name="{} Brawlers {}/27".format(self.emoji("default"), profiledata.brawlers_unlocked), value=brawlers, inline=True)
        embed.set_footer(text=credits, icon_url=creditIcon)

        await self.bot.say(embed=embed)

    @bs.command(pass_context=True)
    async def club(self, ctx):
        """View your Brawl Stars Club statistics and information"""
        member = ctx.message.author

        await self.bot.type()
        try:
            profiletag = await self.tags.getTag(member.id)
            profiledata = self.brawl.get_player(profiletag)
        except brawlstats.RequestError as e:
            return await self.bot.say('```\n{}: {}\n```'.format(e.code, e.error))
        except KeyError:
            return await self.bot.say("You need to first save your profile using ``{}bs save #GAMETAG``".format(ctx.prefix))
        await self.bot.type()

        if profiledata.club is None:
            return self.bot.say("You are are not in a club.")

        clantag = profiledata.club.tag

        try:
            clandata = self.brawl.get_club(clantag)
        except brawlstats.RequestError:
            return await self.bot.say("Error: cannot reach Brawl Stars Servers. Please try again later.")
        low, high = self.trophyrange(clandata.members)
        mem, sen, co = self.numbers(clandata.members)
        topmem, topsen, topco = self.top(clandata.members)
        avgmem, avgsen, avgco = self.trophysum(clandata.members)
        embed = discord.Embed(color=0xFAA61A)
        embed.set_author(name=clandata.name + " | #" + clandata.tag,
                         icon_url=clandata.badge_url,
                         url="https://brawlstats.com/club/" + clandata.tag)
        embed.add_field(name="Trophies", value="{} {:,}".format(self.emoji("bstrophy2"), clandata.trophies), inline=True)
        embed.add_field(name="Required Trophies",
                        value="{} {:,}".format(self.getLeagueEmoji(clandata.required_trophies), clandata.required_trophies), inline=True)
        embed.add_field(name="Members", value="{} {}/100".format(self.emoji("gameroom"), clandata.members_count), inline=True)
        embed.add_field(name="Status", value=":envelope_with_arrow: {}".format(clandata.status), inline=True)
        embed.add_field(name="Trophy Range",
                        value="{}`{}`-{}`{}`".format(self.getLeagueEmoji(low), low, self.getLeagueEmoji(high), high), inline=True)
        embed.add_field(name="President", value=await self.getClubLeader(clandata.get('members')), inline=True)
        embed.add_field(name="Online", value="{} {:,}/{}".format(self.emoji("online"), clandata.online_members, clandata.members_count), inline=True)
        embed.add_field(name="Description", value=clandata.description, inline=False)
        if mem > 0:
            embed.add_field(name="Top Members({})".format(mem), value=topmem + "Average:{}`{}`".format(self.getLeagueEmoji(avgmem), avgmem), inline=True)
        if sen > 0:
            embed.add_field(name="Top Seniors({})".format(sen), value=topsen + "Average:{}`{}`".format(self.getLeagueEmoji(avgsen), avgsen), inline=True)
        embed.add_field(name="Top Presidents({}+1)".format(co), value=topco + "Average:{}`{}`".format(self.getLeagueEmoji(avgco), avgco), inline=True)
        embed.set_footer(text=credits, icon_url=creditIcon)

        await self.bot.say(embed=embed)

    @bs.command(pass_context=True)
    async def events(self, ctx):
        """Gives List of Current and upcoming events"""
        await self.bot.type()
        image = "https://cdn.discordapp.com/avatars/517368847322447873/df58e404ffe235c686fe8008b29c2c34.png"
        try:
            events = self.brawl.get_events()
        except brawlstats.RequestError:
            return await self.bot.say("Error: cannot reach Brawl Stars Servers. Please try again later.")
        finemoji = "<a:endtime:602540846922858537>"
        currentevents = events.current
        upcomingevents = events.upcoming
        spcl = False
        embed = discord.Embed(color=0xFAA61A)
        embed.set_author(name="Live Event Rotation",
                         icon_url=image,
                         url="https://brawlstats.com/events")
        for events in currentevents:
            eventid = events.slot
            if eventid == 7:
                spcl = True
            remtime = events.end_time_in_seconds
            eventmap = events.map_name
            mode = events.game_mode
            memo = mode.replace(" ", "")
            emoji = self.emoji(memo)
            title = emoji + " " + mode + " (" + eventmap + ")"
            time = self.eventtime(remtime)
            up = ""
            for coming in upcomingevents:
                if coming.slot == eventid:
                    upeventmap = coming.map_name
                    upmode = coming.game_mode
                    modeemoji = upmode.replace(" ", "")
                    upemoji = self.emoji(modeemoji)
                    emo = self.emoji("next")
                    updes = emo + " " + upemoji + " " + upmode + " (" + upeventmap + ")"
                    up = up + updes
            timedes = finemoji + " " + time
            if up == "":
                des = timedes + "\n\u200b"
            else:
                des = up + "\n" + timedes + "\n\u200b"
            embed.add_field(name=title, value=des, inline=False)
        if not spcl:
            for events in upcomingevents:
                eventid = events.slot
                if eventid == 7:
                    remtime = events.end_time_in_seconds
                    eventmap = events.map_name
                    mode = events.game_mode
                    memo = mode.replace(" ", "")
                    emoji = self.emoji(memo)
                    title = emoji + " " + mode + " (" + eventmap + ")"
                    time = self.eventtime(remtime)
                    des = finemoji + " " + time
                    embed.add_field(name=title, value=des, inline=False)
        embed.set_thumbnail(url="https://i.imgur.com/WbFDHkV.png")
        embed.set_footer(text=credits, icon_url=creditIcon)
        await self.bot.say(embed=embed)

    @bs.command(pass_context=True, no_pm=True, aliases=['bssave'])
    async def save(self, ctx, profiletag: str, member: discord.Member = None):
        """ save your Brawl Stars Profile Tag

        Example:
            [p]bssave #CRRYTPTT @GR8
            [p]bssave #CRRYRPCC
        """

        server = ctx.message.server
        author = ctx.message.author

        profiletag = await self.tags.formatTag(profiletag)

        if not await self.tags.verifyTag(profiletag):
            return await self.bot.say("The ID you provided has invalid characters. Please try again.")

        await self.bot.type()

        allowed = False
        if member is None:
            allowed = True
        elif member.id == author.id:
            allowed = True
        else:
            botcommander_roles = [discord.utils.get(server.roles, name=r) for r in BOTCOMMANDER_ROLES]
            botcommander_roles = set(botcommander_roles)
            author_roles = set(author.roles)
            if len(author_roles.intersection(botcommander_roles)):
                allowed = True

        if not allowed:
            return await self.bot.say("You dont have enough permissions to set tags for others.")

        member = member or ctx.message.author

        try:
            profiledata = self.brawl.get_player(profiletag)

            checkUser = await self.tags.getUser(server.members, profiletag)
            if checkUser is not None:
                return await self.bot.say("Error, This Player ID is already linked with **" + checkUser.display_name + "**")

            await self.tags.linkTag(profiletag, member.id)

            embed = discord.Embed(color=discord.Color.green())
            avatar = member.avatar_url if member.avatar else member.default_avatar_url
            embed.set_author(name='{} (#{}) has been successfully saved.'.format(await self.tags.formatName(profiledata.name), profiletag),
                             icon_url=avatar)
            await self.bot.say(embed=embed)
        except brawlstats.NotFoundError:
            return await self.bot.say("We cannot find your ID in our database, please try again.")
        except brawlstats.RequestError:
            return await self.bot.say("Error: cannot reach Brawl Stars Servers. Please try again later.")

    @bs.command()
    @checks.mod_or_permissions(administrator=True)
    async def settoken(self, *, key):
        """Input your BrawlStars API Token"""
        await self.auth.addToken(key)
        await self.bot.say("BrawlAPI Token set")

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
    if not os.path.exists('data/brawlstats'):
        os.makedirs('data/brawlstats')


def check_file():
    if not fileIO(tags_path, "check"):
        print("Creating empty tags.json...")
        fileIO(tags_path, "save", {"0": {"tag": "DONOTREMOVE"}})

    if not fileIO(auth_path, "check"):
        print("enter your BrawlAPI token in data/brawlstats/auth.json...")
        fileIO(auth_path, "save", {"Token": "enter your BrawlAPI token here!"})

    f = 'data/brawlstats/settings.json'
    if dataIO.is_valid_json(f) is False:
        dataIO.save_json(f, {})


def check_auth():
    c = dataIO.load_json(auth_path)
    if 'TokenI' not in c:
        c['TOken'] = "enter your BrawlAPI token here!"
    dataIO.save_json(auth_path, c)


def setup(bot):
    check_folder()
    check_file()
    n = BrawlStats(bot)
    bot.add_cog(n)
    bot.add_listener(n._new_message, 'on_message')

import discord
from discord.ext import commands
from .utils import checks
from __main__ import send_cmd_help, settings
from cogs.utils.dataIO import dataIO, fileIO
import os
import asyncio
import re
import brawlstats
from heapq import nlargest


BOTCOMMANDER_ROLES = ["Mod", "admin"]

creditIcon = "https://cdn3.iconfinder.com/data/icons/avatars-15/64/_Ninja-2-512.png"
credits = "Cog by Weirdo914"


tags_path = "data/brawlstats/tags.json"
auth_path = "data/brawlstats/auth.json"
maps_path = "data/brawlstats/maps.json"

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
        self.maps = dataIO.load_json(maps_path)
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
            "starLeague": [10000, 100000],
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
                    avid = m.avatar_id
                    emo = self.profileemoji(avid)
                    emoji = self.emoji(emo)
                    info = emoji + "`" + str(m.trophies) + "` " + m.name + "\n"
                    topmem = topmem + info
            elif m.role == "Senior":
                sen += 1
                if sen <= 5:
                    avid = m.avatar_id
                    emo = self.profileemoji(avid)
                    emoji = self.emoji(emo)
                    info = emoji + "`" + str(m.trophies) + "` " + m.name + "\n"
                    topsen = topsen + info
            else:
                co += 1
                if co <= 5:
                    avid = m.avatar_id
                    emo = self.profileemoji(avid)
                    emoji = self.emoji(emo)
                    info = emoji + "`" + str(m.trophies) + "` " + m.name + "\n"
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
            if not day + hr == "":
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
            if not day + hr + minut == "":
                sec = ", " + sec
        else:
            sec = ""
        final = day + hr + minut + sec
        return str(final)

    def profileemoji(self, avaid: int):
        brawler = {
            "3": "Shelly",
            "4": "Colt",
            "5": "Brock",
            "6": "Jessie",
            "7": "Nita",
            "8": "Dynamike",
            "9": "El Primo",
            "10": "Bull",
            "11": "Rico",
            "12": "Barley",
            "13": "Poco",
            "14": "Mortis",
            "15": "Bo",
            "16": "Spike",
            "17": "Crow",
            "18": "Piper",
            "28": "Pam",
            "29": "Tara",
            "34": "Darryl",
            "35": "Penny",
            "36": "Frank",
            "37": "Leon",
            "38": "Gene",
            "39": "Carl",
            "40": "Rosa",
            "41": "Bibi",
            "42": "Tick"
        }
        checkid = str(avaid - 28000000)
        if checkid in brawler:
            emoji = brawler[checkid]
        else:
            emoji = str(avaid)
        return emoji

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
    async def club(self, ctx, member: discord.Member = None):
        """View your Brawl Stars Club statistics and information"""

        member = member or ctx.message.author

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
            return await self.bot.say("You are are not in a club.")

        clantag = profiledata.club.tag

        try:
            clandata = self.brawl.get_club(clantag)
        except brawlstats.RequestError:
            return await self.bot.say("Error: cannot reach Brawl Stars Servers. Please try again later.")
        low, high = self.trophyrange(clandata.members)
        mem, sen, co = self.numbers(clandata.members)
        per = round((clandata.online_members * 100)/clandata.members_count)
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
        embed.add_field(name="Online", value="{} Online Members: {:,}/{} - {}%".format(self.emoji("online"), clandata.online_members, clandata.members_count, per), inline=True)
        embed.add_field(name="Description", value=clandata.description, inline=False)
        if mem > 0:
            embed.add_field(name="Top Members ({})".format(mem), value=topmem + "Average:{}`{}`".format(self.getLeagueEmoji(avgmem), avgmem), inline=True)
        if sen > 0:
            embed.add_field(name="Top Seniors ({})".format(sen), value=topsen + "Average:{}`{}`".format(self.getLeagueEmoji(avgsen), avgsen), inline=True)
        embed.add_field(name="Top Presidents ({}+1)".format(co), value=topco + "Average:{}`{}`".format(self.getLeagueEmoji(avgco), avgco), inline=True)
        embed.set_footer(text=credits, icon_url=creditIcon)

        await self.bot.say(embed=embed)

    @bs.command(pass_context=True)
    async def events(self):
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

    @bs.command(pass_context=True, aliases=['brawler'])
    async def brawlers(self, ctx, member: discord.Member = None):
        """Gives List of Your Brawlers with their rank and power"""

        member = member or ctx.message.author

        await self.bot.type()
        try:
            profiletag = await self.tags.getTag(member.id)
            profiledata = self.brawl.get_player(profiletag)
        except brawlstats.RequestError as e:
            return await self.bot.say('```\n{}: {}\n```'.format(e.code, e.error))
        except KeyError:
            return await self.bot.say("You need to first save your profile using ``{}bs save #GAMETAG``".format(ctx.prefix))

        brawlers = profiledata.brawlers
        xp = self.emoji("xp")
        star = self.emoji("Star")
        skins = 0
        brcount = 0
        cr = []
        mx = []
        embed = discord.Embed(color=0xFAA61A)
        embed.set_author(name="{} (#{})".format(await self.tags.formatName(profiledata.name), profiledata.tag),
                         icon_url=profiledata.avatar_url,
                         url="https://brawlstats.com/profile/" + profiledata.tag)
        embed1 = discord.Embed(color=0xFAA61A)
        for brawler in brawlers:
            brcount += 1
            name = brawler.name
            namemoji = self.emoji(name)
            if brawler.has_skin:
                skins += 1
                name = brawler.skin
            power = brawler.power
            if power == 10:
                emoji = star
            else:
                emoji = xp
            rank = brawler.rank
            rankemoji = self.emoji("R" + str(rank))
            currtrophies = brawler.trophies
            cr.append(currtrophies)
            maxtrophies = brawler.highest_trophies
            mx.append(maxtrophies)
            des = "{}`{}`  {}`{}/{}`".format(emoji, power, rankemoji, currtrophies, maxtrophies)
            title = "{} {}".format(namemoji, name)
            if brcount < 25:
                embed.add_field(name=title, value=des, inline=True)
            else:
                embed1.add_field(name=title, value=des, inline=True)
        if brcount < 25:
            embed.set_footer(text=credits, icon_url=creditIcon)
        else:
            embed1.set_footer(text=credits, icon_url=creditIcon)
        lsemoji = self.emoji("list")
        hcr = max(cr)
        lcr = min(cr)
        scr = 0
        for num in cr:
            scr += num
        acr = round(scr/brcount)
        hmx = max(mx)
        lmx = min(mx)
        smx = 0
        for num in mx:
            smx += num
        amx = round(smx/brcount)
        stats = "{}  `Total: {}/27`|`Range: {}-> {} / {}-> {}`|`Average: {} / {}`|`Skins: {}`".format(lsemoji, brcount, lcr, hcr, lmx, hmx, acr, amx, skins)
        if brcount < 22:
            embed.add_field(name="Brawler Stats", value=stats, inline=False)
            await self.bot.say(embed=embed)
        else:
            embed1.add_field(name="Brawler Stats", value=stats, inline=False)
            await self.bot.say(embed=embed)
            await self.bot.say(embed=embed1)

    @bs.command(pass_context=True)
    async def members(self, ctx, member: discord.Member = None):
        """Gives List of Your Club Members"""

        member = member or ctx.message.author

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
            return await self.bot.say("You are are not in a club.")

        clantag = profiledata.club.tag

        try:
            clandata = self.brawl.get_club(clantag)
        except brawlstats.RequestError:
            return await self.bot.say("Error: cannot reach Brawl Stars Servers. Please try again later.")

        members = clandata.members
        embed = discord.Embed(color=0xFAA61A)
        embed.set_author(name=clandata.name + " | #" + clandata.tag,
                         icon_url=clandata.badge_url,
                         url="https://brawlstats.com/club/" + clandata.tag)
        em2 = False
        if clandata.members_count > 50:
            em2 = True
            embed1 = discord.Embed(color=0xFAA61A)
            embed1.set_footer(text=credits, icon_url=creditIcon)
        else:
            embed.set_footer(text=credits, icon_url=creditIcon)
        count = 0
        extra = False
        if clandata.members_count % 2 == 1:
            extra = True
        for member in members:
            count += 1
            if count < 10:
                sno = "**`0{}.` ".format(str(count))
            else:
                sno = "**`{}.` ".format(str(count))
            trophies = member.trophies
            tromoji = self.getLeagueEmoji(trophies)
            name = member.name
            role = member.role
            con = "{}`{}` {} ({})**".format(tromoji, str(trophies), name, role)
            if count % 2 == 1:
                title = sno + con
            else:
                description = sno + con
            if count % 2 == 0:
                if count <= 50:
                    embed.add_field(name=title, value=description, inline=False)
                else:
                    embed1.add_field(name=title, value=description, inline=False)
            if extra:
                if count == clandata.members_count:
                    if count <= 50:
                        embed.add_field(name=title, value="/n/u200b", inline=False)
                    else:
                        embed1.add_field(name=title, value="/n/u200b", inline=False)
        await self.bot.say(embed=embed)
        if em2:
            await self.bot.say(embed=embed1)

    @bs.command(pass_context=True, aliases=["maps"])
    async def map(self, ctx, *, mapname):
        """View a Brawl Stars Map"""
        if mapname not in self.maps:
            notfoundembed = discord.Embed(color=0xFAA61A, description="Map `{}` could not be found.".format(mapname))
            return await self.bot.say(embed=notfoundembed)
        linkid = self.maps[mapname]["id"]
        linkname = mapname.replace(" ", "-")
        gamemode = self.maps[mapname]["mode"]
        gamemodelink = "https://www.starlist.pro/img/gamemode/" + gamemode + ".png"
        namelink = "https://www.starlist.pro/maps/detail/" + linkname
        link = str("https://media.githubusercontent.com/media/Mahi-Uddin/bs-assets/master/map_images/" + str(linkid) + ".png")
        authfield = False
        if "author" in self.maps[mapname]:
            author = self.maps[mapname]["author"]
            comap = self.emoji("commap")
            authfield = True
        embed = discord.Embed(color=0xFAA61A)
        embed.set_author(name=mapname,
                         icon_url=gamemodelink,
                         url=namelink)
        embed.set_image(url=link)
        if authfield:
            embed.add_field(name=comap + " Community Map", value="By **" + author + "**", inline=False)
        embed.set_footer(text=credits, icon_url=creditIcon)
        await self.bot.say(embed=embed)

    @bs.command(pass_context=True)
    async def leaderboard(self, ctx):
        await self.bot.type()
        user = ctx.message.author
        trosort = {}
        troinfo = {}
        server = user.server
        for member in server.members:
            try:
                profiletag = await self.tags.getTag(member.id)
                profiledata = self.brawl.get_player(profiletag)
                trophies = profiledata.trophies
                name = profiledata.name
                trosort[member.id] = trophies
                troinfo[member.id] = {}
                troinfo[member.id]["name"] = name
                troinfo[member.id]["tag"] = profiledata.tag
            except brawlstats.RequestError as e:
                return await self.bot.say('```\n{}: {}\n```'.format(e.code, e.error))
            except KeyError:
                pass
        sername = server.name
        serplayer = len(trosort)
        des = ""
        top10 = nlargest(10, trosort, key=trosort.get)
        await self.bot.type()
        if user.id in top10:
            usertop = True
        else:
            usertop = False
            selftro = trosort[user.id]
            ldb = sorted(trosort.values(), reverse=True )
            rank = ldb.index(selftro)
            nearhigh = ldb[rank - 2:rank]
            nearhigh.reverse()
            nearhigh = list(dict.fromkeys(nearhigh))
            nearhighlist = []
            for troph in nearhigh:
                for mm in trosort:
                    if trosort[mm] == troph:
                        nearhighlist.append(mm)
            nearhighlist = nearhighlist[0:2]
            nearhighlist.reverse()
            nearlow = ldb[rank + 1:rank + 3]
            nearlow = list(dict.fromkeys(nearlow))
            nearlowlist = []
            for troph in nearlow:
                for mm in trosort:
                    if trosort[mm] == troph:
                        nearlowlist.append(mm)
            nearlowlist = nearlowlist[0:2]
            near = nearhighlist + [user.id] + nearlowlist
        rno = 0
        lnk = "https://www.starlist.pro/stats/profile/"
        for memid in top10:
            rno += 1
            sno = "`0{}.` ".format(rno)
            if rno == 10:
                sno = "`10.` "
            tro = trosort[memid]
            tromoji = self.getLeagueEmoji(tro)
            name = troinfo[memid]["name"]
            tag = troinfo[memid]["tag"]
            link = lnk + tag
            memfo = sno + " {} `{}` [{}]({}) - <@{}>".format(tromoji, tro, name, link, memid)
            if memid == user.id:
                memfo = "**" + memfo + "**"
            des = des + "\n" + memfo
        embed = discord.Embed(color=0xFAA61A, title=sername + " leaderboard! ({})".format(serplayer), description=des)
        embed.set_footer(text=credits, icon_url=creditIcon)
        embed.set_thumbnail(url="https://www.starlist.pro/img/icon/trophy.png")
        if not usertop:
            rank -= 1
            val = ""
            for memid in near:
                sno = "`{}.` ".format(rank)
                rank += 1
                tro = trosort[memid]
                tromoji = self.getLeagueEmoji( tro )
                name = troinfo[memid]["name"]
                tag = troinfo[memid]["tag"]
                link = lnk + tag
                memfo = sno + " {} `{}` [{}]({}) - <@{}>".format(tromoji, tro, name, link, memid)
                if memid == user.id:
                    memfo = "**" + memfo + "**"
                val = val + "\n" + memfo
            embed.add_field(name="Your Position", value=val)
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

    f = 'data/brawlstats/maps.json'
    if dataIO.is_valid_json(f) is False:
        maps = {
            "Acute Angle": {
                "author": "Milan R.",
                "id": 1500147,
                "mode" : "Gem-Grab"
            },
            "Assembly Attack" : {
                "author" : "OwenReds",
                "id" : 1500130,
                "mode" : "Siege"
            },
            "Backyard Bowl" : {
                "id" : 1500024,
                "mode" : "Brawl-Ball"
            },
            "Bandit Stash" : {
                "id" : 1500017,
                "mode" : "Heist"
            },
            "Beach Ball" : {
                "author" : "FeFaLah",
                "id" : 1500143,
                "mode" : "Brawl-Ball"
            },
            "Beachcombers" : {
                "author" : "Thomas P.",
                "id" : 1500145,
                "mode" : "Heist"
            },
            "Bot Drop" : {
                "id" : 1500097,
                "mode" : "Siege"
            },
            "Bouncing Echo" : {
                "author" : "Lewinham",
                "id" : 1500113,
                "mode" : "Gem-Grab"
            },
            "Bridge Too Far" : {
                "author" : "Zagibulenka",
                "id" : 1500077,
                "mode" : "Heist"
            },
            "Bull Pen" : {
                "id" : 1500085,
                "mode" : "Bounty"
            },
            "Burning Sands" : {
                "author" : "Ossama H.",
                "id" : 1500150,
                "mode" : "Bounty"
            },
            "Cactus Corridor" : {
                "author" : "Schmedricks",
                "id" : 1500049,
                "mode" : "Heist"
            },
            "Canal Grande" : {
                "id" : 1500084,
                "mode" : "Bounty"
            },
            "Cavern Churn" : {
                "id" : 1500033,
                "mode" : "Showdown"
            },
            "Cell Division" : {
                "author" : "Lab2point0",
                "id" : 1500116,
                "mode" : "Gem-Grab"
            },
            "Center Stage" : {
                "author" : "Mordeus",
                "id" : 1500132,
                "mode" : "Brawl-Ball"
            },
            "Chew Out" : {
                "author" : "OwenReds",
                "id" : 1500120,
                "mode" : "Big-Game"
            },
            "Chill Cave" : {
                "author" : "DarkKnight",
                "id" : 1500040,
                "mode" : "Gem-Grab"
            },
            "Corner Case" : {
                "id" : 1500078,
                "mode" : "Heist"
            },
            "Cross Cut" : {
                "id" : 1500139,
                "mode" : "Gem-Grab"
            },
            "Crystal Cavern" : {
                "id" : 1500008,
                "mode" : "Gem-Grab"
            },
            "Crystal Clearing" : {
                "id" : 1500003,
                "mode" : "Bounty"
            },
            "Curveball" : {
                "author" : "ash",
                "id" : 1500134,
                "mode" : "Brawl-Ball"
            },
            "Danger Zone" : {
                "id" : 1500133,
                "mode" : "Boss-Fight"
            },
            "Deathcap Cave" : {
                "id" : 1500009,
                "mode" : "Gem-Grab"
            },
            "Deathcap Trap" : {
                "id" : 1500002,
                "mode" : "Bounty"
            },
            "Deep Siege" : {
                "id" : 1500091,
                "mode" : "Gem-Grab"
            },
            "Diamond Dust" : {
                "author" : "ash",
                "id" : 1500111,
                "mode" : "Gem-Grab"
            },
            "Double Swoosh" : {
                "author" : "benci",
                "id" : 1500115,
                "mode" : "Gem-Grab"
            },
            "Double Trouble" : {
                "id" : 1500043,
                "mode" : "Showdown"
            },
            "Dry Season" : {
                "id" : 1500088,
                "mode" : "Bounty"
            },
            "Dune Drift" : {
                "author" : "Binnyboy",
                "id" : 1500093,
                "mode" : "Showdown"
            },
            "Echo Chamber" : {
                "author" : "Lewinham",
                "id" : 1500041,
                "mode" : "Gem-Grab"
            },
            "Erratic Blocks" : {
                "author" : "Meme-grabbee",
                "id" : 1500105,
                "mode" : "Showdown"
            },
            "Escape Velocity" : {
                "author" : "Mordeus",
                "id" : 1500114,
                "mode" : "Gem-Grab"
            },
            "Excel" : {
                "id" : 1500086,
                "mode" : "Bounty"
            },
            "Eye of the Storm" : {
                "author" : "Pentagonal Cubes",
                "id" : 1500109,
                "mode" : "Showdown"
            },
            "Factory Rush" : {
                "author" : "G.W.B.S.",
                "id" : 1500142,
                "mode" : "Siege"
            },
            "Fancy Fencing" : {
                "author" : "Rushalisk",
                "id" : 1500042,
                "mode" : "Heist"
            },
            "Feast or Famine" : {
                "id" : 1500016,
                "mode" : "Showdown"
            },
            "Flooded Mine" : {
                "author" : "FatBubblyDragon",
                "id" : 1500048,
                "mode" : "Gem-Grab"
            },
            "Flying Fantasies" : {
                "author" : "Mordeus",
                "id" : 1500123,
                "mode" : "Showdown"
            },
            "Forks Out" : {
                "author" : "Mordeus",
                "id" : 1500047,
                "mode" : "Heist"
            },
            "Four Squared" : {
                "author" : "Electra Drake",
                "id" : 1500112,
                "mode" : "Gem-Grab"
            },
            "G.G. Corral" : {
                "id" : 1500023,
                "mode" : "Heist"
            },
            "Gift Wrap" : {
                "id" : 1500063,
                "mode" : "Gem-Grab"
            },
            "Hard Rock Mine" : {
                "id" : 1500007,
                "mode" : "Gem-Grab"
            },
            "Hideout" : {
                "id" : 1500022,
                "mode" : "Bounty"
            },
            "Holiday Chill" : {
                "id" : 1500059,
                "mode" : "Gem-Grab"
            },
            "Hot Maze" : {
                "author" : "Tony_A9",
                "id" : 1500055,
                "mode" : "Showdown"
            },
            "Hot Point" : {
                "author" : "Mordeus",
                "id" : 1500103,
                "mode" : "Showdown"
            },
            "Hot Potato" : {
                "author" : "AlexEsteAdevarat",
                "id" : 1500053,
                "mode" : "Heist"
            },
            "Hunting Party" : {
                "id" : 1500065,
                "mode" : "Big-Game"
            },
            "Ice Block Rock" : {
                "id" : 1500061,
                "mode" : "Gem-Grab"
            },
            "Island Invasion" : {
                "author" : "Rushalisk",
                "id" : 1500045,
                "mode" : "Showdown"
            },
            "Junk Park" : {
                "author" : "OwenReds",
                "id" : 1500127,
                "mode" : "Siege"
            },
            "Kaboom Canyon" : {
                "id" : 1500018,
                "mode" : "Heist"
            },
            "Keep Safe" : {
                "id" : 1500039,
                "mode" : "Robo-Rumble"
            },
            "Layer Cake" : {
                "author" : "OwenReds",
                "id" : 1500087,
                "mode" : "Bounty"
            },
            "Machine Zone" : {
                "id" : 1500057,
                "mode" : "Boss-Fight"
            },
            "Mecha Match" : {
                "author" : "Mr. Lee",
                "id" : 1500141,
                "mode" : "Siege"
            },
            "Metal Scrap" : {
                "id" : 1500067,
                "mode" : "Boss-Fight"
            },
            "Minecart Madness" : {
                "id" : 1500122,
                "mode" : "Gem-Grab"
            },
            "Nuts & Bolts" : {
                "id" : 1500099,
                "mode" : "Siege"
            },
            "Outlaw Camp" : {
                "id" : 1500006,
                "mode" : "Bounty"
            },
            "Pachinko Park" : {
                "id" : 1500027,
                "mode" : "Robo-Rumble"
            },
            "Passage" : {
                "author" : "Maxymus",
                "id" : 1500101,
                "mode" : "Showdown"
            },
            "Pinball Dreams" : {
                "author" : "Mordeus",
                "id" : 1500118,
                "mode" : "Brawl-Ball"
            },
            "Pinhole Punt" : {
                "id" : 1500026,
                "mode" : "Brawl-Ball"
            },
            "Pit Stop" : {
                "author" : "Lex",
                "id" : 1500137,
                "mode" : "Heist"
            },
            "Pool Party" : {
                "id" : 1500092,
                "mode" : "Brawl-Ball"
            },
            "Puddle Splash" : {
                "author" : "Lewinham",
                "id" : 1500052,
                "mode" : "Brawl-Ball"
            },
            "River Rush" : {
                "author" : "OwenReds",
                "id" : 1500107,
                "mode" : "Showdown"
            },
            "Robo Highway" : {
                "author" : "Mordeus",
                "id" : 1500131,
                "mode" : "Siege"
            },
            "Rockwall Brawl" : {
                "id" : 1500015,
                "mode" : "Showdown"
            },
            "Rolling Rumble" : {
                "id" : 1500075,
                "mode" : "Heist"
            },
            "Royal Runway" : {
                "author" : "OwenReds",
                "id" : 1500125,
                "mode" : "Showdown"
            },
            "Royal Tribute" : {
                "author" : "DuccioCh",
                "id" : 1500100,
                "mode" : "Heist"
            },
            "Safe Zone" : {
                "id" : 1500019,
                "mode" : "Heist"
            },
            "Sandy Gems" : {
                "author" : "GO away",
                "id" : 1500146,
                "mode" : "Heist"
            },
            "Sapphire Plains" : {
                "id" : 1500031,
                "mode" : "Gem-Grab"
            },
            "Scorched Stone" : {
                "author" : "OwenReds",
                "id" : 1500014,
                "mode" : "Showdown"
            },
            "Shooting Star" : {
                "id" : 1500005,
                "mode" : "Bounty"
            },
            "Side Story" : {
                "author" : "OwenReds",
                "id" : 1500138,
                "mode" : "Heist"
            },
            "Skull Creek" : {
                "id" : 1500013,
                "mode" : "Showdown"
            },
            "Snake Cavern" : {
                "author" : "Loo K.H.",
                "id" : 1500148,
                "mode" : "Gem-Grab"
            },
            "Snake Prairie" : {
                "id" : 1500004,
                "mode" : "Bounty"
            },
            "Sneaky Fields" : {
                "author" : "Lex",
                "id" : 1500050,
                "mode" : "Brawl-Ball"
            },
            "Snow Fort" : {
                "id" : 1500058,
                "mode" : "Gem-Grab"
            },
            "Snowball Fight" : {
                "id" : 1500060,
                "mode" : "Gem-Grab"
            },
            "Snowy Siege" : {
                "id" : 1500062,
                "mode" : "Gem-Grab"
            },
            "Some Assembly Required" : {
                "id" : 1500098,
                "mode" : "Siege"
            },
            "Sparring Match" : {
                "author" : "Binnyboy",
                "id" : 1500128,
                "mode" : "Siege"
            },
            "Split Second" : {
                "id" : 1500074,
                "mode" : "Heist"
            },
            "Spring Trap" : {
                "author" : "freezeemilk",
                "id" : 1500117,
                "mode" : "Gem-Grab"
            },
            "Spruce Up" : {
                "id" : 1500064,
                "mode" : "Gem-Grab"
            },
            "Steel Junction" : {
                "id" : 1500029,
                "mode" : "Robo-Rumble"
            },
            "Stock Crash" : {
                "author" : "Frep",
                "id" : 1500140,
                "mode" : "Gem-Grab"
            },
            "Stone Fort" : {
                "id" : 1500089,
                "mode" : "Gem-Grab"
            },
            "Stormy Plains" : {
                "id" : 1500095,
                "mode" : "Showdown"
            },
            "Straight Shot" : {
                "author" : "Binnyboy",
                "id" : 1500129,
                "mode" : "Siege"
            },
            "Sunny Soccer" : {
                "author" : "Chief Pekka",
                "id" : 1500144,
                "mode" : "Brawl-Ball"
            },
            "Sunstroke" : {
                "author" : "Justin W.",
                "id" : 1500149,
                "mode" : "Bounty"
            },
            "Super Stadium" : {
                "author" : "Mordeus",
                "id" : 1500051,
                "mode" : "Brawl-Ball"
            },
            "Superstar" : {
                "author" : "Mordeus",
                "id" : 1500135,
                "mode" : "Showdown"
            },
            "Table Flip" : {
                "id" : 1500066,
                "mode" : "Big-Game"
            },
            "Team Day" : {
                "author" : "OwenReds",
                "id" : 1500119,
                "mode" : "Big-Game"
            },
            "Temple Ruins" : {
                "id" : 1500000,
                "mode" : "Bounty"
            },
            "Thousand Lakes" : {
                "author" : "Mordeus",
                "id" : 1500032,
                "mode" : "Showdown"
            },
            "Triple Dribble" : {
                "id" : 1500025,
                "mode" : "Brawl-Ball"
            },
            "Twist and Shoot" : {
                "author" : "AeroNautikks",
                "id" : 1500076,
                "mode" : "Heist"
            },
            "Undermine" : {
                "id" : 1500090,
                "mode" : "Gem-Grab"
            },
            "Vault Defenders" : {
                "id" : 1500068,
                "mode" : "Robo-Rumble"
            }
        }
        dataIO.save_json(f, maps)


def check_auth():
    c = dataIO.load_json(auth_path)
    if 'Token' not in c:
        c['Token'] = "Enter your BrawlAPI token here!"
    dataIO.save_json(auth_path, c)


def setup(bot):
    check_folder()
    check_file()
    n = BrawlStats(bot)
    bot.add_cog(n)
    bot.add_listener(n._new_message, 'on_message')

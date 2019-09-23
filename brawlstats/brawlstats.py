import discord
from discord.ext import commands
from .utils import checks
from __main__ import send_cmd_help, settings
from cogs.utils.dataIO import dataIO, fileIO
import os
import asyncio
import re
import aiohttp
import brawlstats
import time
from heapq import nlargest


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


class Auth:

    def __init__(self, path):
        self.auth = dataIO.load_json(path)

    async def addToken(self, key):
        """Add a BrawlAPI.cf Token"""
        self.auth['Token'] = key
        dataIO.save_json(auth_path, self.auth)

    async def Emojiset(self, method: int):
        """Add Emoji Verfication method"""
        self.auth['Emoji'] = method
        dataIO.save_json(auth_path, self.auth)

    async def Servset(self, no: int, server_id: int):
        """Add Emoji Servers method"""
        n = "s" + str(no)
        self.auth[n] = server_id
        dataIO.save_json(auth_path, self.auth)

    def getMethod(self):
        """Get emoji setup method Token"""
        return int(self.auth['Emoji'])

    def getToken(self):
        """Get brawlstars-api Token"""
        return self.auth['Token']


class BrawlStats:
    """Live statistics for Brawl Stars"""

    def __init__(self, bot):
        self.bot = bot
        self.location = 'data/brawlstats/settings.json'
        self.json = dataIO.load_json(self.location)
        self.auth = Auth(auth_path)
        self.tags = tags(tags_path)
        self.ldb = dataIO.load_json("data/brawlstats/ldb.json")
        self.brawl = brawlstats.Client(self.auth.getToken(), is_async=False)

    def update(self):
        self.brawl = brawlstats.Client(self.auth.getToken(), is_async=False)

    def emoji(self, name):
        """Emoji by name."""
        for emoji in self.bot.get_all_emojis():
            if emoji.name == name.replace(" ", "").replace("-", "").replace(".", ""):
                if emoji.id == "602540846922858537":
                    return "<a:endtime:602540846922858537>"
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
            "42": "Tick",
            "43": "8-Bit"
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
        if self.auth.getToken() is None:
            return await self.bot.say("The brawlAPI token has not been set.\nGet it from- https://brawlapi.cf/dashboard"
                                      "\nSet it using {}bs set token".format(ctx.prefix))

        member = member or ctx.message.author

        await self.bot.type()
        try:
            profiletag = await self.tags.getTag(member.id)
            profiledata = self.brawl.get_player(profiletag)
            await self.update_profile_withdata(member, profiledata)
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
        if self.auth.getToken() is None:
            return await self.bot.say("The brawlAPI token has not been set.\nGet it from- https://brawlapi.cf/dashboard"
                                      "\nSet it using {}bs set token".format(ctx.prefix))

        member = member or ctx.message.author

        await self.bot.type()
        try:
            profiletag = await self.tags.getTag(member.id)
            profiledata = self.brawl.get_player(profiletag)
            await self.update_profile_withdata(member, profiledata)
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
    async def events(self, ctx):
        """Gives List of Current and upcoming events"""
        if self.auth.getToken() is None:
            return await self.bot.say("The brawlAPI token has not been set.\nGet it from- https://brawlapi.cf/dashboard"
                                      "\nSet it using {}bs set token".format(ctx.prefix))

        await self.bot.type()
        image = "https://cdn.discordapp.com/avatars/517368847322447873/df58e404ffe235c686fe8008b29c2c34.png"
        try:
            events = self.brawl.get_events()
        except brawlstats.RequestError:
            return await self.bot.say("Error: cannot reach Brawl Stars Servers. Please try again later.")
        finemoji = self.emoji("endtime")
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
                    if coming.map_name is not None:
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
        if self.auth.getToken() is None:
            return await self.bot.say("The brawlAPI token has not been set.\nGet it from- https://brawlapi.cf/dashboard"
                                      "\nSet it using {}bs set token".format(ctx.prefix))

        member = member or ctx.message.author

        await self.bot.type()
        try:
            profiletag = await self.tags.getTag(member.id)
            profiledata = self.brawl.get_player(profiletag)
            await self.update_profile_withdata(member, profiledata)
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
        if self.auth.getToken() is None:
            return await self.bot.say("The brawlAPI token has not been set.\nGet it from- https://brawlapi.cf/dashboard"
                                      "\nSet it using {}bs set token".format(ctx.prefix))

        member = member or ctx.message.author

        await self.bot.type()
        try:
            profiletag = await self.tags.getTag(member.id)
            profiledata = self.brawl.get_player(profiletag)
            await self.update_profile_withdata(member, profiledata)
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
                        embed.add_field(name=title, value="Last Member", inline=False)
                    else:
                        embed1.add_field(name=title, value="Last Member", inline=False)
        await self.bot.say(embed=embed)
        if em2:
            await self.bot.say(embed=embed1)

    @bs.command(pass_context=True, aliases=["maps"])
    async def map(self, ctx, *, mapname):
        """View a Brawl Stars Map"""
        headers = {"map": mapname}
        async with aiohttp.ClientSession(headers=headers, loop=self.bot.loop) as session:
            r = await session.get('https://bs-map.glitch.me/')
            await session.close()
            res = await r.json()
        if not res["success"]:
            if res["error"] in ("Map Not Found", "No Map Specified"):
                notfoundembed = discord.Embed(color=0xFAA61A,
                                              description="Map `{}` could not be found.".format(mapname))
                return await self.bot.say(embed=notfoundembed)
            else:
                errorembed = discord.Embed(color=0xFAA61A,
                                           description="An Unexpected error occurred. Please try again later".format(mapname))
                return await self.bot.say(embed=errorembed)
        data = res["data"]
        mapname = data["map"]
        modelink = data["mode"]
        namelink = data["pagelink"]
        link = data["maplink"]
        embed = discord.Embed(color=0xFAA61A)
        embed.set_author(name=mapname,
                         icon_url=modelink,
                         url=namelink)
        count = 0
        recom = ""
        for brawler in data["brawlers"]:
            count += 1
            emo = self.emoji(brawler)
            if count % 3 == 0:
                recom += emo + "`" + brawler + "`\n"
            else:
                recom += emo + "`" + brawler + "` "
        embed.set_image(url=link)
        embed.add_field(name="Recommended Brawlers:", value=recom, inline=False)
        embed.set_footer(text=credits, icon_url=creditIcon)
        await self.bot.say(embed=embed)

    @bs.command(pass_context=True)
    async def leaderboard(self, ctx):
        """Shows server leaderboard for brawlstars"""
        if self.auth.getToken() is None:
            return await self.bot.say("The brawlAPI token has not been set.\nGet it from- https://brawlapi.cf/dashboard"
                                      "\nSet it using {}bs set token".format(ctx.prefix))

        await self.bot.type()
        user = ctx.message.author
        trosort = {}
        troinfo = {}
        server = user.server
        for member in server.members:
            try:
                if member.id in self.ldb:
                    profiledata = self.ldb[member.id]
                else:
                    await self.update_profile(member)
                    profiledata = self.ldb[member.id]
                trophies = profiledata["trophies"]
                name = profiledata["name"]
                trosort[member.id] = trophies
                troinfo[member.id] = {}
                troinfo[member.id]["name"] = name
                troinfo[member.id]["tag"] = profiledata["tag"]
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
                tromoji = self.getLeagueEmoji(tro)
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
            mod_role = settings.get_server_mod(server).lower()
            admin_role = settings.get_server_admin(server).lower()
            role = discord.utils.find(lambda r: r.name.lower() in (mod_role, admin_role), author.roles)
            if role is not None:
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

    @bs.group(pass_context=True, no_pm=True)
    async def set(self, ctx):
        """Setup And Manage This BS Cog."""
        if str(ctx.invoked_subcommand) == "bs set":
            await send_cmd_help(ctx)

    @set.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(administrator=True)
    async def token(self, ctx, key: str):
        """Input your BrawlStars API Token. Get it from brawlapi.cf"""
        key = str(key)
        brawlcheck = brawlstats.Client(key, is_async=False)
        try:
            brawlcheck.get_events()
        except brawlstats.ServerError or brawlstats.MaintenanceError or brawlstats.UnexpectedError:
            return await self.bot.say("BrawlAPI Server is down. Try again later.")
        except brawlstats.Unauthorized:
            return await self.bot.say("The TOKEN- ```{}``` you entered is invalid.".format(key))
        await self.auth.addToken(str(key))
        await self.bot.say("BrawlAPI Token set -\n```" + key + "```")
        self.update()

    @set.command(name="emoji", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(administrator=True)
    async def _set_emoji(self, ctx):
        """You can Setup The emojis For this COG by this command."""
        check1, check2, check3 = False, False, False
        for serv in self.bot.servers:
            if serv.id == "581069387512020995":
                check1 = True
            if serv.id == "603177745823957012":
                check2 = True
            if serv.id == "572762862980825089":
                check3 = True
        if check1 and check2 and check3:
            await self.auth.Emojiset(1)
            return await self.bot.say("I am already set up. I am in the emoji server.")
        fch = self.auth.getMethod()
        if fch == 0:
            pass
        else:
            return await self.bot.say("I am already set up. IF the cog is having any problem do {}bs set error".format(ctx.prefix))
        user = ctx.message.author
        server = user.server
        servno = len(self.bot.servers)
        if servno <= 7:
            out = "You can Use This Option"
        else:
            out = "Your bot cannot make more servers so you cannot use this Option."
        embed = discord.Embed(color=0xFAA61A, title="Emojis Setup Menu", description="Menu to Setup Emojis for thiis BS Cog.")
        embed.set_footer(text=credits, icon_url=creditIcon)
        embed.add_field(name=":one: Option 1", value="**You Can Join Our Server For The Emojis.\n"
                                                     "The Emojis will be auto-updated.\n**"
                                                     "(NOTE- You will have to give us our Bot Invite.\n"
                                                     "`IT WIL NOT BE OUR RESPONSIBILITY IF YOUR BOT JOINS ANY SERVER YOU DIDN'T WANT IT TO.`)"
                        , inline=False)
        embed.add_field(name=":two: Option 2", value="**The Bot can create 3 servers and add all emojis there.\n"
                                                     "The Emojis will be auto-updated every 24 hrs.\nYou can update these emojis manually also.**\n"
                                                     "(NOTE- You bot must not be in more than 7 Servers.\n"
                                                     "`YOUR BOT IS CURRENTLY IN {} SERVERS.`\n{})".format(str(servno), out)
                        , inline=False)
        embed.add_field(name=":three: Option 3", value="**You can create 3 servers yourself and bot will add all emojis there.\n"
                                                       "The Emojis will be auto-updated every 24 hrs.\nYou can update these emojis manually also.**\n"
                                                       "(Note- You must give bot perms to add emojis.\n"
                                                       "`Add the bot in those 3 servers and then provide the 3 server IDs properly.`)"
                        , inline=False)
        embed.add_field(name="😁 Reaction", value="React with :one: to use Option 1.\n"
                                                  "React with :two: to use Option 2.\n"
                                                  "React with :three: to use Option 3.\n"
                                                  "React with :x: to Cancel."
                        , inline=False)
        msg = await self.bot.say(embed=embed)
        emojis = []
        blo = chr(8419)
        num = [49, 50, 51]
        for n in num:
            ie = chr(n)
            emojis.append(ie + blo)
        emojis.append("❌")
        for emoji in emojis:
            await self.bot.add_reaction(message=msg, emoji=emoji)
        res = await self.bot.wait_for_reaction(emojis, user=user, timeout=90, message=msg)
        if res is None:
            return await self.bot.say("You took too long to react. Exiting Emoji Setup Process.")
        react = res.reaction
        recno = emojis.index(react.emoji) + 1
        if recno == 4:
            return await self.bot.say("Ok. Cancelling Emoji Setup Process.")
        elif recno == 1:
            return await self.bot.say("Ok. Join This Server- https://discord.gg/jQp52Ew ."
                                      "```Rest Of the Steps Will be explained there.```")
        elif recno == 2:
            if servno > 7:
                return await self.bot.say("Your bot is in more than 7 servers so you cannot use this option.")
            await self.bot.say("The bot will Create 3 Servers and add all the emojis there.\n"
                               "Type Cancel within 30 seconds to cancel. Else Bot will proceed.\n"
                               "Type Yes TO proceed immediately.")

            def check(mesg):
                return mesg.content.lower == "cancel" or "yes"
            reply = await self.bot.wait_for_message(author=user, check=check, timeout=30)
            if reply is None:
                pass
            elif reply.content.lower == "cancel":
                return await self.bot.say("Ok. Cancelling Emoji Setup Process.")
            await self.bot.say("Ok Creating Servers...")
            s1 = await self.bot.create_server(name="BS Emojis 1")
            s2 = await self.bot.create_server(name="BS Emojis 2")
            s3 = await self.bot.create_server(name="BS Emojis 3")
            c1 = await self.bot.create_channel(s1, name="general")
            inv1 = await self.bot.create_invite(c1)
            await self.bot.say("Server 1 (BS Emojis 1) Invite - " + inv1.url)
            c2 = await self.bot.create_channel(s2, name="general")
            inv2 = await self.bot.create_invite(c2)
            await self.bot.say("Server 2 (BS Emojis 2) Invite - " + inv2.url)
            c3 = await self.bot.create_channel(s3, name="general")
            inv3 = await self.bot.create_invite(c3)
            await self.bot.say("Server 3 (BS Emojis 3) Invite - " + inv3.url)
            self.clone()
            toadd = dataIO.load_json("data/brawlstats/Emojis/emoji.json")
            e1 = toadd[0]
            for emo in e1:
                h = emo.split(".")
                ext = "." + h[-1]
                nm = emo.replace(ext, "")
                path = "data/brawlstats/Emojis/BS Emotes 1/" + emo
                with open(path, "rb") as image:
                    im = image.read()
                    await self.bot.create_custom_emoji(s1, name=nm, image=im)
            await self.bot.say("Server 1 setup complete.")
            e2 = toadd[1]
            for emo in e2:
                h = emo.split(".")
                ext = "." + h[-1]
                nm = emo.replace(ext, "")
                path = "data/brawlstats/Emojis/BS Emotes 2/" + emo
                with open(path, "rb") as image:
                    im = image.read()
                    await self.bot.create_custom_emoji(s2, name=nm, image=im)
            await self.bot.say("Server 2 setup complete.")
            e3 = toadd[2]
            for emo in e3:
                h = emo.split(".")
                ext = "." + h[-1]
                nm = emo.replace(ext, "")
                path = "data/brawlstats/Emojis/BS Emotes 3/" + emo
                with open(path, "rb") as image:
                    im = image.read()
                    await self.bot.create_custom_emoji(s3, name=nm, image=im)
            await self.bot.say("Server 3 setup complete.")
            await self.auth.Servset(1, s1.id)
            await self.auth.Servset(2, s2.id)
            await self.auth.Servset(3, s3.id)
            await self.bot.say("Emojis have been setup. You can now use the bs cog properly.")
        elif recno == 3:
            botid = self.bot.user.id
            await self.bot.say("Add the bot the 1st server and then send The Server ID.")
            reply1 = await self.bot.wait_for_message(author=user, timeout=90)
            if reply1 is None:
               return await self.bot.say("You took too long to answer. Cancelling process.")
            if reply1.content.isnumeric():
                servid = reply1.content
                ch1 = False
                for servers in self.bot.servers:
                    if servers.id == servid:
                        botinserv = servers.get_member(botid)
                        if len(servers.emojis) > 0:
                            return await self.bot.say("That server already has some emojis.")
                        perms = botinserv.server_permissions
                        if perms.administrator or perms.manage_emojis or servers.owner.id == botid:
                            s1 = servers
                            ch1 = True
                            break
                        else:
                            return await self.bot.say("I dont have permissions to add emojis in that server.")
                if ch1:
                    pass
                else:
                    return await self.bot.say("Either the Server Id is invalid or I am not in that server.")
            else:
                return await self.bot.say("The Server ID is invalid.")
            await self.bot.say("Add the bot the 2nd server and then send The Server ID.")
            reply2 = await self.bot.wait_for_message(author=user, timeout=90)
            if reply2 is None:
                return await self.bot.say("You took too long to answer. Cancelling process.")
            if reply2.content.isnumeric():
                servid = reply2.content
                ch2 = False
                for servers in self.bot.servers:
                    if servers.id == servid:
                        botinserv = servers.get_member(botid)
                        if len(servers.emojis) > 0:
                            return await self.bot.say("That server already has some emojis.")
                        perms = botinserv.server_permissions
                        if perms.administrator or perms.manage_emojis or servers.owner.id == botid:
                            s2 = servers
                            ch2 = True
                        else:
                            return await self.bot.say("I dont have permissions to add emojis in that server.")
                if ch2:
                    pass
                else:
                    return await self.bot.say("Either the Server Id is invalid or I am not in that server.")
            else:
                return await self.bot.say("The Server ID is invalid.")
            await self.bot.say("Add the bot the 3rd server and then send The Server ID.")
            reply3 = await self.bot.wait_for_message(author=user, timeout=90)
            if reply3 is None:
                return await self.bot.say("You took too long to answer. Cancelling process.")
            if reply3.content.isnumeric():
                servid = reply3.content
                ch3 = False
                for servers in self.bot.servers:
                    if servers.id == servid:
                        botinserv = servers.get_member(botid)
                        if len(servers.emojis) > 0:
                            return await self.bot.say("That server already has some emojis.")
                        perms = botinserv.server_permissions
                        if perms.administrator or perms.manage_emojis or servers.owner.id == botid:
                            s3 = servers
                            ch3 = True
                        else:
                            return await self.bot.say("I dont have permissions to add emojis in that server.")
                if ch3:
                    pass
                else:
                    return await self.bot.say("Either the Server Id is invalid or I am not in that server.")
            else:
                return await self.bot.say("The Server ID is invalid.")
            self.clone()
            toadd = dataIO.load_json("data/brawlstats/Emojis/emoji.json")
            e1 = toadd[0]
            for emo in e1:
                h = emo.split(".")
                ext = "." + h[-1]
                nm = emo.replace(ext, "")
                path = "data/brawlstats/Emojis/BS Emotes 1/" + emo
                with open(path, "rb") as image:
                    im = image.read()
                    await self.bot.create_custom_emoji(s1, name=nm, image=im)
            await self.bot.say("Server 1 setup complete.")
            e2 = toadd[1]
            for emo in e2:
                h = emo.split(".")
                ext = "." + h[-1]
                nm = emo.replace(ext, "")
                path = "data/brawlstats/Emojis/BS Emotes 2/" + emo
                with open(path, "rb") as image:
                    im = image.read()
                    await self.bot.create_custom_emoji(s2, name=nm, image=im)
            await self.bot.say("Server 2 setup complete.")
            e3 = toadd[2]
            for emo in e3:
                h = emo.split(".")
                ext = "." + h[-1]
                nm = emo.replace(ext, "")
                path = "data/brawlstats/Emojis/BS Emotes 3/" + emo
                with open(path, "rb") as image:
                    im = image.read()
                    await self.bot.create_custom_emoji(s3, name=nm, image=im)
            await self.bot.say("Server 3 setup complete.")
            await self.auth.Servset(1, s1.id)
            await self.auth.Servset(2, s2.id)
            await self.auth.Servset(3, s3.id)
            await self.bot.say("Emojis have been setup. You can now use the bs cog properly.")

    @set.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(administrator=True)
    async def error(self, ctx):
        """Command for handling any sort of error in bs set emoji.(WIP)"""
        user = ctx.message.author
        check1, check2, check3 = False, False, False
        for serv in self.bot.servers:
            if serv.id == "581069387512020995":
                check1 = True
            if serv.id == "603177745823957012":
                check2 = True
            if serv.id == "572762862980825089":
                check3 = True
        if check1 and check2 and check3:
            await self.auth.Emojiset(1)
            return await self.bot.say("I am in the emoji servers. If there is any problem Send it here- https://discord.gg/jQp52Ew <#607476781867466764>")
        fch = self.auth.getMethod()
        if fch == 0:
            msg = await self.bot.say("First Setup the Emojis using `{}bs set emoji`. If you have set up the emojis already and then facing problems react with ✅.".format(ctx.prefix))
            await self.bot.add_reaction(message=msg, emoji="✅")
            res = await self.bot.wait_for_reaction("✅", user=user, timeout=90, message=msg)
            if res is None:
                return
            else:
                pass
        embed = discord.Embed(color=0xFAA61A, title="Emojis Error Menu", description="Menu to Handle Error in set emoji for thiis BS Cog.")
        embed.set_footer(text=credits, icon_url=creditIcon)
        embed.add_field(name=":one: Option 1", value="Emojis are not auto updating. You also manually update emojis using this method.\n"
                                                     "(Emojis in your bot are updated every week but we may be late to update them.)"
                        , inline=False)
        embed.add_field(name=":two: Option 2", value="The emoji servers Got deleted.", inline=False)
        embed.add_field(name=":three: Option 3", value="", inline=False)
        embed.add_field(name="😁 Reaction", value="React with :one: to use Option 1.\n"
                                                  "React with :two: to use Option 2.\n"
                                                  "React with :three: to use Option 3.\n"
                                                  "React with :x: to Cancel."
                        , inline=False)
        msg = await self.bot.say(embed=embed)

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
                            await self.bot.delete_message(message)
                            embed = discord.Embed(title=title, url=link, description=tag, color=0xff0000)
                            embed.set_footer(text=user, icon_url=icon)
                            await self.bot.send_message(channel, embed=embed)

    async def update_ldb(self):
        while self is self.bot.get_cog("BrawlStats"):
            start = time.time()
            for server in self.bot.servers:
                await self.update_server_ldb(server)
            end = time.time()
            if (end - start) >= 3600:
                wait = 0
            else:
                wait = 3600 - (end - start)
            await asyncio.sleep(wait)

    async def update_server_ldb(self, server):
        for member in server.members:
            await self.update_profile(member)
            await asyncio.sleep(0.4)

    async def update_profile(self, member):
        try:
            profiletag = await self.tags.getTag(member.id)
            profiledata = self.brawl.get_player(profiletag)
            trophies = profiledata.trophies
            name = profiledata.name
            tag = profiledata.tag
            pdata = {"name": name,
                     "tag": tag,
                     "trophies": trophies}
            self.ldb[member.id] = pdata
            self.save_system()
        except KeyError:
            pass
        except brawlstats.RateLimitError:
            await asyncio.sleep(0.4)
            await self.update_profile(member)
        except brawlstats.MaintenanceError or brawlstats.ServerError:
            return

    async def update_profile_withdata(self, member, profiledata):
        trophies = profiledata.trophies
        name = profiledata.name
        tag = profiledata.tag
        pdata = {"name": name,
                 "tag": tag,
                 "trophies": trophies}
        self.ldb[member.id] = pdata
        self.save_system()

    def save_system(self):
        dataIO.save_json('data/brawlstats/ldb.json', self.ldb)

    def clone(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        rlpath = os.getcwd()
        path = str(dir_path).replace("\\cogs", "") + "\\data\\brawlstats"
        os.chdir(path)
        os.system("git clone https://github.com/Weirdo914/Emojis.git")
        os.chdir(rlpath)

    def delclone(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        rlpath = os.getcwd()
        path = str(dir_path).replace("\\cogs", "") + "\\data\\brawlstats"
        os.chdir(path)
        try:
            os.rmdir("Emojis")
        except:
            pass
        os.chdir(rlpath)
        self.clone()

    def update(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        rlpath = os.getcwd()
        path = str(dir_path).replace("\\cogs", "") + "\\data\\brawlstats\\Emojis"
        os.chdir(path)
        os.system("git fetch && git pull")
        os.chdir(rlpath)

    async def update_emojis(self):
        while self is self.bot.get_cog("BrawlStats"):
            self.update()
            await asyncio.sleep(86400)


def check_folder():
    if not os.path.exists('data/brawlstats'):
        os.makedirs('data/brawlstats')


def check_file():
    if not fileIO(tags_path, "check"):
        print("Creating empty tags.json...")
        fileIO(tags_path, "save", {"0": {"tag": "DONOTREMOVE"}})

    if not fileIO(auth_path, "check"):
        print("enter your BrawlAPI token in data/brawlstats/auth.json...")
        fileIO(auth_path, "save", {"Token": None,
                                   "Emoji": 0,
                                   "s1": None,
                                   "s2": None,
                                   "s3": None})

    f = 'data/brawlstats/settings.json'
    if dataIO.is_valid_json(f) is False:
        dataIO.save_json(f, {})

    f = 'data/brawlstats/ldb.json'
    if dataIO.is_valid_json(f) is False:
        dataIO.save_json(f, {})


def check_auth():
    c = dataIO.load_json(auth_path)
    if 'Token' not in c:
        c['Token'] = "Enter your BrawlAPI token here!"
    dataIO.save_json(auth_path, c)


def setup(bot):
    check_folder()
    check_file()
    n = BrawlStats(bot)
    loop = asyncio.get_event_loop()
    loop.create_task(n.update_ldb())
    if Auth(auth_path).getMethod() > 1:
        loop2 = asyncio.get_event_loop()
        loop2.create_task(n.update_emojis())
    bot.add_cog(n)
    bot.add_listener(n._new_message, 'on_message')

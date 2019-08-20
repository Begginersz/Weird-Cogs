import discord
import requests
from discord.ext import commands

icon = "https://cdn3.iconfinder.com/data/icons/avatars-15/64/_Ninja-2-512.png"
credit = "Cog by Weirdo914"


def embed(**kwargs):
    return discord.Embed(**kwargs).set_footer(
        text=credit,
        icon_url=icon
    )


class Fun:
    """Cog with some fun commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def meme(self):
        """Sends a random meme."""
        await self.bot.type()
        response = requests.get('https://apis.duncte123.me/meme')
        res = response.json()
        if res["success"] is False:
            await self.bot.say("Oops! An error occurred. Try Again Later.")
        else:
            data = res["data"]
            title = data["title"]
            url = data["url"]
            imageurl = data["image"]
            emb = embed(colour=0x00ff57, title=title, url=url)
            emb.set_image(url=imageurl)
            await self.bot.say(embed=emb)

    @commands.command(pass_context=True)
    async def cat(self):
        """Sends a random cat image."""
        await self.bot.type()
        response = requests.get('http://aws.random.cat/meow')
        res = response.json()
        if 'file' not in res:
            await self.bot.say("Oops! An error occurred. Try Again Later.")
        else:
            imageurl = res['file']
            emb = embed(colour=0x00ff57, title="Meow :heart_eyes_cat:")
            emb.set_image(url=imageurl)
            await self.bot.say(embed=emb)

    @commands.command(pass_context=True)
    async def dog(self):
        """Sends a random dog image."""
        await self.bot.type()
        response = requests.get('https://dog.ceo/api/breeds/image/random')
        res = response.json()
        if res["status"] != 'success':
            await self.bot.say("Oops! An error occurred. Try Again Later.")
        else:
            imageurl = res['message']
            emb = embed(colour=0x00ff57, title="Bork Bork! :dog:")
            emb.set_image(url=imageurl)
            await self.bot.say(embed=emb)


def setup(bot):
    bot.add_cog(Fun(bot))

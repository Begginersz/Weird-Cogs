import discord
from discord.ext import commands

class donate:
    """My custom cog that does stuff!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def donate(self):
        """This does stuff!"""

        #Your code will go here
        embed = discord.Embed(colour=0x00ff00)
        embed.add_field(name=":point_right:Donate money:point_left:", value="Support")
        embed.title = "Help support CRZA Esports"
        embed.set_footer(text="Bot by CRZA",  icon_url=https://cdn.discordapp.com/attachments/569495909294145536/583588075498635280/images_63_1.jpeg)
        await self.bot.say(content=mention, embed=embed)
def setup(bot):
    bot.add_cog(donate(bot))

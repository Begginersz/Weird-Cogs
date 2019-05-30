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
        embed = discord.Embed(title=Help support CRZA Esports, description = Support us, color = 0x00ff00)
        embed.set_author(name=CRZA)
        embed.add_field(name=: point_right:Donate money: point_left:, value = a href = "https://donatebot.io/checkout/567325025649033236?buyer=425991701681930260" Support < / a >, inline = True)
        embed.set_footer(text=Bot by CRZA, icon_url = https: // cdn.discordapp.com / attachments / 569495909294145536 / 583588075498635280 / images_63_1.jpeg)
        await self.bot.say(embed=embed)
def setup(bot):
    bot.add_cog(Mycog(bot))

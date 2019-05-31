import discord
from discord.ext import commands

icon="https://cdn3.iconfinder.com/data/icons/avatars-15/64/_Ninja-2-512.png"

class donate:
    """My custom cog that does stuff!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def donate(self):
        """This does stuff!"""

        #Your code will go here
        embed = discord.Embed(colour=0x00ff00)
        embed.add_field(name=":point_right:Donate money:point_left:", value="https://bit.ly/2EJK7sV")
        embed.title = "Help support CRZA Esports"
        embed.set_footer(text="Bot by Weirdo914",  icon_url=icon)
        await self.bot.say(embed=embed)
def setup(bot):
    bot.add_cog(donate(bot))

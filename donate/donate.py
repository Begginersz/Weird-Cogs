import discord
from discord.ext import commands

icon="https://www.google.com/url?sa=i&source=images&cd=&ved=2ahUKEwio3MH6l8XiAhUJQhoKHcstB0YQjRx6BAgBEAU&url=https%3A%2F%2Fwallpapersite.com%2Fcreative-graphics%2Firon-man-artwork-minimal-dark-background-hd-16834.html&psig=AOvVaw0xTosKvgQvPQnWo7j_xhkZ&ust=1559372102433402"

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

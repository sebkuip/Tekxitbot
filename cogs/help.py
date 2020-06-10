import discord
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # This is the bot instance, it lets us interact with most things

    @commands.command(help='Show this menu, how else would this show up?')
    async def help(self, ctx):
        embed = discord.Embed(title='Help menu', description='All the commands!', color=discord.Color.blurple())
        embed.add_field(name='***prefix***', value='*//*')
        for command in self.bot.commands:
            try:
                if await command.can_run(ctx):
                    embed.add_field(name=f'***{command.name}***', value=f'*{command.help}*', inline=False)
            except:
                pass
        await ctx.send(embed=embed)

    @commands.command(help='Shows info about the bot')
    async def info(self, ctx):
        embed = discord.Embed(title='Info menu', description='Info about the bot', color=discord.Color.blurple())
        embed.add_field(name='Creator', value=self.bot.get_user(234649992357347328).mention, inline=False)
        embed.add_field(name='Ping', value=str(round(self.bot.latency, 5) * 1000) + 'ms', inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))

import discord
from discord.ext import commands

from config import PREFIX


class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # This is the bot instance, it lets us interact with most things

    @commands.command(help='Gets the custom help commands')
    async def chelp(self, ctx, name='help'):
        name = name.lower()
        with open(f'cogs/chelp/{name}.txt', 'r') as f:
            message = f.read()
        await ctx.send(f'{message}')
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(CustomCommands(bot))

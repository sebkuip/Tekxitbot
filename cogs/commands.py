import random
import typing

import discord
from discord.ext import commands


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # This is the bot instance, it lets us interact with most things

    @commands.command(help='Shows the latency of the bot')
    async def ping(self, ctx):
        await ctx.send(f'My ping is ' + str(round(self.bot.latency, 5) * 1000) + 'ms')

    @commands.command(help='Allows you to talk as the bot in the specified channel or current if non is specified')
    @commands.has_permissions(administrator=True)
    async def echo(self, ctx, channel: typing.Optional[discord.TextChannel] = None, *, text):
        if channel is None:
            channel = ctx.channel
        await channel.send(text)
        await ctx.message.delete()

    @commands.command(
        help='Allows you to send an embed using the bot in the specified channel or current if none is specified')
    @commands.has_permissions(manage_messages=True)
    async def embed(self, ctx, channel: typing.Optional[discord.TextChannel] = None, *, text):
        if channel is None:
            channel = ctx.channel
        embed = discord.Embed()
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        embed.add_field(name=f'**Said**', value=text)
        await channel.send(embed=embed)
        await ctx.message.delete()

    @commands.command(help='Stops the bot from running. **WARNING: DOES NOT AUTO RESTART**')
    @commands.has_permissions(administrator=True)
    async def stop(self, ctx):
        # good night
        await ctx.send('Shutting down')
        print(f'shutting down')
        await self.bot.close()
        input('Shutdown complete, press enter to close this window')

    @commands.command(help='Pick a random person!')
    @commands.has_permissions(mention_everyone=True)
    async def someone(self, ctx):
        members = ctx.guild.members
        embed = discord.Embed(title=f'@someone', description=random.choice(members).mention())
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Commands(bot))

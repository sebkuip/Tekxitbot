import random
import typing

import discord
import wikia
from discord.ext import commands


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # This is the bot instance, it lets us interact with most things

    @commands.command(help='Shows the latency of the bot')
    async def ping(self, ctx):
        await ctx.send(f'My ping is ' + str(round(self.bot.latency, 5) * 1000) + 'ms')

    @commands.command(help='Allows you to talk as the bot in the specified channel or current if non is specified', aliases=['say',])
    @commands.has_permissions(administrator=True)
    async def echo(self, ctx, channel: typing.Optional[discord.TextChannel] = None, *, text):
        if channel is None:
            channel = ctx.channel
        await channel.send(text)
        await ctx.message.delete()

    @commands.command(help='Allows you to send an embed using the bot in the specified channel or current if none is specified')
    @commands.has_permissions(manage_messages=True)
    async def embed(self, ctx, channel: typing.Optional[discord.TextChannel] = None, *, text):
        if channel is None:
            channel = ctx.channel
        embed = discord.Embed()
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        embed.add_field(name=f'\u200b', value=text)
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
        embed = discord.Embed(title=f'@someone', description=random.choice(members).mention)
        await ctx.send(embed=embed)

    @commands.command(help='Searched the Tekxit wiki')
    async def wiki(self, ctx, *, wiki=None):
        if not wiki:
            await ctx.send('The Tekxit wiki can be found at:\nhttps://tekxit.fandom.com/wiki/Tekxit_Wiki')
        else:
            async with ctx.typing():
                try:
                    summary = wikia.summary("tekxit", wiki)
                    page = wikia.page("tekxit", wiki)
                    link = page.url
                    embed = discord.Embed(title=f'{wiki} | Tekxit wiki', color=discord.Color.blurple())
                    embed.add_field(name=link, value=summary)
                    embed.set_footer(text='If you want to edit this page, click the link at the top of this message')
                    await ctx.send(embed=embed)
                except Exception as e:
                    raise e

    @commands.command(help='show someone\'s profile picture', name='pfp')
    async def profilepicture(self, ctx, member: typing.Optional[typing.Union[discord.User, discord.Object]]):
        if not member:
            member = ctx.author
        elif isinstance(member, discord.Object):
            member = self.bot.get_user(member.id) or await self.bot.fetch_user(member.id)
        pic = member.avatar_url
        await ctx.send(pic)

    @commands.command(help='Make a poll with yes or no, or up to 10 custom answers')
    async def poll(self, ctx, question, *options):
        if len(options) == 1 or len(options) > 10:
            await ctx.send("Please enter a valid number of arguments")
            return

        if len(options) == 0:
            answers = ["Yes", "No"]
        else:
            answers = [answer for answer in options]
        
        embed = discord.Embed(title=question, color=discord.Color.blurple())
        for i, answer in enumerate(answers):
            embed.add_field(name=f"**{i+1}**", value=answer, inline=False)

        message = await ctx.send(embed=embed)
        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        for i in range(len(answers)):
            await message.add_reaction(reactions[i])
        


def setup(bot):
    bot.add_cog(Commands(bot))

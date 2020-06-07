import asyncio
import discord
from discord.ext import commands
from config import *


class Members(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # This is the bot instance, it lets us interact with most things

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(JOINCHANNEL)
        if channel is not None:
            embed = discord.Embed(title=None, description=':heart: Welcome ' + member.mention + '!\nWe now have ' + str(
                self.bot.get_guild(
                    GUILDID).member_count) + 'members\nBe sure to check <#606795102987223051> \nHope you enjoy your '
                                             'stay :Heart3:',
                                  colour=discord.Color.dark_purple())
            await channel.send(embed=embed)
            message = await channel.send(member.mention)
            await message.delete()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = self.bot.get_channel(GUILDID)
        if channel is not None:
            await channel.send(str(member) + ' just left the server :slight_frown:')


def setup(bot):
    bot.add_cog(Members(bot))

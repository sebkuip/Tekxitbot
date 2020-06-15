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
            emoji = discord.utils.get(channel.guild.emojis, name='Heart3')
            message = await channel.send(f'> <:R3:721722986339631234><:R2:721722986159407115><:R4:721722986356539472>**__New Member__**<:R5:721722986373185646><:R3:721722986339631234><:R2:721722986159407115>\n'
                                         f'> <:R1:721722971164508190> Welcome {member.mention}!\n'
                                         f'> <:R1:721722971164508190> We now have** {self.bot.get_guild(GUILDID).member_count} **members!\n'
                                         f'> <:R1:721722971164508190> Be sure to check <#606795102987223051>\n'
                                         f'> <:R1:721722971164508190> Hope you enjoy your stay! <:Heart3:655160924134440990>')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = self.bot.get_channel(JOINCHANNEL)
        if channel is not None:
            await channel.send(f'> <:R6:721990379158896680> ***{member}***  just left the server :slight_frown:')


def setup(bot):
    bot.add_cog(Members(bot))

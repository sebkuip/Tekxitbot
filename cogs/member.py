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
            message = await channel.send(f'>>> :heart: Welcome {member.mention}!\n'
                                         f'We now have {self.bot.get_guild(GUILDID).member_count} '
                                         f'members '
                                         f'\nBe sure to check <#606795102987223051>\n'
                                         f'Hope you enjoy your stay {emoji}')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = self.bot.get_channel(JOINCHANNEL)
        if channel is not None:
            await channel.send(f'{member} just left the server :slight_frown:')


def setup(bot):
    bot.add_cog(Members(bot))

import discord
from discord.ext import commands

from config import *

class Pinboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pinemoji = None

    @commands.Cog.listener
    async def on_raw_reaction_add(self, payload):
        guild = await self.bot.get_guild(payload.guild_id)
        pinchannel = await guild.get_channel(PINCHANNEL)
        pincheckchannel = await guild.get_channel(PINCHECKCHANNEL)

        if not self.pinemoji:
            await guild.fetch_emoji(PINEMOJI)

        message = await pincheckchannel.fetch_message(payload.message_id)

        reactions = message.reactions

        counter = 0

        for reaction in reactions:
            if reaction.emoji == self.pinemoji:
                counter+=1

        if counter < 3:
            return

        embed = discord.Embed(description=message.content)
        embed.set_author(name=payload.member.name, icon_url=payload.member.avatar_url)
        await pinchannel.send(embed=embed)
        

def setup(bot):
    bot.add_cog(Pinboard(bot))
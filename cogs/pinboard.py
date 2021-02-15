import discord
from discord.ext import commands

from config import *

class Pinboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pinemoji = None

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        pinchannel = guild.get_channel(PINCHANNEL)
        pincheckchannel = guild.get_channel(PINCHECKCHANNEL)

        if not self.pinemoji:
            self.pinemoji = await guild.fetch_emoji(PINEMOJI)

        if payload.emoji == self.pinemoji:

            message = await pincheckchannel.fetch_message(payload.message_id)

            reactions = message.reactions

            for reaction in reactions:
                if reaction.emoji == self.pinemoji:
                    counter = reaction.count

            if counter > 1:
                return

            embed = discord.Embed(description=message.jump_url)
            embed.add_field(name=message.author.name, value=message.content)
            await pinchannel.send(embed=embed)
        

def setup(bot):
    bot.add_cog(Pinboard(bot))
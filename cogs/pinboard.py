import discord
from discord.ext import commands
import datetime

from config import *

class Pinboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pinemoji = None
        self.lastmessage = 0

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        pinchannel = guild.get_channel(PINCHANNEL)
        pincheckchannel = guild.get_channel(PINCHECKCHANNEL)

        if not self.pinemoji:
            self.pinemoji = await guild.fetch_emoji(PINEMOJI)

        if payload.emoji == self.pinemoji:

            message = await pincheckchannel.fetch_message(payload.message_id)
            if not message.channel.id == PINCHECKCHANNEL:
                return
            else:
                await message.add_reaction(self.pinemoji)
                await message.add_reaction('✅')

            reactions = message.reactions

            for reaction in reactions:
                if (reaction.emoji == self.pinemoji and reaction.count > 1) or reaction.emoji == '✅' or self.lastmessage == payload.message_id:
                    return

            embed = discord.Embed(description=message.content)
            embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
            embed.set_footer(text=f"Sent at: {message.created_at.strftime('%a %Y-%m-%d %H:%M')}")
            embed.add_field(name="Link:", value=f"[jump]({message.jump_url})")
            await pinchannel.send(embed=embed)

            self.lastmessage = payload.message_id
        

def setup(bot):
    bot.add_cog(Pinboard(bot))
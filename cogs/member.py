from discord.ext import commands

from config import *


class Members(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # This is the bot instance, it lets us interact with most things

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # add to levels db
        async with self.bot.pool.acquire() as con:
            await con.execute(
                "INSERT INTO levels(uid, xp, level, message_count) VALUES($1, $2, $3, $4) ON CONFLICT (uid) DO NOTHING",
                member.id,
                0,
                0,
                0,
            )
        # add a few roles to the member on joining
        roles = []
        for roleid in JOINROLES:
            role = member.guild.get_role(roleid)
            roles.append(role)
        await member.add_roles(*roles)

        self.joinchannel = member.guild.get_channel(JOINCHANNEL)

        # Join message
        await self.joinchannel.send(
            f"> **__New Member__**\n "
            f"> Welcome {member.mention}!\n"
            f"> We now have** {self.bot.get_guild(GUILDID).member_count} **members!\n "
            f"> Be sure to check <#606795102987223051>\n"
            f"> Hope you enjoy your stay! <:Heart3:655160924134440990>"
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # Leave message
        self.joinchannel = member.guild.get_channel(JOINCHANNEL)
        await self.joinchannel.send(
            f"> ***{member}***  just left the server :slight_frown:"
        )


def setup(bot):
    bot.add_cog(Members(bot))

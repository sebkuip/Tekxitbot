import discord
import asyncpg
from discord.ext import commands
import re
import datetime
import typing
import asyncio

from discord.ext.commands.errors import BadArgument

from config import *


# banned user converter. From R.Danny by Danny (Raptzz). https://github.com/Rapptz/RoboDanny
class BannedMember(commands.Converter):
    async def convert(self, ctx, argument):
        if argument.isdigit():
            member_id = int(argument, base=10)
            try:
                return await ctx.guild.fetch_ban(discord.Object(id=member_id))
            except discord.NotFound:
                raise commands.BadArgument(
                    'This member has not been banned before.') from None

        ban_list = await ctx.guild.bans()
        entity = discord.utils.find(
            lambda u: str(u.user) == argument, ban_list)

        if entity is None:
            raise commands.BadArgument(
                'This member has not been banned before.')
        return entity


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # This is the bot instance, it lets us interact with most things

    # Anti character spam
    @commands.Cog.listener()
    async def on_message(self, m):
        if not m.guild or m.author.bot or isinstance(m.author, discord.User):
            return
        if m.author.permissions_in(m.channel).manage_messages:
            return
        content = re.sub(r"[a-zA-Z_0-9\s]",r"", m.content)
        for letter in set(content):
            if content.count(letter) > SPAMTRESHOLD:
                await m.delete()

                embed = discord.Embed(color=0xFF0000)
                embed.set_author(name=str(m.author), icon_url=m.author.avatar_url)
                embed.add_field(name="Text", value=discord.utils.escape_markdown(m.content))
                embed.set_footer(text=f"Deleted at {datetime.datetime.utcnow().strftime('%a %b %d %H:%M:%S %Z')}")
                await self.bot.logchannel.send(f"Found spam in <#{m.channel.id}> by <@{m.author.id}>:", embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):

        muterole = member.guild.get_role(MUTEDROLE)

        async with self.bot.pool.acquire() as con:
            mutedata = await con.fetch("SELECT active FROM mutes where uid = $1", member.id)
            tempmutedata = await con.fetch("SELECT endtime from tempmutes where uid  = $1", member.id)
            
            if mutedata:
                for mute in mutedata:
                    if mute["active"]:
                        await member.add_roles(muterole)
                        await self.bot.logchannel.send(f"user {member.mention} ({member.id}) joined with active mute.")
                        return
                
            elif tempmutedata:
                for mute in tempmutedata:
                    if mute["endtime"] < datetime.datetime.utcnow():
                        await member.add_roles(muterole)
                        await self.bot.logchannel.send(f"user {member.mention} ({member.id}) joined with active mute.")
                        return


    @commands.command(help='Kicks the specified member for the specified reason')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await ctx.message.delete()
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot kick this person")
            return
        embed = discord.Embed(
            title=f'You have been kicked from {ctx.guild.name}', color=discord.Color.green())
        if reason:
            embed.add_field(name='Reason:', value=f'{reason}', inline=False)
        embed.add_field(name='\u200b', value=f'If you have questions about this action, or would like '
                                             f'to appeal it. Please contact the staff team. '
                                             f'You were warned by {ctx.author.mention}', inline=False)
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            await ctx.send('Could not send DM to user')
        await member.kick(reason=reason)
        async with self.bot.pool.acquire() as con:
            try:
                result = await con.fetchrow("INSERT INTO kicks(uid, executor, timedate, reason) VALUES($1, $2, "
                                                    "CURRENT_TIMESTAMP(1), $3) RETURNING kickid", member.id, ctx.author.id, reason)
                kickid = result[0]
            except Exception as error:
                print(error)
        if reason:
            embed = discord.Embed(title=f' ', description=f' ',
                                  color=discord.Color.green())
            embed.set_footer(
                text=f'Action performed by {ctx.author} | Case {kickid}')
            embed.set_author(name=f'Case {kickid} | Kick | {member}')
            embed.add_field(name=f'Reason', value=f'{reason}', inline=False)
        else:
            embed = discord.Embed(title=f' ', description=f' ',
                                  color=discord.Color.green())
            embed.set_footer(
                text=f'Action performed by {ctx.author} | Case {kickid}')
            embed.set_author(name=f'Case {kickid} | Kick | {member}')
        await ctx.send(embed=embed)
        await self.bot.logchannel.send(embed=embed)

    @commands.command(help='Bans the specified member for the specified reason')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: typing.Union[discord.Member, discord.User, discord.Object], *, reason=None):
        await ctx.message.delete()

        if isinstance(member, discord.Member):
            if member.top_role >= ctx.author.top_role:
                await ctx.send("You cannot ban this person")
                return
        else:
            member = member if isinstance(member, discord.User) else await self.bot.fetch_user(member.id)

        embed = discord.Embed(
            title=f'You have been banned from {ctx.guild.name}', color=discord.Color.green())
        if reason:
            embed.add_field(name='Reason:', value=f'{reason}', inline=False)
        embed.add_field(name='\u200b', value=f'If you have questions about this action, or would like '
                                             f'to appeal it. Please contact the staff team. '
                                             f'You were warned by {ctx.author.mention}', inline=False)
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            await ctx.send('Could not send DM to user')
        await ctx.guild.ban(member, reason=reason, delete_message_days=0)
        async with self.bot.pool.acquire() as con:
            try:
                result = await con.fetchrow("INSERT INTO bans(uid, executor, timedate, reason) VALUES($1, $2, "
                                                    "CURRENT_TIMESTAMP(1), $3) RETURNING banid", member.id, ctx.author.id, reason)
                banid = result[0]
            except Exception as error:
                print(error)

        embed = discord.Embed(title=f' ', description=f' ',
                              color=discord.Color.green())
        embed.set_footer(
            text=f'Action performed by {ctx.author} | Case {banid}')
        embed.set_author(name=f'Case {banid} | Ban | {member}')
        if reason:
            embed.add_field(name=f'Reason', value=f'{reason}', inline=False)

        await ctx.send(embed=embed)

        await self.bot.logchannel.send(embed=embed)

    @commands.command(help='Bans the specified member for the specified reason for a specified time')
    @commands.has_permissions(administrator=True)
    async def tempban(self, ctx, member: typing.Union[discord.Member, discord.User, discord.Object], time, *, reason=None):
        await ctx.message.delete()
        if isinstance(member, discord.Member):
            if member.top_role >= ctx.author.top_role:
                await ctx.send("You cannot ban this person")
                return
        else:
            member = member if isinstance(member, discord.User) else await self.bot.fetch_user(member.id)

        weeks = int((re.findall(r"(\d+)w", time) or "0")[0])
        days = int((re.findall(r"(\d+)d", time) or "0")[0])
        hours = int((re.findall(r"(\d+)h", time) or "0")[0])
        minutes = int((re.findall(r"(\d+)m", time) or "0")[0])

        timedelta = datetime.timedelta(
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes
        )
        endtime = datetime.datetime.utcnow() + timedelta

        embed = discord.Embed(title=f'You have been temporary banned from {ctx.guild.name}. You have been banned until {endtime}.',
                              color=discord.Color.green())
        if reason:
            embed.add_field(name='Reason:', value=f'{reason}', inline=False)
        embed.add_field(name='If you have questions:', value=f'If you have questions about this action, or would like '
                                                             f'to appeal it. Please contact the staff team. '
                                                             f'You were banned by {ctx.author.mention}', inline=False)
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            await ctx.send('Could not send DM to user')
        await ctx.guild.ban(member, reason=reason, delete_message_days=1)
        async with self.bot.pool.acquire() as con:
            try:
                result = await con.fetchrow("INSERT INTO tempbans(uid, executor, timedate, endtime, reason) VALUES($1, $2, "
                                                    "CURRENT_TIMESTAMP(1), $3, $4) RETURNING banid", member.id, ctx.author.id, endtime, reason)
                banid = result[0]
            except Exception as error:
                print(error)

        embed = discord.Embed(title=f' ', description=f' ',
                              color=discord.Color.green())
        embed.set_footer(
            text=f'Action performed by {ctx.author} | Case {banid}')
        embed.set_author(name=f'Case {banid} | Temp ban | {member}')
        embed.add_field(name='End time', value=f'{endtime}', inline=False)
        if reason:
            embed.add_field(name=f'Reason', value=f'{reason}', inline=False)
        await ctx.send(embed=embed)
        await self.bot.logchannel.send(embed=embed)

    @commands.command(help='Unbans the specified member for the specified reason')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, entry: BannedMember, *, reason=None):
        await ctx.message.delete()
        embed = discord.Embed(
            title=f'You have been unbanned from {ctx.guild.name}', color=discord.Color.green())
        if reason:
            embed.add_field(name='Reason:', value=f'{reason}', inline=False)
        try:
            await entry[1].send(embed=embed)
        except discord.Forbidden:
            await ctx.send('Could not send DM to user')

        embed = discord.Embed(title=f' ', description=f' ',
                              color=discord.Color.green())
        embed.set_footer(text=f'Action performed by {ctx.author}')
        embed.set_author(name=f'Unban | {entry[1]}')
        if reason:
            embed.add_field(name=f'Reason', value=f'{reason}', inline=False)

        await ctx.send(embed=embed)
        await self.bot.logchannel.send(embed=embed)
        await ctx.guild.unban(entry[1], reason=reason)

    @commands.command(help='Warns the user for the specified reason')
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: typing.Union[discord.Member, discord.User, discord.Object], *, reason=None):
        await ctx.message.delete()

        if isinstance(member, discord.Member):
            if member.top_role >= ctx.author.top_role:
                await ctx.send("You cannot warn this person")
                return
        else:
            member = member if isinstance(member, discord.User) else await self.bot.fetch_user(member.id)

        embed = discord.Embed(
            title=f'You have been warned in {ctx.guild.name}', color=discord.Color.green())
        if reason:
            embed.add_field(name='Reason:', value=f'{reason}', inline=False)
        embed.add_field(name='\u200b', value=f'If you have questions about this action, or would like '
                                             f'to appeal it. Please contact the staff team. '
                                             f'You were warned by {ctx.author.mention}', inline=False)
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            await ctx.send('Could not send DM to user')
        async with self.bot.pool.acquire() as con:
            try:
                result = await con.fetchrow("INSERT INTO warnings(uid, executor, timedate, reason) VALUES($1, "
                                                    "$2, CURRENT_TIMESTAMP(1), $3) RETURNING warnid", member.id, ctx.author.id, reason)
                warnid = result[0]
            except Exception as error:
                print(error)

        embed = discord.Embed(color=discord.Color.green())
        embed.set_footer(
            text=f'Action performed by {ctx.author} | Case {warnid}')
        embed.set_author(name=f'Case {warnid} | Warn | {member}')

        if reason:
            embed.add_field(name=f'Reason', value=f'{reason}', inline=False)

        await ctx.send(embed=embed)
        await self.bot.logchannel.send(embed=embed)

    @commands.command(help='Mutes the person', aliases=['stfu'])
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member, *, reason=None):
        await ctx.message.delete()
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot mute this person")
            return

        muterole = ctx.guild.get_role(MUTEDROLE)

        await member.add_roles(muterole)

        async with self.bot.pool.acquire() as con:
            muteid = await con.fetchrow("INSERT INTO mutes(uid, executor, timedate, reason, active) VALUES($1, $2, $3, $4, $5) RETURNING muteid", member.id, ctx.author.id, datetime.datetime.utcnow(), reason, True)
            muteid = muteid["muteid"]

        embed = discord.Embed(
            title=f'You have been muted in {ctx.guild.name}', color=discord.Color.green())
        if reason:
            embed.add_field(name='Reason:', value=f'{reason}', inline=False)
        embed.add_field(name='\u200b', value=f'If you have questions about this action, or would like '
                                             f'to appeal it. Please contact the staff team. '
                                             f'You were muted by {ctx.author.mention}', inline=False)
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            await ctx.send('Could not send DM to user')

        embed = discord.Embed(color=discord.Color.green())
        embed.set_footer(text=f'Action performed by {ctx.author}')
        embed.set_author(name=f'Case {muteid} | Mute | {member}')

        if reason:
            embed.add_field(name=f'Reason', value=f'{reason}', inline=False)

        await ctx.send(embed=embed)
        await self.bot.logchannel.send(embed=embed)
    
    @commands.command(help='mutes the specified member for the specified reason for a specified time')
    @commands.has_permissions(manage_messages=True)
    async def tempmute(self, ctx, member: typing.Union[discord.Member, discord.User, discord.Object], time, *, reason=None):
        await ctx.message.delete()
        if isinstance(member, discord.Member):
            if member.top_role >= ctx.author.top_role:
                await ctx.send("You cannot mute this person")
                return
        else:
            member = member if isinstance(member, discord.User) else await self.bot.fetch_user(member.id)

        if not member:
            raise commands.BadArgument("User was not found")

        weeks = int((re.findall(r"(\d+)w", time) or "0")[0])
        days = int((re.findall(r"(\d+)d", time) or "0")[0])
        hours = int((re.findall(r"(\d+)h", time) or "0")[0])
        minutes = int((re.findall(r"(\d+)m", time) or "0")[0])

        timedelta = datetime.timedelta(
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes
        )
        endtime = datetime.datetime.utcnow() + timedelta

        embed = discord.Embed(title=f'You have been temporary muted from {ctx.guild.name}. You have been muted until {endtime}.',
                              color=discord.Color.green())
        if reason:
            embed.add_field(name='Reason:', value=f'{reason}', inline=False)
        embed.add_field(name='If you have questions:', value=f'If you have questions about this action, or would like '
                                                             f'to appeal it. Please contact the staff team. '
                                                             f'You were muted by {ctx.author.mention}', inline=False)
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            await ctx.send('Could not send DM to user')

        muterole = ctx.guild.get_role(MUTEDROLE)
        await member.add_roles(muterole)

        async with self.bot.pool.acquire() as con:
            try:
                result = await con.fetchrow("INSERT INTO tempmutes(uid, executor, timedate, endtime, reason) VALUES($1, $2, "
                                                    "CURRENT_TIMESTAMP(1), $3, $4) RETURNING muteid", member.id, ctx.author.id, endtime, reason)
                muteid = result[0]
            except Exception as error:
                print(error)

        embed = discord.Embed(title=f' ', description=f' ',
                              color=discord.Color.green())
        embed.set_footer(
            text=f'Action performed by {ctx.author} | Case {muteid}')
        embed.set_author(name=f'Case {muteid} | Temp mute | {member}')
        embed.add_field(name='End time', value=f'{endtime}', inline=False)
        if reason:
            embed.add_field(name=f'Reason', value=f'{reason}', inline=False)
        await ctx.send(embed=embed)
        await self.bot.logchannel.send(embed=embed)

    @commands.command(help='Unmutes the person', aliases=['unstfu'])
    @commands.has_permissions(manage_messages=True)
    async def unmute(self, ctx, id: int, *, reason=None):
        await ctx.message.delete()

        def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
        
        await ctx.send("Is the mute temporary?")
        try:
            temp = await self.bot.wait_for("message", check=check, timeout=10)
            if temp.content.lower() in ("yes, true, 1"):
                temp = True
            else:
                temp = False
            print(temp)
        except asyncio.TimeoutError:
            await ctx.send("Didn't receive an answer in time, aborting")
            return

        try:
            async with self.bot.pool.acquire() as con:
                if temp:
                    userid = await con.fetchrow("UPDATE tempmutes SET endtime = $1 WHERE muteid = $2 RETURNING uid", datetime.datetime.utcnow(), id)
                    if not userid:
                        await ctx.send("Couldn't find database entry. Continuing")
                    else:
                        userid = userid["uid"]
                else:
                    userid = await con.fetchrow("UPDATE mutes SET active = $1 WHERE muteid = $2 RETURNING uid", False, id)
                    if not userid:
                        await ctx.send("Couldn't find database entry. Continuing")
                    else:
                        userid = userid["uid"]
                if userid:
                    member = ctx.guild.get_member(userid)
        except Exception as e:
            print(e)
        try:
            if member:
                muterole = ctx.guild.get_role(MUTEDROLE)

                await member.remove_roles(muterole)

                embed = discord.Embed(
                    title=f'You have been unmuted in {ctx.guild.name}', color=discord.Color.green())
                if reason:
                    embed.add_field(name='Reason:', value=f'{reason}', inline=False)
                try:
                    await member.send(embed=embed)
                except discord.Forbidden:
                    await ctx.send('Could not send DM to user')
        except:
            pass

        try:
            embed = discord.Embed(color=discord.Color.green())
            embed.set_footer(text=f'Action performed by {ctx.author}')
            if member:
                embed.set_author(name=f'Unmute | {member}')
            else:
                embed.set_author(name=f'Unmute | {id}')

            if reason:
                embed.add_field(name=f'Reason', value=f'{reason}', inline=False)
        except:
            pass

        await ctx.send(embed=embed)
        await self.bot.logchannel.send(embed=embed)

    @commands.command(help='View all infractions for a user')
    @commands.has_permissions(manage_messages=True)
    async def infractions(self, ctx, member: typing.Union[discord.Member, discord.User, discord.Object]):
        if not isinstance(member, discord.Member):
            member = member if isinstance(member, discord.User) else await self.bot.fetch_user(member.id)
        await ctx.message.delete()
        try:
            async with self.bot.pool.acquire() as con:
                warns = await con.fetch("SELECT * FROM warnings WHERE uid = $1", member.id)
                kicks = await con.fetch("SELECT * FROM kicks WHERE uid = $1", member.id)
                bans = await con.fetch("SELECT * FROM bans WHERE uid = $1", member.id)
                tempbans = await con.fetch("SELECT * FROM bans WHERE uid = $1", member.id)

            embeds = [[], [], [], []]
            for i in range(0, len(warns)//25+1):
                embeds[0].append(discord.Embed(color=0xb277dd))
            for i in range(0, len(kicks)//25+1):
                embeds[1].append(discord.Embed(color=0xb277dd))
            for i in range(0, len(bans)//25+1):
                embeds[2].append(discord.Embed(color=0xb277dd))
            for i in range(0, len(tempbans)//25+1):
                embeds[3].append(discord.Embed(color=0xb277dd))

            await ctx.send(f"Showing infractions for {member} (This could take some time)")
            async with ctx.typing():
                # warnings
                for i, warn in enumerate(warns):
                    warnid = warn[0]
                    invoker = self.bot.get_user(warn[2]) or await self.bot.fetch_user(warn[2])
                    datetime = str(warn[3])[0:-7]
                    reason = warn[4]

                    embeds[0][i//25].add_field(
                        name=f'ID: {warnid}', value=f'When: {datetime} UTC\nExecutor:{invoker}\nReason: {reason}')

                # kicks
                for i, kick in enumerate(kicks):
                    kickid = kick[0]
                    invoker = self.bot.get_user(kick[2]) or await self.bot.fetch_user(kick[2])
                    datetime = str(kick[3])[0:-7]
                    reason = kick[4]

                    embeds[1][i//25].add_field(
                        name=f'ID: {kickid}', value=f'When: {datetime} UTC\nExecutor: {invoker}\nReason: {reason}')

                # bans
                for i, ban in enumerate(bans):
                    banid = ban[0]
                    invoker = self.bot.get_user(ban[2]) or await self.bot.fetch_user(ban[2])
                    datetime = str(ban[3])[0:-7]
                    reason = ban[4]

                    embeds[2][i//25].add_field(
                        name=f'ID: {banid}', value=f'When: {datetime} UTC\nExecutor: {invoker}\nReason: {reason}')

                # tempbans
                for ban in tempbans:
                    banid = ban[0]
                    invoker = self.bot.get_user(ban[2]) or await self.bot.fetch_user(ban[2])
                    datetime = str(ban[3])[0:-7]
                    end = ban[4]
                    reason = ban[5]

                    embeds[3][i//25].add_field(
                        name=f'ID: {banid}', value=f'When: {datetime} UTC\nExecutor: {invoker}\nEnd date time: {end}\nReason: {reason}')

                await ctx.send('Warnings:')
                for embed in embeds[0]:
                    if not embed:
                        embed.add_field(name='No warns found', value='\u200b')
                    await ctx.send(embed=embed)

                await ctx.send('Kicks:')
                for embed in embeds[1]:
                    if not embed:
                        embed.add_field(name='No kicks found', value='\u200b')
                    await ctx.send(embed=embed)

                await ctx.send('Bans:')
                for embed in embeds[2]:
                    if not embed:
                        embed.add_field(name='No bans found', value='\u200b')
                    await ctx.send(embed=embed)

                await ctx.send('Tempbans:')
                for embed in embeds[3]:
                    if not embed:
                        embed.add_field(
                            name='No temp bans found', value='\u200b')
                    await ctx.send(embed=embed)

        except Exception as error:
            print(error)

    @commands.command(help='Delete a warning')
    @commands.has_permissions(manage_messages=True)
    async def delwarn(self, ctx, warnid: int):
        await ctx.message.delete()
        async with self.bot.pool.acquire() as con:
            try:
                await con.execute("DELETE FROM warnings WHERE warnid = $1", warnid)
                await ctx.send(f'Successfully deleted warn with ID: {warnid}')
            except Exception:
                await ctx.send(f'Could not find warn with ID: {warnid}')

    @commands.command(help='Delete a kick')
    @commands.has_permissions(manage_messages=True)
    async def delkick(self, ctx, kickid: int):
        await ctx.message.delete()
        async with self.bot.pool.acquire() as con:
            try:
                await con.execute("DELETE FROM kicks WHERE kickid = $1", kickid)
                await ctx.send(f'Successfully deleted kick with ID: {kickid}')
            except Exception:
                await ctx.send(f'Could not find kick with ID: {kickid}')

    @commands.command(help='Delete a ban')
    @commands.has_permissions(manage_messages=True)
    async def delban(self, ctx, banid: int):
        await ctx.message.delete()
        async with self.bot.pool.acquire() as con:
            try:
                await con.execute("DELETE FROM bans WHERE banid = $1", banid)
                await ctx.send(f'Successfully deleted ban with ID: {banid}')
            except Exception:
                await ctx.send(f'Could not find ban with ID: {banid}')

    @commands.command(help='Delete a temporary ban')
    @commands.has_permissions(manage_messages=True)
    async def deltempban(self, ctx, banid: int):
        await ctx.message.delete()
        async with self.bot.pool.acquire() as con:
            try:
                await con.execute("DELETE FROM tempbans WHERE banid = $1", banid)
                await ctx.send(f'Successfully deleted temporary ban with ID: {banid}')
            except Exception:
                await ctx.send(f'Could not find temporary ban with ID: {banid}')

    @commands.command(help='Check out a warning case')
    @commands.has_permissions(manage_messages=True)
    async def warncase(self, ctx, warnid: int):
        await ctx.message.delete()
        try:
            async with self.bot.pool.acquire() as con:
                case = await con.fetchrow("SELECT * FROM warnings WHERE warnid = $1", warnid)
            embed = discord.Embed(color=0xb277dd)
            member = await self.bot.fetch_user(case[1])
            embed.set_author(name=str(member), icon_url=member.avatar_url)
            invoker = await self.bot.fetch_user(case[2])
            datetime = str(case[3])[0:-7]
            embed.add_field(name='ID: ' + str(case[0]),
                            value=f'When: {datetime} UTC\nExecutor: {invoker}\nReason: {case[4]}', inline=False)
            await ctx.send(embed=embed)
        except Exception:
            await ctx.send(f'Could not find warn with ID: {warnid}')

    @commands.command(help='Check out a kick case')
    @commands.has_permissions(manage_messages=True)
    async def kickcase(self, ctx, kickid: int):
        await ctx.message.delete()
        try:
            async with self.bot.pool.acquire() as con:
                case = await con.fetchrow("SELECT * FROM kicks WHERE kickid = $1", kickid)
            embed = discord.Embed(color=0xb277dd)
            member = await self.bot.fetch_user(case[1])
            embed.set_author(name=str(member), icon_url=member.avatar_url)
            invoker = await self.bot.fetch_user(case[2])
            datetime = str(case[3])[0:-7]
            embed.add_field(name='ID: ' + str(case[0]),
                            value=f'When: {datetime} UTC\nExecutor: {invoker}\nReason: {case[4]}', inline=False)
            await ctx.send(embed=embed)
        except Exception:
            await ctx.send(f'Could not find kick with ID: {kickid}')

    @commands.command(help='Check out a ban case')
    @commands.has_permissions(manage_messages=True)
    async def bancase(self, ctx, banid: int):
        await ctx.message.delete()
        try:
            async with self.bot.pool.acquire() as con:
                case = con.fetchrow("SELECT * FROM bans WHERE banid = %s", banid)
            embed = discord.Embed(color=0xb277dd)
            member = await self.bot.fetch_user(case[1])
            embed.set_author(name=str(member), icon_url=member.avatar_url)
            invoker = await self.bot.fetch_user(case[2])
            datetime = str(case[3])[0:-7]
            embed.add_field(name='ID: ' + str(case[0]),
                            value=f'When: {datetime} UTC\nExecutor: {invoker}\nReason: {case[4]}',
                            inline=False)
        except Exception:
            await ctx.send(f'Could not find ban with ID: {banid}')

    @commands.command(help='Check out a temporary ban case')
    @commands.has_permissions(manage_messages=True)
    async def tempbancase(self, ctx, banid: int):
        await ctx.message.delete()
        try:
            async with self.bot.pool.acquire() as con:
                case = con.fetchrow("SELECT * FROM tempbans WHERE banid = %s", banid)
            embed = discord.Embed(color=0xb277dd)
            member = await self.bot.fetch_user(case[1])
            embed.set_author(name=str(member), icon_url=member.avatar_url)
            invoker = await self.bot.fetch_user(case[2])
            datetime = str(case[3])[0:-7]
            enddatetime = str(case[4])[0:-7]
            embed.add_field(name='ID: ' + str(case[0]),
                            value=f'When: {datetime} UTC\nExecutor: {invoker}\nReason: {case[6]}\nEnd: {enddatetime}\n',
                            inline=False)
        except Exception:
            await ctx.send(f'Could not find ban with ID: {banid}')


def setup(bot):
    bot.add_cog(Moderation(bot))

import discord
import psycopg2
from discord.ext import commands

from config import *


class moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # This is the bot instance, it lets us interact with most things
        try:
            self.conn = psycopg2.connect(host=HOST, port=PORT, database=DATABASE, user=USER,
                                         password=PASSWORD)
            self.cur = self.conn.cursor()
        except (Exception, psycopg2.DatabaseError):
            pass

    @commands.command(help='Kicks the specified member for the specified reason')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await ctx.message.delete()
        embed = discord.Embed(title=f'You have been kicked from {ctx.guild.name}', color=discord.Color.green())
        if reason:
            embed.add_field(name='Reason:', value=f'{reason}', inline=False)
        embed.add_field(name='If you have questions:', value=f'If you have questions about this action, or would like '
                                                             f'to appeal it. Please contact the staff team. '
                                                             f'You were kicked by {ctx.author.mention}', inline=False)
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            await ctx.send('Could not send DM to user')
        await member.kick(reason=reason)
        try:
            self.cur.execute("INSERT INTO kicks(uid, executor, timedate, reason) VALUES(%s, %s, "
                             "CURRENT_TIMESTAMP(1), %s) RETURNING kickid", (member.id, ctx.author.id, reason))
            kickid = self.cur.fetchone()[0]
            self.conn.commit()
        except Exception as error:
            print(error)
        if reason:
            embed = discord.Embed(title=f'👌 CASE {kickid} {member} has been kicked for the reason:',
                                  color=discord.Color.green())
            embed.add_field(name='\u200b', value=f'**{reason}**', inline=False)
        else:
            embed = discord.Embed(title=f'👌 CASE {kickid} {member} has been kicked',
                                  color=discord.Color.green())
        await ctx.send(embed=embed)
        channel = await self.bot.fetch_channel(425632491622105088)
        await channel.send(embed=embed)

    @commands.command(help='Bans the specified member for the specified reason')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.User, *, reason=None):
        await ctx.message.delete()
        embed = discord.Embed(title=f'You have been banned from {ctx.guild.name}', color=discord.Color.green())
        if reason:
            embed.add_field(name='Reason:', value=f'{reason}', inline=False)
        embed.add_field(name='If you have questions:', value=f'If you have questions about this action, or would like '
                                                             f'to appeal it. Please contact the staff team. '
                                                             f'You were banned by {ctx.author.mention}', inline=False)
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            await ctx.send('Could not send DM to user')
        await member.ban(reason=reason)
        if reason:
            embed = discord.Embed(title=f'👌 {member} has been banned for the reason:',
                                  color=discord.Color.green())
            embed.add_field(name='\u200b', value=f'`{reason}`', inline=False)
        else:
            embed = discord.Embed(title=f'👌 {member} has been banned', color=discord.Color.green())
        await ctx.send(embed=embed)
        channel = await self.bot.fetch_channel(425632491622105088)
        await channel.send(embed=embed)

    @commands.command(help='Warns the user for the specified reason')
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.User, *, reason=None):
        await ctx.message.delete()
        embed = discord.Embed(title=f'You have been warned in {ctx.guild.name}', color=discord.Color.green())
        if reason:
            embed.add_field(name='Reason:', value=f'{reason}', inline=False)
        embed.add_field(name='\u200b', value=f'If you have questions about this action, or would like '
                                             f'to appeal it. Please contact the staff team. '
                                             f'You were warned by {ctx.author.mention}', inline=False)
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            await ctx.send('Could not send DM to user')
        try:
            self.cur.execute("INSERT INTO warnings(uid, executor, timedate, reason) VALUES(%s, "
                             "%s, CURRENT_TIMESTAMP(1), %s) RETURNING warnid", (member.id, ctx.author.id, reason))
            warnid = self.cur.fetchone()[0]
            self.conn.commit()
        except Exception as error:
            print(error)

        if reason:
            embed = discord.Embed(title=f'👌 CASE {warnid} {member} has been warned for the reason:',
                                  color=discord.Color.green())
            embed.add_field(name='\u200b', value=f'**{reason}**', inline=False)
        else:
            embed = discord.Embed(title=f'👌 CASE {warnid} {member} has been warned')
        await ctx.send(embed=embed)
        channel = await self.bot.fetch_channel(425632491622105088)
        await channel.send(embed=embed)

    @commands.command(help='View all infractions for a user')
    @commands.has_permissions(manage_messages=True)
    async def infractions(self, ctx, member: discord.Member):
        await ctx.message.delete()
        try:
            embed = discord.Embed(color=0xb277dd)
            self.cur.execute("SELECT * FROM warnings WHERE uid = %s", (member.id,))
            warns = self.cur.fetchall()
            self.cur.execute("SELECT * FROM kicks WHERE uid = %s", (member.id,))
            kicks = self.cur.fetchall()
            self.cur.execute("SELECT * FROM bans WHERE uid = %s", (member.id,))
            bans = self.cur.fetchall()
            embed.set_author(name=str(member), icon_url=member.avatar_url)
            # warnings
            embed.add_field(name='\u200b', value='Warnings:', inline=False)
            for warn in warns:
                invoker = await self.bot.fetch_user(warn[2])
                datetime = str(warn[3])[0:-7]
                embed.add_field(name='ID: ' + str(warn[0]),
                                value=f'When: {datetime} UTC\nExecutor: {invoker}\nReason: {warn[4]}', inline=False)
            # kicks
            embed.add_field(name='\u200b', value='Kicks:', inline=False)
            for kick in kicks:
                invoker = await self.bot.fetch_user(kick[2])
                datetime = str(kick[3])[0:-7]
                embed.add_field(name='ID: ' + str(kick[0]),
                                value=f'When: {datetime} UTC\nExecutor: {invoker}\nReason: {kick[4]}', inline=False)
            # bans
            embed.add_field(name='\u200b', value='Bans:', inline=False)
            for ban in bans:
                invoker = await self.bot.fetch_user(ban[2])
                datetime = str(ban[3])[0:-7]
                if ban[4]:
                    enddatetime = str(ban[5])
                embed.add_field(name='ID: ' + str(ban[0]),
                                value=f'When: {datetime} UTC\nExecutor: {invoker}\nReason: {ban[6]}\nTemporary: {ban[4]}\nend: {enddatetime}',
                                inline=False)
            await ctx.send(embed=embed)
        except Exception as error:
            print(error)

    @commands.command(help='Delete a warning')
    @commands.has_permissions(manage_messages=True)
    async def delwarn(self, ctx, warnid: int):
        await ctx.message.delete()
        try:
            self.cur.execute("DELETE FROM warnings WHERE warnid = %s", (warnid,))
            await ctx.send(f'Successfully deleted warn with ID: {warnid}')
        except:
            await ctx.send(f'Could not find warn with ID: {warnid}')
        finally:
            self.conn.commit()

    @commands.command(help='Delete a kick')
    @commands.has_permissions(manage_messages=True)
    async def delkick(self, ctx, kickid: int):
        await ctx.message.delete()
        try:
            self.cur.execute("DELETE FROM kicks WHERE kickid = %s", (kickid,))
            await ctx.send(f'Successfully deleted kick with ID: {kickid}')
        except:
            await ctx.send(f'Could not find kick with ID: {kickid}')
        finally:
            self.conn.commit()

    @commands.command(help='Delete a ban')
    @commands.has_permissions(manage_messages=True)
    async def delban(self, ctx, banid: int):
        await ctx.message.delete()
        try:
            self.cur.execute("DELETE FROM bans WHERE kickid = %s", (banid,))
            await ctx.send(f'Successfully deleted ban with ID: {banid}')
        except:
            await ctx.send(f'Could not find ban with ID: {banid}')
        finally:
            self.conn.commit()

    @commands.command(help='Check out a warning case')
    @commands.has_permissions(manage_messages=True)
    async def warncase(self, ctx, warnid: int):
        await ctx.message.delete()
        try:
            self.cur.execute("SELECT * FROM warnings WHERE warnid = %s", (warnid,))
            case = self.cur.fetchone()
            embed = discord.Embed(color=0xb277dd)
            member = await self.bot.fetch_user(case[1])
            embed.set_author(name=str(member), icon_url=member.avatar_url)
            invoker = await self.bot.fetch_user(case[2])
            datetime = str(case[3])[0:-7]
            embed.add_field(name='ID: ' + str(case[0]),
                            value=f'When: {datetime} UTC\nExecutor: {invoker}\nReason: {case[4]}', inline=False)
            await ctx.send(embed=embed)
        except:
            await ctx.send(f'Could not find warn with ID: {warnid}')

    @commands.command(help='Check out a kick case')
    @commands.has_permissions(manage_messages=True)
    async def kickcase(self, ctx, kickid: int):
        await ctx.message.delete()
        try:
            self.cur.execute("SELECT * FROM kicks WHERE kickid = %s", (kickid,))
            case = self.cur.fetchone()
            embed = discord.Embed(color=0xb277dd)
            member = await self.bot.fetch_user(case[1])
            embed.set_author(name=str(member), icon_url=member.avatar_url)
            invoker = await self.bot.fetch_user(case[2])
            datetime = str(case[3])[0:-7]
            embed.add_field(name='ID: ' + str(case[0]),
                            value=f'When: {datetime} UTC\nExecutor: {invoker}\nReason: {case[4]}', inline=False)
            await ctx.send(embed=embed)
        except:
            await ctx.send(f'Could not find kick with ID: {kickid}')

    @commands.command(help='Check out a ban case')
    @commands.has_permissions(manage_messages=True)
    async def bancase(self, ctx, banid: int):
        await ctx.message.delete()
        try:
            self.cur.execute("SELECT * FROM bans WHERE banid = %s", (banid,))
            case = self.cur.fetchone()
            embed = discord.Embed(color=0xb277dd)
            member = await self.bot.fetch_user(case[1])
            embed.set_author(name=str(member), icon_url=member.avatar_url)
            invoker = await self.bot.fetch_user(case[2])
            datetime = str(case[3])[0:-7]
            if case[4]:
                enddatetime = str(case[5])
            embed.add_field(name='ID: ' + str(case[0]),
                            value=f'When: {datetime} UTC\nExecutor: {invoker}\nReason: {case[6]}\nTemporary: {case[4]}\nend: {enddatetime}',
                            inline=False)
        except:
            await ctx.send(f'Could not find ban with ID: {banid}')


def setup(bot):
    bot.add_cog(moderation(bot))

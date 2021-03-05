from discord.ext import commands
import os
from asyncio import TimeoutError


class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # This is the bot instance, it lets us interact with most things

    @commands.group(help='Gets the custom help commands', invoke_without_command=True)
    async def chelp(self, ctx, name='chelp'):
        name = name.lower()
        try:
	@@ -14,9 +16,50 @@ async def chelp(self, ctx, name='chelp'):
            await ctx.send(f'{message}')
            await ctx.message.delete()

        except BaseException:
            pass

    @commands.has_permissions(administrator=True)
    @chelp.command(help='Add a new custom command')
    async def add(self, ctx, name, *, text):
        name = name.lower()
        if name in os.listdir('./cogs/chelp'[:-4]):
            await ctx.send(f"Command {name} already exists")
            return
        with open(f'cogs/chelp/{name}.txt', 'w') as f:
            f.write(text)
        await ctx.send(f'Created new custom command {name}\n\n{text}')

    @commands.has_permissions(administrator=True)
    @chelp.command(help='Edit an already existing custom command')
    async def edit(self, ctx, name, *, text):
        name = name.lower()
        if name not in os.listdir('./cogs/chelp'[:-4]):
            await ctx.send(f"Command {name} doesn't exists")
            return
        with open(f'cogs/chelp/{name}.txt', 'w') as f:
            f.write(text)
        await ctx.send(f'Edited custom command {name}\n\n{text}')

    @commands.has_permissions(administrator=True)
    @chelp.command(help='Delete a custom command')
    async def delete(self, ctx, name):
        name = name.lower()
        if name not in os.listdir('./cogs/chelp'[:-4]):
            await ctx.send(f"Command {name} doesn't exists")
            return
        await ctx.send(f"Please retype {name} to confirm")

        def check(m):
            return ctx.channel == m.channel and ctx.author == m.author and m.content == name
        try:
            await self.bot.wait_for('message', check=check, timeout=10)
        except TimeoutError:
            await ctx.send("Did not confirm in time. Aborting")

        os.remove(f"./cogs/chelp/{name}.txt")
        await ctx.send(f"sucesfully deleted command {name}")


def setup(bot):
    bot.add_cog(CustomCommands(bot))

import os
from asyncio import TimeoutError

from discord.ext import commands


class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # This is the bot instance, it lets us interact with most things

    @commands.group(help="Gets the custom help commands")
    async def chelp(self, ctx):
        if ctx.invoked_subcommand is None:
            name = name.lower()
            try:
                with open(f"cogs/chelp/{name}.txt", "r") as f:
                    command = f.read()
                await ctx.send(f"{command}")
                # await message.delete()
            except (FileNotFoundError, OSError):
                pass

    @commands.has_permissions(administrator=True)
    @chelp.command()
    async def add(self, ctx, name, *, text):
        name = name.lower()
        if str(name + ".txt") in os.listdir("./cogs/chelp"):
            await ctx.send(f"Command {name} already exists")
            return

        with open(f"cogs/chelp/{name}.txt", "w") as f:
            f.write(text)
        await ctx.send(f"Created new custom command {name}\n\n{text}")

    @commands.has_permissions(administrator=True)
    @chelp.command()
    async def edit(self, ctx, name, *, text):
        name = name.lower()
        if str(name + ".txt") not in os.listdir("./cogs/chelp"):
            await ctx.send(f"Command {name} doesn't exists")
            return

        await ctx.send(f"Please retype {name} to confirm")

        def check(m):
            return (
                ctx.channel == m.channel
                and ctx.author == m.author
                and m.content == name
            )

        try:
            await self.bot.wait_for("message", check=check, timeout=10)
        except TimeoutError:
            await ctx.send("Did not confirm in time. Aborting")
            return

        with open(f"cogs/chelp/{name}.txt", "w") as f:
            f.write(text)
        await ctx.send(f"Edited custom command {name}\n\n{text}")

    @commands.has_permissions(administrator=True)
    @chelp.command()
    async def delete(self, ctx, name):
        name = name.lower()
        if str(name + ".txt") not in os.listdir("./cogs/chelp"):
            await ctx.send(f"Command {name} doesn't exists")
            return

        await ctx.send(f"Please retype {name} to confirm")

        def check(m):
            return (
                ctx.channel == m.channel
                and ctx.author == m.author
                and m.content == name
            )

        try:
            await self.bot.wait_for("message", check=check, timeout=10)
        except TimeoutError:
            await ctx.send("Did not confirm in time. Aborting")
            return

        os.remove(f"./cogs/chelp/{name}.txt")
        await ctx.send(f"sucesfully deleted command {name}")


def setup(bot):
    bot.add_cog(CustomCommands(bot))

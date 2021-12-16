# bot.py
import asyncio
import logging
import os
from random import randint

import asyncpg
import discord
from discord.ext import commands

from config import *

intents = discord.Intents.all()
activity = discord.Activity(
    type=discord.ActivityType.listening, name=f"your commands beginning with {PREFIX}"
)
bot = commands.Bot(
    command_prefix=PREFIX,
    case_insensitive=True,
    intents=intents,
    help_command=None,
    activity=activity,
)

logger = logging.getLogger("latest")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="latest.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    print(f"Username is {bot.user.name}")
    print(f"ID is {bot.user.id}")
    print(f"Keep this window open to keep the bot running.")

    # database
    print("Connecting to database")
    await get_db()

    # extensions
    await load_extensions()

    bot.logchannel = await bot.fetch_channel(425632491622105088)


async def get_db():
    bot.pool = await asyncpg.create_pool(
        host=HOST, port=PORT, database=DATABASE, user=USER, password=PASSWORD
    )

    async with bot.pool.acquire() as con:
        result = await con.fetchrow("SELECT version()")
        db_version = result[0]
        print(f"Database version: {db_version}")


async def load_extensions():
    if __name__ == "__main__":

        status = {}
        for extension in os.listdir("./cogs"):
            if extension.endswith(".py"):
                status[extension] = "x"
        errors = []

        for extension in status:
            if extension.endswith(".py"):
                try:
                    bot.load_extension(f"cogs.{extension[:-3]}")
                    status[extension] = "L"
                except Exception as e:
                    errors.append(e)

        maxlen = max(len(str(extension)) for extension in status)
        for extension in status:
            print(f" {extension.ljust(maxlen)} | {status[extension]}")
        print(errors) if errors else print("no errors during loading")


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# SOME EXTRA COMMANDS THAT DON'T FIT IN A COG
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# chelp
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.startswith(PREFIX):
        try:
            command = message.content.strip(PREFIX).lower()
            with open(f"cogs/chelp/{command}.txt", "r") as f:
                command = f.read()
            await message.channel.send(f"{command}")
            # await message.delete()
            return
        except (FileNotFoundError, OSError):
            pass
        await bot.process_commands(message)


@bot.command()
@commands.has_permissions(administrator=True)
async def load(ctx, extension):
    await ctx.send(f"loading cog {extension}")
    try:
        bot.load_extension(f"cogs.{extension}")
        await ctx.send(f"loaded cog {extension}")
    except Exception as e:
        await ctx.send(f"Failed to load extension {extension}. {e}")
        await ctx.send(e)
        print(f"Failed to load extension {extension}.")
        print(e)


@bot.command()
@commands.has_permissions(administrator=True)
async def unload(ctx, extension):
    await ctx.send(f"unloading cog {extension}")
    try:
        bot.unload_extension(f"cogs.{extension}")
        await ctx.send(f"unloaded cog {extension}")
    except Exception as e:
        await ctx.send(f"Failed to unload extension {extension}. {e}")
        await ctx.send(e)
        print(f"Failed to unload extension {extension}.")
        print(e)


@bot.command(help="Reload a cog")
@commands.has_permissions(administrator=True)
async def reload(ctx, name):
    name = name.lower()
    await ctx.send(f"reloading cog {name}")
    bot.unload_extension(f"cogs.{name}")
    try:
        bot.load_extension(f"cogs.{name}")
        await ctx.send(f"reloaded cog {name}")
    except Exception as e:
        print(f"Failed to load extension {name}.")
        print(e)
        await ctx.send(e)


bot.run(TOKEN)

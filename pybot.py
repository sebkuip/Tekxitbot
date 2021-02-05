# bot.py
import asyncio
import logging
import os

import discord
import asyncpg
from discord.ext import commands
from random import randint

from config import *

intents = discord.Intents.all()
activity = discord.Activity(type=discord.ActivityType.listening, name=f"your commands beginning with {PREFIX}")
bot = commands.Bot(command_prefix=PREFIX, case_insensitive=True, intents=intents, help_command=None, activity=activity)

logger = logging.getLogger('latest')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='latest.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Username is {bot.user.name}')
    print(f'ID is {bot.user.id}')
    print(f'Keep this window open to keep the bot running.')

    bot.logchannel = await bot.fetch_channel(425632491622105088)

    # database
    print('Connecting to database')
    try:
        bot.con = await asyncpg.connect(host=HOST, port=PORT, database=DATABASE, user=USER,
                                password=PASSWORD)
        result = await bot.con.fetchrow('SELECT version()')
        db_version = result[0]
        print(f'Database version: {db_version}')
    except Exception as error:
        print(error)


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# SOME EXTRA COMMANDS THAT DON'T FIT IN A COG
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# chelp
@bot.event
async def on_message(message):
    if message.content.startswith(PREFIX):
        try:
            command = message.content.strip(PREFIX).lower()
            with open(f'cogs/chelp/{command}.txt', 'r') as f:
                command = f.read()
            await message.channel.send(f'{command}')
            # await message.delete()
        except (FileNotFoundError, OSError):
            await bot.process_commands(message)

@bot.command()
@commands.has_permissions(administrator=True)
async def load(ctx, extension):
    await ctx.send(f'loading cog {extension}')
    try:
        bot.load_extension(f'cogs.{extension}')
    except Exception as e:
        await ctx.send(f"Failed to load extension {extension}.")
        print(f"Failed to load extension {extension}.")
        print(e)
    await ctx.send(f'loaded cog {extension}')

@bot.command()
@commands.has_permissions(administrator=True)
async def unload(ctx, extension):
    await ctx.send(f'unloading cog {extension}')
    try:
        bot.load_extension(f'cogs.{extension}')
    except Exception as e:
        await ctx.send(f"Failed to load extension {extension}.")
        print(f"Failed to load extension {extension}.")
        print(e)
    await ctx.send(f'unloaded cog {extension}')

@bot.command(help='Reload a cog')
@commands.has_permissions(administrator=True)
async def reload(ctx, name):
    name = name.lower()
    await ctx.send(f'reloading cog {name}')
    bot.unload_extension(f'cogs.{name}')
    try:
        bot.load_extension(f'cogs.{name}')
        await ctx.send(f'reloaded cog {name}')
    except Exception as e:
        print(f"Failed to load extension {extension}.")
        print(e)
        await ctx.send(e)

if __name__ == '__main__':
    for extension in os.listdir('./cogs'):
        if extension.endswith('.py'):
            try:
                bot.load_extension(f'cogs.{extension[:-3]}')
            except Exception as e:
                print(f"Failed to load extension {extension}.")
                print(e)

bot.run(TOKEN)

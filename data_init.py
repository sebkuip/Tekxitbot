"""
import asyncpg
import asyncio
import aiohttp
import json
from config import *

class dataClient:
    def __init__(self, dbpool):
        self.pages = [n for n in range(0,10)] # filler data
        self.dbpool = dbpool
    
    async def get_page(self, n):
        async with aiohttp.ClientSession as session:
            async with session.get(f"https://mee6.xyz/api/plugins/levels/leaderboard/346653006759985152?page={n}&limit=1000") as r:
                data = await r.json()
                self.pages[n] = data
    
    async def write_page(self, n):
        for i in range(0,999):
            async with self.dbpool.acquire() as con:
                await con.execute("INSERT INTO levels(uid, xp, level, message_count) VALUES($1, $2, $3, $4)",
                                self.pages[n]["players"][i]["id"], self.pages[n]["players"][i]["xp"], self.pages[n]["players"][i]["level"], self.pages[n]["players"][i]["message_count"])

async def startup():
    dbpool = await asyncpg.create_pool(host=HOST, port=PORT, database=DATABASE, user=USER, password=PASSWORD)
    client = dataClient(dbpool)

    async with client.dbpool.acquire() as con:
        result = await con.fetchrow('SELECT version()')
        db_version = result[0]
        print(f'Database version: {db_version}')
    
    return client

async def main():
    loop = asyncio.get_event_loop()
    task = loop.create_task(startup())
    client = await task
    for i in range(0,9):
        await client.get_page(i)
        print(client.pages)

asyncio.run(main())
"""

import psycopg2
from config import *
import requests

conn = psycopg2.connect(host=HOST, port=PORT, database=DATABASE, user=USER, password=PASSWORD)
cur = conn.cursor()

pages = [n for n in range(0,9)]
print(pages)

for i in range(0,9):
    print(i)
    with requests.get(f"https://mee6.xyz/api/plugins/levels/leaderboard/346653006759985152?page={i}&limit=1000") as r:
        print("got response")
        data = r.json()
        print("made json")
        pages[i] = data
        print("copied to memory")

for i, page in enumerate(pages):
    for j in range(0,999):
        print(i, ",", j)
        try:
            print((pages[i]["players"][j]["id"], pages[i]["players"][j]["xp"], pages[i]["players"][j]["level"], pages[i]["players"][j]["message_count"]))
            cur.execute("INSERT INTO levels(uid, xp, level, message_count) VALUES(%s, %s, %s, %s)", (pages[i]["players"][j]["id"], pages[i]["players"][j]["xp"], pages[i]["players"][j]["level"], pages[i]["players"][j]["message_count"]))
            print("inserted")
        except IndexError:
            print("end")
conn.commit()
conn.close()
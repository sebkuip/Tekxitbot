import psycopg2
from config import *
import requests

conn = psycopg2.connect(host=HOST, port=PORT, database=DATABASE, user=USER, password=PASSWORD)
cur = conn.cursor()

pages = [n for n in range(0,10)]
print(pages)

for i in range(0,10):
    print(i)
    with requests.get(f"https://mee6.xyz/api/plugins/levels/leaderboard/346653006759985152?page={i}&limit=1000") as r:
        print("got response")
        data = r.json()
        print("made json")
        pages[i] = data
        print("copied to memory")

for i, page in enumerate(pages):
    for j in range(0,1000):
        print(i, ",", j)
        try:
            print((pages[i]["players"][j]["id"], pages[i]["players"][j]["xp"], pages[i]["players"][j]["level"], pages[i]["players"][j]["message_count"]))
            cur.execute("INSERT INTO levels(uid, xp, level, message_count) VALUES(%s, %s, %s, %s)", (pages[i]["players"][j]["id"], pages[i]["players"][j]["xp"], pages[i]["players"][j]["level"], pages[i]["players"][j]["message_count"]))
            print("inserted")
        except IndexError:
            print("end")
conn.commit()
conn.close()
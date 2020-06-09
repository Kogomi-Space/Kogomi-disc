import os
import asyncio
import aiohttp
import discord
import json
import datetime
import random
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup

from .DBFunctions import *

class OsuAPI:

    def __init__(self,user = "",discid = None):
        self.db = Database()
        username = " ".join(user)
        if username == "":
            self.user = self.db.fetch_osuid(discid)
        else:
            self.user = username
        self.url = "https://osu.ppy.sh/api"
        self.key = os.environ['OSUAPI']
        self.header = {"content-type": "application/json", "user-key": self.key}

    async def rank_graph(self,mode=0):
        md = 'osu'
        if mode == '1': md = 'taiko'
        if mode == '2': md = 'fruits'
        if mode == '3': md = 'mania'
        async with aiohttp.ClientSession() as session:
            async with session.get('https://osu.ppy.sh/users/{}/{}'.format(self.user, md)) as resp:
                text = await resp.read()
                res = BeautifulSoup(text.decode('utf-8'), 'lxml')
        script = res.find("script", {"id": "json-user"}, type='application/json')
        web_data = json.loads(script.text)
        rank_data = web_data['rankHistory']['data']
        base = datetime.datetime.today()
        date_list = [base - datetime.timedelta(days=x) for x in range(0, 90)]
        date_list = date_list[::-1]
        fig = plt.figure(figsize=(8, 2))
        ax = fig.add_subplot(111)
        plt.style.use('ggplot')
        color = 'yellow'
        ax.plot(date_list, rank_data, color=color, linewidth=3.0)
        ax.tick_params(axis='y', colors=color, labelcolor=color)
        ax.yaxis.label.set_color(color)
        ax.grid(color='w', linestyle='-', axis='y', linewidth=1)
        fig.tight_layout()
        rank_range = max(rank_data) - min(rank_data)
        plt.ylim(max(rank_data) + int(.15 * rank_range), min(rank_data) - int(.15 * rank_range))
        plt.xticks([])
        img_id = random.randint(0, 50)
        filepath = 'cache/rank_{}.png'.format(img_id)
        fig.savefig(filepath, transparent=True)
        file = discord.File(f'cache/rank_{img_id}.png', 'rank_{}.png'.format(img_id))
        plt.close()
        return file, 'rank_{}.png'.format(img_id)

    async def mrank(self, ctx, mapID, mapScore):
        res = await self.fetch_json("get_scores",f"b={mapID}&limit=100")
        idx = 1
        for score in res:
            if score['user_id'] == userID:
                if score['score'] == mapScore:
                    return idx
            idx += 1
        return None

    async def getUser(self):
        res = await self.fetch_json("get_user",f"u={self.user}")
        if len(res) == 0:
            return False
        return res

    async def fetch_json(self,type,params = ""):
        async with aiohttp.ClientSession(headers=self.header) as session:
            try:
                async with session.get("{}/{}?k={}&{}".format(self.url,type,self.key,params)) as channel:
                    res = await channel.json()
                    return res
            except Exception as e:
                return e
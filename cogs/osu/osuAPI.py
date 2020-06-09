import os
import asyncio
import aiohttp
import discord
import json
import datetime
import random
import matplotlib.pyplot as plt
import pyoppai
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

    async def mrank(self, mapID, mapScore):
        res = await self.fetch_json("get_scores",f"b={mapID}&limit=100")
        idx = 1
        for score in res:
            if score['user_id'] == userID:
                if score['score'] == mapScore:
                    return idx
            idx += 1
        return None

    async def getBeatmap(self,mapid):
        ptnko = await self.get_pyttanko(mapid)
        res = await self.fetch_json("get_beatmaps",f"b={mapid}")
        return ptnko, res

    async def getUser(self):
        res = await self.fetch_json("get_user",f"u={self.user}")
        if len(res) == 0:
            return False
        return res

    async def get_pyttanko(self, map_id: str, accs=[100], mods=0, misses=0, combo=None, completion=None, fc=None, color='blue'):
        url = 'https://osu.ppy.sh/osu/{}'.format(map_id)
        file_path = 'temp/{}.osu'.format(map_id)
        await self.download_file(url, file_path)
        bmap = pyttanko.parser().map(open(file_path))
        _, ar, od, cs, hp = pyttanko.mods_apply(mods, ar=bmap.ar, od=bmap.od, cs=bmap.cs, hp=bmap.hp)
        stars = pyttanko.diff_calc().calc(bmap, mods=mods)
        bmap.stars = stars.total
        bmap.aim_stars = stars.aim
        bmap.speed_stars = stars.speed

        if not combo:
            combo = bmap.max_combo()

        bmap.pp = []
        bmap.aim_pp = []
        bmap.speed_pp = []
        bmap.acc_pp = []

        bmap.acc = accs

        for acc in accs:
            n300, n100, n50 = pyttanko.acc_round(acc, len(bmap.hitobjects), misses)
            pp, aim_pp, speed_pp, acc_pp, _ = pyttanko.ppv2(
                bmap.aim_stars, bmap.speed_stars, bmap=bmap, mods=mods,
                n300=n300, n100=n100, n50=n50, nmiss=misses, combo=combo)
            bmap.pp.append(pp)
            bmap.aim_pp.append(aim_pp)
            bmap.speed_pp.append(speed_pp)
            bmap.acc_pp.append(acc_pp)
        if fc:
            n300, n100, n50 = pyttanko.acc_round(fc, len(bmap.hitobjects), 0)
            # print("-------------", n300, n100, n50)
            fc_pp, _, _, _, _ = pyttanko.ppv2(
                bmap.aim_stars, bmap.speed_stars, bmap=bmap, mods=mods,
                n300=n300 + misses, n100=n100, n50=n50, nmiss=0, combo=bmap.max_combo())

        pyttanko_json = {
            'version': bmap.version,
            'title': bmap.title,
            'artist': bmap.artist,
            'creator': bmap.creator,
            'combo': combo,
            'max_combo': bmap.max_combo(),
            'misses': misses,
            'mode': bmap.mode,
            'stars': bmap.stars,
            'aim_stars': bmap.aim_stars,
            'speed_stars': bmap.speed_stars,
            'pp': bmap.pp,  # list
            'aim_pp': bmap.aim_pp,
            'speed_pp': bmap.speed_pp,
            'acc_pp': bmap.acc_pp,
            'acc': bmap.acc,  # list
            'cs': cs,
            'od': od,
            'ar': ar,
            'hp': hp
        }

        if completion:
            try:
                pyttanko_json['map_completion'] = (completion / len(bmap.hitobjects)) * 100
            except:
                pyttanko_json['map_completion'] = "Error"

        os.remove(file_path)
        return pyttanko_json

    async def fetch_json(self,type,params = ""):
        async with aiohttp.ClientSession(headers=self.header) as session:
            try:
                async with session.get("{}/{}?k={}&{}".format(self.url,type,self.key,params)) as channel:
                    res = await channel.json()
                    return res
            except Exception as e:
                return e

    async def download_file(self, url, filename):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                with open(filename, 'wb') as f:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)
                return await response.release()
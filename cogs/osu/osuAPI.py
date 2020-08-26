import os
import asyncio
import aiohttp
import discord
import json
import datetime
import random
import matplotlib.pyplot as plt
# import pyoppai
import pyttanko

from bs4 import BeautifulSoup

from .DBFunctions import *
os.chdir("/root/Cubchoo-disc/cogs/osu/data")

TEMP_FILE_PATH = '/root/Cubchoo-disc/cogs/osu/data/temp'
CACHE_FILE_PATH = '/root/Cubchoo-disc/cogs/osu/data/cache'

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

    async def beatmap_embed(self, map_id: str):
        res2, res = await self.getBeatmap(map_id, accs=[95, 99, 100])
        mapper = res[0]['creator']
        mapperlink = f"https://osu.ppy.sh/users/{res[0]['creator_id']}"
        dllink = f"https://osu.ppy.sh/d/{res[0]['beatmapset_id']}"
        bclink = f"https://bloodcat.com/osu/s/{res[0]['beatmapset_id']}"
        preview = f"https://bloodcat.com/osu/preview.html#{res[0]['beatmap_id']}"
        embed = discord.Embed(description=f"by [{mapper}]({mapperlink})\nDownload: [official]({dllink}) ([no vid]({dllink}n)) [bloodcat]({bclink}), [Map Preview]({preview})", color=0x00ffff)
        embed.set_author(name=f"{res[0]['artist']} - {res[0]['title']}",
                         url=f"https://osu.ppy.sh/beatmapsets/{res[0]['beatmapset_id']}#osu/{res[0]['beatmap_id']}")
        embed.set_thumbnail(url=f"https://b.ppy.sh/thumb/{res[0]['beatmapset_id']}l.jpg")
        lnth = float(res[0]['total_length'])
        bpm = str(round(float(res[0]['bpm']), 2)).rstrip("0")
        if bpm.endswith("."):
            bpm = bpm[:-1]
        length = str(datetime.timedelta(seconds=lnth))
        if length[:1] == "0":
            length = length[2:]
        ar = str(round(res2['ar'], 2)).rstrip("0")
        if bpm.endswith("."):
            bpm = bpm[:-1]
        if ar.endswith("."):
            ar = ar[:-1]
        od = str(round(res2['od'], 2)).rstrip("0")
        if od.endswith("."):
            od = od[:-1]
        cs = str(round(res2['cs'], 2)).rstrip("0")
        if cs.endswith("."):
            cs = cs[:-1]
        hp = str(round(res2['hp'], 2)).rstrip("0")
        if hp.endswith("."):
            hp = hp[:-1]
        f = []
        f.append(f"◆ {round(float(res2['stars']), 2)}***** ◆ **Length:** {length} ◆ {round(float(bpm), 2)} **BPM**")
        f.append(f"◆ **AR** {ar} ◆ **OD** {od} ◆ **HP** {hp} ◆ **CS** {cs}")
        f.append(
            f"◆ **{round(float(res2['pp'][0]), 2)}pp** for 95% ◆ **{round(float(res2['pp'][1]), 2)}pp** for 99% ◆ **{round(float(res2['pp'][2]), 2)}pp** for SS")
        embed.add_field(name="**{}**".format(res[0]['version']), value="\n".join(f), inline=False)
        return embed

    async def rank_graph(self,mode=0):
        md = 'osu'
        if mode == '1': md = 'taiko'
        if mode == '2': md = 'fruits'
        if mode == '3': md = 'mania'
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://osu.ppy.sh/users/{self.user}/{md}') as resp:
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
        fig.savefig(filepath, transparent=True)
        file = discord.File(f'{CACHE_FILE_PATH}/rank_{img_id}.png', f'rank_{img_id}.png')
        plt.close()
        return file, f'rank_{img_id}.png'

    async def mrank(self, mapID, mapScore,user=False):
        if not user:
            user = self.user
        res = await self.fetch_json("get_scores",f"b={mapID}&limit=100")
        idx = 1
        for score in res:
            if score['user_id'] == user:
                if score['score'] == mapScore:
                    return idx
            idx += 1
        return None

    async def bloodcat(self,search,params):
        async with aiohttp.ClientSession(headers=self.header) as session:
            try:
                async with session.get(f"https://bloodcat.com/osu/?mod=json&q={search}{params}") as channel:
                    res = await channel.json()
                    return res
            except Exception as e:
                return {}

    async def getBeatmap(self,mapid,accs=[100], mods=0, misses=0, combo=None, completion=None, fc=None):
        try:
            ptnko = await self.get_pyttanko(mapid,accs,mods,misses,combo,completion,fc)
        except Exception as e:
            print(e)
            ptnko = False
        res = await self.fetch_json("get_beatmaps",f"b={mapid}")
        return ptnko, res

    async def getScores(self,mapid,user=False):
        if not user:
            user = self.user
        res = await self.fetch_json("get_scores",f"u={user}&b={mapid}")
        if len(res) == 0:
            return False
        return res

    async def getUser(self,user=False):
        if not user:
            user = self.user
        res = await self.fetch_json("get_user",f"u={user}")
        if len(res) == 0:
            return False
        return res

    async def getUserBest(self,user=False):
        if not user:
            user = self.user
        res = await self.fetch_json("get_user_best", f"u={user}&m=0&limit=100")
        if len(res) == 0:
            return False
        return res

    async def getUserRecent(self,user=False):
        if not user:
            user = self.user
        res = await self.fetch_json("get_user_recent", f"u={user}&m=0&limit=50")
        if len(res) == 0:
            return False
        return res

    async def getMatch(self,mp):
        res = await self.fetch_json("get_match",f"mp={mp}")
        if len(res) == 0:
            return False
        return res

    async def get_pyttanko(self, map_id: str, accs=[100], mods=0, misses=0, combo=None, completion=None, fc=None):
        url = 'https://osu.ppy.sh/osu/{}'.format(map_id)
        file_path = f'{TEMP_FILE_PATH}/{map_id}.osu'
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
                async with session.get(f"{self.url}/{type}?k={self.key}&{params}") as channel:
                    res = await channel.json()
                    return res
            except Exception as e:
                return {}

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

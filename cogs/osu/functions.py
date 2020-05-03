import discord
from .functions import *
from redbot.core import Config
import os
import math
import aiohttp
import asyncio
import pyoppai
import decimal
import textwrap
import json
import random
import pyttanko
import time
import pycountry
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from collections import OrderedDict
import datetime
from pippy.beatmap import Beatmap
from PIL import Image, ImageDraw, ImageFont
import urllib.request
from redbot.core.utils.menus import menu, commands, DEFAULT_CONTROLS

# ***************************** SIMPLE FUNCTIONS
def time_ago(time1, time2):
    time_diff = time1 - time2
    timeago = datetime.datetime(1,1,1) + time_diff
    time_limit = 0
    time_ago = ""
    if timeago.year-1 != 0:
        time_ago += "{} Year{} ".format(timeago.year-1, determine_plural(timeago.year-1))
        time_limit = time_limit + 1
    if timeago.month-1 !=0:
        time_ago += "{} Month{} ".format(timeago.month-1, determine_plural(timeago.month-1))
        time_limit = time_limit + 1
    if timeago.day-1 !=0 and not time_limit == 2:
        time_ago += "{} Day{} ".format(timeago.day-1, determine_plural(timeago.day-1))
        time_limit = time_limit + 1
    if timeago.hour != 0 and not time_limit == 2:
        time_ago += "{} Hour{} ".format(timeago.hour, determine_plural(timeago.hour))
        time_limit = time_limit + 1
    if timeago.minute != 0 and not time_limit == 2:
        time_ago += "{} Minute{} ".format(timeago.minute, determine_plural(timeago.minute))
        time_limit = time_limit + 1
    if not time_limit == 2:
        time_ago += "{} Second{} ".format(timeago.second, determine_plural(timeago.second))
    return time_ago

def calculate_acc(beatmap):
    total_unscale_score = float(beatmap['count300'])
    total_unscale_score += float(beatmap['count100'])
    total_unscale_score += float(beatmap['count50'])
    total_unscale_score += float(beatmap['countmiss'])
    total_unscale_score *=300
    user_score = float(beatmap['count300']) * 300.0
    user_score += float(beatmap['count100']) * 100.0
    user_score += float(beatmap['count50']) * 50.0
    return (float(user_score)/float(total_unscale_score)) * 100.0

def format_number(num):
    try:
        dec = decimal.Decimal(num)
    except:
        return 'bad'
    tup = dec.as_tuple()
    delta = len(tup.digits) + tup.exponent
    digits = ''.join(str(d) for d in tup.digits)
    if delta <= 0:
        zeros = abs(tup.exponent) - len(tup.digits)
        val = '0.' + ('0'*zeros) + digits
    else:
        val = digits[:delta] + ('0'*tup.exponent) + '.' + digits[delta:]
    val = val.rstrip('0')
    if val[-1] == '.':
        val = val[:-1]
    if tup.sign:
        return '-' + val
    return val

def sortdict(main_list):
    list1 = []
    list2 = []
    try:
        od = OrderedDict(sorted(main_list.items(),key=lambda x:x[1], reverse=True))
    except:
        od = sorted(main_list.items(),key=lambda x:x[1], reverse=True)
    for key,value in od.items():
        list1.append(key)
        list2.append(value)
    return list1, list2

def parse_match(games,teamVS):
    plist = {}
    for game in games:
        try:
            del game['game_id']
        except:
            pass
        try:
            del game['play_mode']
        except:
            pass
        try:
            del game['match_type']
        except:
            pass
        try:
            del game['team_type']
        except:
            pass
        try:
            starttime = datetime.datetime.strptime(game['start_time'],"%Y-%m-%d %H:%M:%S")
            endtime = datetime.datetime.strptime(game['end_time'],"%Y-%m-%d %H:%M:%S")
            timediff = endtime - starttime
            game["time_taken"] = str(timediff)
        except:
            pass
        try:
            del game['start_time']
            del game['end_time']
            del game['scoring_type']
        except:
            pass
        scoresum = 0
        game['newscores'] = []
        game['playercount'] = 0
        for score in game['scores']:
            try:
                if 'EZ' in num_to_mod(int(score['enabled_mods'])):
                    score['score'] = int(score['score'])
                    score['score'] *= 2
            except:
                pass
            g = {}
            if int(score['score']) < 1000:
                continue
            g['user_id'] = score['user_id']
            if teamVS:
                try:
                    plist[int(score['team'])][g['user_id']] = 0
                except:
                    plist[int(score['team'])] = {}
                    plist[int(score['team'])][g['user_id']] = 0

            else:
                plist[g['user_id']] = 0
            g['score'] = score['score']
            g['maxcombo'] = score['maxcombo']
            g['acc'] = calculate_acc(score)
            g['enabled_mods'] = score['enabled_mods']
            scoresum += int(score['score'])
            game['playercount'] += 1
            game['newscores'].append(g)
        game['scoresum'] = scoresum
        try:
            del game['scores']
        except:
            pass
        for newscore in game['newscores']:
            avg = int(game['scoresum']) / game['playercount']
            pointcost = (int(newscore['score']) / avg) + 0.4
            newscore['point_cost'] = pointcost
    k = 0.4
    if teamVS:
        for player,point in plist[1].items():
            pointlist = []
            for game in games:
                for score in game['newscores']:
                    if player == score['user_id']:
                        pointlist.append(score['point_cost'])
            pointmax = 0
            for i in range(0,len(pointlist)):
                pointmax += pointlist[i]
            plist[1][player] = pointmax / len(pointlist) - 0.1
            plist[1][player] *= 1.2 ** ((len(pointlist)/len(games))**k)
        for player,point in plist[2].items():
            pointlist = []
            for game in games:
                for score in game['newscores']:
                    if player == score['user_id']:
                        pointlist.append(score['point_cost'])
            pointmax = 0
            for i in range(0,len(pointlist)):
                pointmax += pointlist[i]
            plist[2][player] = pointmax / len(pointlist) - 0.1
            plist[2][player] *= 1.2 ** ((len(pointlist)/len(games))**k)
    else:
        for player,point in plist.items():
            pointlist = []
            for game in games:
                for score in game['newscores']:
                    if player == score['user_id']:
                        pointlist.append(score['point_cost'])
            pointmax = 0
            for i in range(0,len(pointlist)):
                pointmax += pointlist[i]
            plist[player] = pointmax / len(pointlist)

    return games, plist

def num_to_mod(number):
    number = int(number)
    mod_list = []

    if number & 1<<0:   mod_list.append('NF')
    if number & 1<<1:   mod_list.append('EZ')
    if number & 1<<3:   mod_list.append('HD')
    if number & 1<<4:   mod_list.append('HR')
    if number & 1<<5:   mod_list.append('SD')
    if number & 1<<9:   mod_list.append('NC')
    elif number & 1<<6: mod_list.append('DT')
    if number & 1<<7:   mod_list.append('RX')
    if number & 1<<8:   mod_list.append('HT')
    if number & 1<<10:  mod_list.append('FL')
    if number & 1<<12:  mod_list.append('SO')
    if number & 1<<14:  mod_list.append('PF')
    if number & 1<<15:  mod_list.append('4 KEY')
    if number & 1<<16:  mod_list.append('5 KEY')
    if number & 1<<17:  mod_list.append('6 KEY')
    if number & 1<<18:  mod_list.append('7 KEY')
    if number & 1<<19:  mod_list.append('8 KEY')
    if number & 1<<20:  mod_list.append('FI')
    if number & 1<<24:  mod_list.append('9 KEY')
    if number & 1<<25:  mod_list.append('10 KEY')
    if number & 1<<26:  mod_list.append('1 KEY')
    if number & 1<<27:  mod_list.append('3 KEY')
    if number & 1<<28:  mod_list.append('2 KEY')

    return mod_list

def star_to_emote(sr):
    if sr <= 1.5: return "<:easys:524762856407957505>"
    if sr <= 2.25: return "<:normals:524762905560875019>"
    if sr <= 3.75: return "<:hards:524762888079015967>"
    if sr <= 5.25: return "<:insanes:524762897235312670>"
    if sr <= 6.75: return "<:experts:524762877912154142>"
    return "<:expertpluss:524762868235894819>"

def rank_to_emote(rank):
    if rank == "XH": return "<:rankingSSH:524765519686008867>"
    if rank == "X": return "<:rankingSS:524765487394062366>"
    if rank == "SH": return "<:rankingSH:524765442456289290>"
    if rank == "S": return "<:rankingS:524765397581430797>"
    if rank == "A": return "<:rankingA:524765216093765653>"
    if rank == "B": return "<:rankingB:524765259773509672>"
    if rank == "C": return "<:rankingC:524765302064676864>"
    if rank == "D": return "<:rankingD:524765348319330304>"
    if rank == "F": return "<:rankingF:524971327640305664>"

def hit_to_emote(hit):
    if hit == "hit300": return "<:hit300:524769369532792833>"
    if hit == "hit100": return "<:hit100:524769397840281601>"
    if hit == "hit50": return "<:hit50:524769420887982081>"
    if hit == "hit0": return "<:hit0:524769445936234496>"

def calculate_acc(beatmap):
    total_unscale_score = float(beatmap['count300'])
    total_unscale_score += float(beatmap['count100'])
    total_unscale_score += float(beatmap['count50'])
    total_unscale_score += float(beatmap['countmiss'])
    total_unscale_score *=300
    user_score = float(beatmap['count300']) * 300.0
    user_score += float(beatmap['count100']) * 100.0
    user_score += float(beatmap['count50']) * 50.0
    return (float(user_score)/float(total_unscale_score)) * 100.0

def determine_plural(number):
    if int(number) != 1:
        return 's'
    else:
        return ''

def time_ago(time1, time2):
    time_diff = time1 - time2
    timeago = datetime.datetime(1,1,1) + time_diff
    time_limit = 0
    time_ago = ""
    if timeago.year-1 != 0:
        time_ago += "{} Year{} ".format(timeago.year-1, determine_plural(timeago.year-1))
        time_limit = time_limit + 1
    if timeago.month-1 !=0:
        time_ago += "{} Month{} ".format(timeago.month-1, determine_plural(timeago.month-1))
        time_limit = time_limit + 1
    if timeago.day-1 !=0 and not time_limit == 2:
        time_ago += "{} Day{} ".format(timeago.day-1, determine_plural(timeago.day-1))
        time_limit = time_limit + 1
    if timeago.hour != 0 and not time_limit == 2:
        time_ago += "{} Hour{} ".format(timeago.hour, determine_plural(timeago.hour))
        time_limit = time_limit + 1
    if timeago.minute != 0 and not time_limit == 2:
        time_ago += "{} Minute{} ".format(timeago.minute, determine_plural(timeago.minute))
        time_limit = time_limit + 1
    if not time_limit == 2:
        time_ago += "{} Second{} ".format(timeago.second, determine_plural(timeago.second))
    return time_ago

async def rank_graph(userID,mode = 0):
    md = 'osu'
    if mode == '1': md = 'taiko'
    if mode == '2': md = 'fruits'
    if mode == '3': md = 'mania'
    async with aiohttp.ClientSession() as session:
        async with session.get('https://osu.ppy.sh/users/{}/{}'.format(userID,md)) as resp:
            text = await resp.read()
            res = BeautifulSoup(text.decode('utf-8'),'lxml')
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
    ax.tick_params(axis='y', colors=color, labelcolor = color)
    ax.yaxis.label.set_color(color)
    ax.grid(color='w', linestyle='-', axis='y', linewidth=1)
    fig.tight_layout()
    rank_range = max(rank_data) - min(rank_data)
    plt.ylim(max(rank_data) + int(.15*rank_range), min(rank_data) - int(.15*rank_range))
    plt.xticks([])
    img_id = random.randint(0, 50)
    filepath = 'cache/rank_{}.png'.format(img_id)
    fig.savefig(filepath, transparent=True)
    file = discord.File(f'cache/rank_{img_id}.png','rank_{}.png'.format(img_id))
    plt.close()
    return file, 'rank_{}.png'.format(img_id)

async def mrank(self, ctx, mapID, mapScore, userID):
    apikey = await self.config.apikey()
    async with aiohttp.ClientSession(headers=self.header) as session:
        try:
            async with session.get("https://osu.ppy.sh/api/get_scores?b={}&limit=100&k={}".format(mapID,apikey)) as channel:
                res = await channel.json()
        except Exception as e:
            await ctx.send("Error: " + str(e))
            return
    idx = 1
    for score in res:
        if score['user_id'] == userID:
            if score['score'] == mapScore:
                return idx
        idx += 1
    return None

async def get_sr(self, mapID, mods):
    if mapID in self.maps:
        return self.maps[mapID]['stars']
    url = 'https://osu.ppy.sh/osu/{}'.format(mapID)
    ctx = pyoppai.new_ctx()
    b = pyoppai.new_beatmap(ctx)

    BUFSIZE = 2000000
    buf = pyoppai.new_buffer(BUFSIZE)

    file_path = self.defaultPath + 'maps/{}.osu'.format(mapID)
    await download_file(url, file_path)
    pyoppai.parse(file_path, b, buf, BUFSIZE, True, self.defaultPath + 'cache/')
    dctx = pyoppai.new_d_calc_ctx(ctx)
    pyoppai.apply_mods(b, int(mods))

    stars, aim, speed, _, _, _, _ = pyoppai.d_calc(dctx, b)
    pyoppai_json = {
        'stars' : stars
    }

    os.remove(file_path)
    return stars

async def beatmap_embed(self,key,map_id: str):
    res = await try_api(self,f"https://osu.ppy.sh/api/get_beatmaps?k={key}&b={map_id}")
    res2 = await get_pyttanko(res[0]['beatmap_id'],accs=[95,99,100])
    mapper = res[0]['creator']
    mapperlink = "https://osu.ppy.sh/users/{}".format(res[0]['creator_id'])
    dllink = "https://osu.ppy.sh/d/{}".format(res[0]['beatmapset_id'])
    bclink = "https://bloodcat.com/osu/s/{}".format(res[0]['beatmapset_id'])
    preview = "https://bloodcat.com/osu/preview.html#{}".format(res[0]['beatmap_id'])
    embed=discord.Embed(description="by [{}]({})\nDownload: [official]({}) ([no vid]({}n)) [bloodcat]({}), [Map Preview]({})".format(mapper,mapperlink,dllink,dllink,bclink,preview), color=0x00ffff)
    embed.set_author(name="{} - {}".format(res[0]['artist'],res[0]['title']),url="https://osu.ppy.sh/beatmapsets/{}#osu/{}".format(res[0]['beatmapset_id'],res[0]['beatmap_id']))
    embed.set_thumbnail(url="https://b.ppy.sh/thumb/{}l.jpg".format(res[0]['beatmapset_id']))
    lnth = float(res[0]['total_length'])
    bpm = str(round(float(res[0]['bpm']),2)).rstrip("0")
    if bpm.endswith("."):
        bpm = bpm[:-1]
    length = str(datetime.timedelta(seconds=lnth))
    if length[:1] == "0":
        length = length[2:]
    ar = str(round(res2['ar'],2)).rstrip("0")
    if bpm.endswith("."):
        bpm = bpm[:-1]
    if ar.endswith("."):
        ar = ar[:-1]
    od = str(round(res2['od'],2)).rstrip("0")
    if od.endswith("."):
        od = od[:-1]
    cs = str(round(res2['cs'],2)).rstrip("0")
    if cs.endswith("."):
        cs = cs[:-1]
    hp = str(round(res2['hp'],2)).rstrip("0")
    if hp.endswith("."):
        hp = hp[:-1]
    f = []
    f.append(f"◆ {round(float(res2['stars']),2)}***** ◆ **Length:** {length} ◆ {round(float(bpm),2)} **BPM**")
    f.append(f"◆ **AR** {ar} ◆ **OD** {od} ◆ **HP** {hp} ◆ **CS** {cs}")
    f.append(f"◆ **{round(float(res2['pp'][0]),2)}pp** for 95% ◆ **{round(float(res2['pp'][1]),2)}pp** for 99% ◆ **{round(float(res2['pp'][2]),2)}pp** for SS")
    embed.add_field(name="**{}**".format(res[0]['version']),value="\n".join(f), inline=False)
    return embed

async def get_pyttanko(map_id:str, accs=[100], mods=0, misses=0, combo=None, completion=None, fc=None, plot = False, color = 'blue'):
    url = 'https://osu.ppy.sh/osu/{}'.format(map_id)
    file_path = 'temp/{}.osu'.format(map_id)
    await download_file(url, file_path)
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
        'pp': bmap.pp, # list
        'aim_pp': bmap.aim_pp,
        'speed_pp': bmap.speed_pp,
        'acc_pp': bmap.acc_pp,
        'acc': bmap.acc, # list
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
    if plot:
        #try:
        pyttanko_json['graph_url'] = await plot_map_stars(file_path, mods, color)
        # print(pyttanko_json['graph_url'])
        #except:
            #pass
        # print(pyttanko_json['graph_url'])

    os.remove(file_path)
    return pyttanko_json

async def download_file(url, filename):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            with open(filename, 'wb') as f:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    f.write(chunk)
            return await response.release()

async def plot_map_stars(beatmap, mods, color = 'blue'):
    #try:
    star_list, speed_list, aim_list, time_list = [], [], [], []
    results = oppai(beatmap, mods=mods)
    for chunk in results:
        time_list.append(chunk['time'])
        star_list.append(chunk['stars'])
        aim_list.append(chunk['aim_stars'])
        speed_list.append(chunk['speed_stars'])
    fig = plt.figure(figsize=(6, 2))
    ax = fig.add_subplot(111)
    plt.style.use('ggplot')
    ax.plot(time_list, star_list, color=color, label='Stars', linewidth=2)
    fig.gca().xaxis.set_major_formatter(ticker.FuncFormatter(plot_time_format))
    # plt.ylabel('Stars')
    ax.legend(loc='best')
    fig.tight_layout()
    ax.xaxis.label.set_color(color)
    ax.yaxis.label.set_color(color)
    ax.tick_params(axis='both', colors=color, labelcolor = color)
    ax.grid(color='w', linestyle='-', linewidth=1)

    img_id = random.randint(0, 50)
    filepath = "map_{}.png".format(img_id)
    fig.savefig(filepath, transparent=True)
    plt.close()
    upload = cloudinary.uploader.upload(filepath)
    url = upload['url']
    os.remove(filepath)
    # print(url)
    return url

async def use_api(self,ctx,url):
    async with aiohttp.ClientSession(headers=self.header) as session:
        try:
            async with session.get(url) as channel:
                res = await channel.json()
                return res
        except Exception as e:
            await ctx.send("Error: {}".format(str(e)))
            return

async def fetch_json(url):
    async with aiohttp.ClientSession(headers={"User-Agent": "User_Agent"}) as session:
        try:
            async with session.get(url) as channel:
                res = await channel.json()
                return res
        except Exception as e:
            return False

async def try_api(self,url):
    async with aiohttp.ClientSession(headers=self.header) as session:
        try:
            async with session.get(url) as channel:
                res = await channel.json()
                return res
        except Exception as e:
            await print("Error: {}".format(str(e)))
            return None

async def get_username(self,ctx,id):
    apikey = await self.config.apikey()
    async with aiohttp.ClientSession(headers=self.header) as session:
        try:
            async with session.get("https://osu.ppy.sh/api/get_user?u={}&k={}".format(id,apikey)) as channel:
                res = await channel.json()
                return res[0]['username']
        except Exception as e:
            return False

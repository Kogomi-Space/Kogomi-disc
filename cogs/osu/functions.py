import discord
from .functions import *
from redbot.core import Config
import os
import math
import aiohttp
import asyncio
import decimal
import textwrap
import json
import random
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

# async def plot_map_stars(beatmap, mods, color = 'blue'):
#     #try:
#     star_list, speed_list, aim_list, time_list = [], [], [], []
#     results = oppai(beatmap, mods=mods)
#     for chunk in results:
#         time_list.append(chunk['time'])
#         star_list.append(chunk['stars'])
#         aim_list.append(chunk['aim_stars'])
#         speed_list.append(chunk['speed_stars'])
#     fig = plt.figure(figsize=(6, 2))
#     ax = fig.add_subplot(111)
#     plt.style.use('ggplot')
#     ax.plot(time_list, star_list, color=color, label='Stars', linewidth=2)
#     fig.gca().xaxis.set_major_formatter(ticker.FuncFormatter(plot_time_format))
#     # plt.ylabel('Stars')
#     ax.legend(loc='best')
#     fig.tight_layout()
#     ax.xaxis.label.set_color(color)
#     ax.yaxis.label.set_color(color)
#     ax.tick_params(axis='both', colors=color, labelcolor = color)
#     ax.grid(color='w', linestyle='-', linewidth=1)
#
#     img_id = random.randint(0, 50)
#     filepath = "map_{}.png".format(img_id)
#     fig.savefig(filepath, transparent=True)
#     plt.close()
#     upload = cloudinary.uploader.upload(filepath)
#     url = upload['url']
#     os.remove(filepath)
#     # print(url)
#     return url
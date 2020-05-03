from .functions import *
import os
import asyncio
import textwrap
import random
import aggdraw
import time
import pycountry
import matplotlib.pyplot as plt
import datetime
from PIL import Image, ImageDraw, ImageFont
import urllib.request

async def _gen_rb_img(self,ctx,num,user,apikey,temp,res):
    acc = round(calculate_acc(res[num]), 2)
    totalhits = (int(res[num]['count50']) + int(res[num]['count100']) + int(res[num]['count300']) + int(
        res[num]['countmiss']))
    apibmapinfo = await use_api(self, ctx, "https://osu.ppy.sh/api/get_beatmaps?k={}&b={}".format(apikey, str(
        res[num]['beatmap_id'])))
    bmapinfo = await get_pyttanko(map_id=int(res[num]['beatmap_id']), misses=int(res[num]['countmiss']), accs=[acc],
                                  mods=int(res[num]['enabled_mods']), combo=int(res[num]['maxcombo']),
                                  completion=totalhits)
    complete = round(bmapinfo['map_completion'], 2)
    srating = str(round(bmapinfo['stars'], 2))
    pp = round(float(bmapinfo['pp'][0]), 2)
    mods = str(",".join(num_to_mod(res[num]['enabled_mods'])))
    score = format(int(res[num]['score']), ',d')
    if mods != "":
        mods = "+" + mods
    titleText = "{} - {}".format(bmapinfo['artist'], bmapinfo['title'])
    subtitleText = "[" + bmapinfo['version']
    maprank = await mrank(self, ctx, res[num]['beatmap_id'], res[num]['score'], user[0]['user_id'])
    toprank = None
    for idx, i in enumerate(temp):
        if i['beatmap_id'] == res[num]['beatmap_id']:
            toprank = idx + 1
            break
    self.rtemplate = Image.open("templates/recent.png")
    draw = ImageDraw.Draw(self.rtemplate)
    adraw = aggdraw.Draw(self.rtemplate)
    titleFont = ImageFont.truetype("/root/Cubchoo-disc/fonts/NotoSansSemiBold.otf", 16)
    subtitleFont = ImageFont.truetype("/root/Cubchoo-disc/fonts/NotoSansRegular.otf", 12)
    defaultFont = ImageFont.truetype("/root/Cubchoo-disc/fonts/NotoSansLight.otf", 15)
    defaultBoldFont = ImageFont.truetype("/root/Cubchoo-disc/fonts/NotoSansSemiBold.otf", 15)
    smallFont = aggdraw.Font((255, 255, 255), "/root/Cubchoo-disc/fonts/NotoSansLight.otf", size=12, opacity=255)
    smalllFont = ImageFont.truetype("/root/Cubchoo-disc/fonts/NotoSansLight.otf", 12)
    smallBoldFont = aggdraw.Font((255, 255, 255), "/root/Cubchoo-disc/fonts/NotoSansSemiBold.otf", size=12, opacity=255)
    smallBolddFont = ImageFont.truetype("/root/Cubchoo-disc/fonts/NotoSansSemiBold.otf", 12)
    smallestFont = aggdraw.Font((255, 255, 255), "/root/Cubchoo-disc/fonts/NotoSansLight.otf", size=10, opacity=255)
    smallesttFont = ImageFont.truetype("/root/Cubchoo-disc/fonts/NotoSansLight.otf", 10)
    tryFont = ImageFont.truetype("/root/Cubchoo-disc/fonts/NotoSansLight.otf", 20)
    hittFont = ImageFont.truetype("/root/Cubchoo-disc/fonts/NotoSansRegular.otf", 10)
    hitFont = aggdraw.Font((255, 255, 255), "/root/Cubchoo-disc/fonts/NotoSansRegular.otf", size=12, opacity=255)
    titleCutoff = False
    while titleFont.getsize(titleText)[0] > 448:
        titleText = titleText[:-1]
        titleCutoff = True
    if titleCutoff:
        titleText += "..."
    subtitleText += "] " + mods
    # Draw User Info
    adraw.text((498, 184), "{}pp".format(user[0]['pp_raw']), smallFont)
    adraw.text((498, 198), "#{}, {} #{}".format(user[0]['pp_rank'], user[0]['country'], user[0]['pp_country_rank']),
               smallFont)
    timeago = "Score set {}ago.".format(time_ago(datetime.datetime.utcnow() + datetime.timedelta(hours=0),
                                                 datetime.datetime.strptime(res[num]['date'], '%Y-%m-%d %H:%M:%S')))
    tago = textwrap.wrap(timeago, width=22)
    h = 268
    for line in tago:
        adraw.text((498, h), str(line), smallestFont)
        h += 14
    # Draw Combo
    w, h = draw.textsize(res[num]['maxcombo'], smalllFont)
    width = 20
    height = 190
    tempFont = aggdraw.Font((255, 255, 255), "/root/Cubchoo-disc/fonts/NotoSansLight.otf", size=14, opacity=255)
    tempFontSize = ImageFont.truetype("/root/Cubchoo-disc/fonts/NotoSansLight.otf", 14)
    tempBoldFont = aggdraw.Font((255, 255, 255), "/root/Cubchoo-disc/fonts/NotoSansSemiBold.otf", size=14, opacity=255)
    tempBoldFontSize = ImageFont.truetype("/root/Cubchoo-disc/fonts/NotoSansSemiBold.otf", 14)
    adraw.text((width, height), str(res[num]['maxcombo']), smallFont)
    w2, h2 = draw.textsize(str(bmapinfo['max_combo']), smallBolddFont)
    width2 = width + w + 12
    height2 = (414 - h2) / 2
    pen = aggdraw.Pen("white", 0.8)
    adraw.line((width2, height + 4, width + w, height2 + h2), pen)
    adraw.text((width2, height2), str(bmapinfo['max_combo']), smallBoldFont)
    # Draw 300s 100s 50s and misses
    w, h = draw.textsize(res[num]['count300'], font=hittFont)
    adraw.text(((290 - w) / 2, (244 - h) / 2), str(res[num]['count300']), hitFont)
    w, h = draw.textsize(res[num]['count50'], font=hittFont)
    adraw.text(((290 - w) / 2, (300 - h) / 2), res[num]['count50'], hitFont)
    w, h = draw.textsize(res[num]['count100'], font=hittFont)
    adraw.text(((478 - w) / 2, (244 - h) / 2), str(res[num]['count100']), hitFont)
    w, h = draw.textsize(res[num]['countmiss'], font=hittFont)
    adraw.text(((478 - w) / 2, (300 - h) / 2), res[num]['countmiss'], hitFont)
    # Draw if FC Stats
    new300 = int(res[num]['count300']) + int(res[num]['countmiss'])
    iffcstats = {"count50": res[num]['count50'], "count100": res[num]['count100'], "count300": new300, "countmiss": 0}
    iffcacc = round(calculate_acc(iffcstats), 2)
    iffcinfo = await get_pyttanko(map_id=res[num]['beatmap_id'], accs=[iffcacc], mods=int(res[num]['enabled_mods']),
                                  fc=True)
    iffcpp = round(float(iffcinfo['pp'][0]), 2)
    w, h = draw.textsize(str(iffcacc), smallesttFont)
    adraw.text(((790 - w) / 2, (530 - h) / 2), "IF FC WITH {}%".format(iffcacc), smallestFont)
    # Draw URL
    adraw.text((13, 282), "Generated using Cubchoo: https://github.com/dain98/Cubchoo-disc", smallestFont)
    # Flush aggdraw
    adraw.flush()
    # Draw User Image
    try:
        urllib.request.urlretrieve("https://a.ppy.sh/{}".format(user[0]['user_id']),
                                   "cache/user_{}.png".format(user[0]['user_id']))
        userimage = Image.open("cache/user_{}.png".format(user[0]['user_id']))
        userimage.thumbnail((54, 54), Image.ANTIALIAS)
        self.rtemplate.paste(userimage, (525, 107))
        os.remove("cache/user_{}.png".format(user[0]['user_id']))
    except:
        pass
    # Draw Beatmap Image
    try:
        urllib.request.urlretrieve("https://b.ppy.sh/thumb/" + str(apibmapinfo[0]['beatmapset_id']) + "l.jpg",
                                   'cache/map_{}.png'.format(apibmapinfo[0]['beatmapset_id']))
        mapimage = Image.open("cache/map_{}.png".format(apibmapinfo[0]['beatmapset_id']))
        mapimage.thumbnail((104, 78), Image.ANTIALIAS)
        self.rtemplate.paste(mapimage, (498, 7))
        os.remove("cache/map_{}.png".format(apibmapinfo[0]['beatmapset_id']))
    except:
        # print("Couldn't find a beatmap image for {}.".format(apibmapinfo[0]['beatmapset_id']))
        pass
    rankimage = Image.open("rankletters/rank" + res[num]['rank'] + ".png")
    rankimage.thumbnail((100, 100), Image.ANTIALIAS)
    self.rtemplate.paste(rankimage, (365, 63), rankimage)
    # Draw User Info
    draw.text((498, 166), "{}".format(user[0]['username']), font=defaultBoldFont, fill=(255, 255, 255))
    # Draw name of map
    draw.text((18, 13), titleText, font=titleFont, fill=(255, 255, 255))
    if maprank is not None:
        subtitleText = subtitleText + " Rank #{}".format(maprank)
        if toprank is not None:
            subtitleText = subtitleText + ", Personal Best #{}!".format(toprank)
    elif toprank is not None:
        subtitleText = subtitleText + " Personal Best #{}!".format(toprank)
    draw.text((18, 34), subtitleText, font=subtitleFont, fill=(255, 255, 255))
    # Draw score
    draw.text((19, 79), score, font=defaultFont, fill=(255, 255, 255))
    # Draw Difficulty
    draw.text((284, 139), "{}*".format(srating), font=defaultBoldFont, fill=(255, 255, 255))
    # Draw Map completion
    draw.text((241, 193), "{:.2f}%".format(complete), font=defaultFont, fill=(255, 255, 255))
    # Draw Accuracy
    draw.text((150, 193), "{:.2f}%".format(acc), font=defaultBoldFont, fill=(255, 255, 255))
    # Draw Beatmap information
    if "DT" in mods:
        lnth = round(float(apibmapinfo[0]['total_length']) / 1.5)
        bpm = str(round(float(apibmapinfo[0]['bpm']) * 1.5, 2)).rstrip("0")
    elif "HT" in mods:
        lnth = round(float(apibmapinfo[0]['total_length']) / 0.75)
        bpm = str(round(float(apibmapinfo[0]['bpm']) * 0.75, 2)).rstrip("0")
    else:
        lnth = float(apibmapinfo[0]['total_length'])
        bpm = str(round(float(apibmapinfo[0]['bpm']), 2)).rstrip("0")
        if bpm.endswith("."):
            bpm = bpm[:-1]
    length = str(datetime.timedelta(seconds=lnth))
    if length[:1] == "0":
        length = length[2:]
    # minutes = int(lnth/60)
    # seconds = lnth % 60
    # hours = int(minutes/60)
    # minutes = minutes%60
    # if hours == 0:
    #     length = str(minutes) + ":" + str(int(seconds))
    # else:
    #     length = str(hours) + ":" + str(int(minutes)) + ":" + str(int(seconds))
    ar = str(round(bmapinfo['ar'], 2)).rstrip("0")
    if bpm.endswith("."):
        bpm = bpm[:-1]
    if ar.endswith("."):
        ar = ar[:-1]
    od = str(round(bmapinfo['od'], 2)).rstrip("0")
    if od.endswith("."):
        od = od[:-1]
    cs = str(round(bmapinfo['cs'], 2)).rstrip("0")
    if cs.endswith("."):
        cs = cs[:-1]
    hp = str(round(bmapinfo['hp'], 2)).rstrip("0")
    if hp.endswith("."):
        hp = hp[:-1]
    draw.text((20, 255), "Length: {}, AR {}, OD {}, CS {}, HP {}, {} BPM".format(length, ar, od, cs, hp, bpm),
              font=smalllFont, fill=(255, 255, 255))
    # Draw Performance
    w, h = draw.textsize(str(pp), font=defaultFont)
    draw.text(((832 - w) / 2, (406 - h) / 2), "{}pp".format(pp), font=defaultFont, fill=(255, 255, 255))
    w, h = draw.textsize(str(iffcpp), font=defaultFont)
    draw.text(((832 - w) / 2, (496 - h) / 2), "{}pp".format(iffcpp), font=defaultFont, fill=(255, 255, 255))
    code = random.randint(100000000, 999999999)
    self.rtemplate.save("cache/score_{}.png".format(code))
    return code

async def _gen_rs_img(self,ctx,num,user,apikey,userbest,res,isTry = False):
    if isTry:
        trycount = 0
        tempid = res[num]['beatmap_id']
        for i in res:
            if i['beatmap_id'] == tempid:
                trycount += 1
            else:
                break
        await ctx.send("Try #{}".format(trycount))
    acc = round(calculate_acc(res[num]), 2)
    totalhits = (int(res[num]['count50']) + int(res[num]['count100']) + int(res[num]['count300']) + int(
        res[num]['countmiss']))
    apibmapinfo = await use_api(self, ctx, "https://osu.ppy.sh/api/get_beatmaps?k={}&b={}".format(apikey, str(
        res[num]['beatmap_id'])))
    bmapinfo = await get_pyttanko(map_id=int(res[num]['beatmap_id']), misses=int(res[num]['countmiss']), accs=[acc],
                                  mods=int(res[num]['enabled_mods']), combo=int(res[num]['maxcombo']),
                                  completion=totalhits)
    complete = round(bmapinfo['map_completion'], 2)
    srating = str(round(bmapinfo['stars'], 2))
    pp = round(float(bmapinfo['pp'][0]), 2)
    mods = str(",".join(num_to_mod(res[num]['enabled_mods'])))
    score = format(int(res[num]['score']), ',d')
    if mods != "":
        mods = "+" + mods
    titleText = "{} - {}".format(bmapinfo['artist'], bmapinfo['title'])
    subtitleText = "[" + bmapinfo['version']
    maprank = await mrank(self, ctx, res[num]['beatmap_id'], res[num]['score'], user[0]['user_id'])
    toprank = None
    for idx, i in enumerate(userbest):
        if i['beatmap_id'] == res[num]['beatmap_id']:
            if i['score'] == res[num]['score']:
                toprank = idx + 1
                break
    self.rtemplate = Image.open("templates/recent.png")
    draw = ImageDraw.Draw(self.rtemplate)
    adraw = aggdraw.Draw(self.rtemplate)
    defaultFont = getFont("NotoSansLight",16)
    defaultBoldFont = getFont("NotoSansSemiBold",16)
    smallFont = getFont("NotoSansLight",12)
    smallBoldFont = getFont("NotoSansSemiBold",12)
    smallestFont = getFont("NotoSansLight",10)
    bigFont = getFont("NotoSansSemiBold",20)
    hitFont = getFont("NotoSansRegular",12)

    # Draw name of map
    titleCutoff = False
    while getFont("NotoSansSemiBold",16,True).getsize(titleText)[0] > 448:
        titleText = titleText[:-1]
        titleCutoff = True
    if titleCutoff:
        titleText += "..."
    subtitleText += "] " + mods
    adraw.text((18, 13), titleText, getFont("NotoSansSemiBold", 16))
    adraw.text((18, 34),subtitleText,getFont("NotoSansRegular", 12))
    # Draw User Info
    adraw.text((498, 163), "{}".format(user[0]['username']), getFont("NotoSansSemiBold",16))
    adraw.text((498, 184), "{}pp".format(user[0]['pp_raw']), getFont("NotoSansLight",12))
    adraw.text((498, 198), "#{}, {} #{}".format(user[0]['pp_rank'], user[0]['country'], user[0]['pp_country_rank']),
               smallFont)
    timeago = "Score set {}ago.".format(time_ago(datetime.datetime.utcnow() + datetime.timedelta(hours=0),
                                                 datetime.datetime.strptime(res[num]['date'], '%Y-%m-%d %H:%M:%S')))
    tago = textwrap.wrap(timeago, width=22)
    h = 268
    for line in tago:
        adraw.text((498, h), str(line), smallestFont)
        h += 14
    # Draw Combo
    w, h = adraw.textsize(res[num]['maxcombo'], getFont("NotoSansLight", 12))
    width = 20
    height = 190
    tempFont = aggdraw.Font((255, 255, 255), "/root/Cubchoo-disc/fonts/NotoSansLight.otf", size=14, opacity=255)
    tempFontSize = ImageFont.truetype("/root/Cubchoo-disc/fonts/NotoSansLight.otf", 14)
    tempBoldFont = aggdraw.Font((255, 255, 255), "/root/Cubchoo-disc/fonts/NotoSansSemiBold.otf", size=14, opacity=255)
    tempBoldFontSize = ImageFont.truetype("/root/Cubchoo-disc/fonts/NotoSansSemiBold.otf", 14)
    adraw.text((width, height), str(res[num]['maxcombo']), smallFont)
    w2, h2 = adraw.textsize(str(bmapinfo['max_combo']),smallBoldFont)
    width2 = width + w + 12
    height2 = (414 - h2) / 2
    pen = aggdraw.Pen("white", 0.8)
    adraw.line((width2, height + 4, width + w, height2 + h2), pen)
    adraw.text((width2, height2), str(bmapinfo['max_combo']), smallBoldFont)
    # Draw score
    adraw.text((66, 70), score, defaultFont)
    # Draw 300s 100s 50s and misses
    w, h = adraw.textsize(res[num]['count300'],hitFont)
    adraw.text(((160 - w) / 2, (226 - h) / 2), str(res[num]['count300']), hitFont)
    w, h = adraw.textsize(res[num]['count100'],hitFont)
    adraw.text(((160 - w) / 2, (269 - h) / 2), str(res[num]['count100']), hitFont)
    w, h = adraw.textsize(res[num]['count50'],hitFont)
    adraw.text(((160 - w) / 2, (311 - h) / 2), res[num]['count50'], hitFont)
    w, h = adraw.textsize(res[num]['countmiss'],hitFont)
    adraw.text(((300 - w) / 2, (311 - h) / 2), res[num]['countmiss'], hitFont)
    # Draw Performance
    if maprank is not None:
        w, h = adraw.textsize(str(pp),defaultBoldFont)
        adraw.text(((832 - w) / 2, (208 - h) / 2), "{}pp".format(pp), defaultBoldFont)
        r = " R#{}".format(maprank)
        if toprank is not None:
            r += ", PB{}".format(toprank)
        w , h = adraw.textsize(r,getFont("NotoSansSemiBold", 12))
        adraw.text(((842 - w) / 2, (258 - h) / 2), r, getFont("NotoSansSemiBold", 12))
    elif toprank is not None:
        w, h = adraw.textsize(str(pp),defaultBoldFont)
        adraw.text(((832 - w) / 2, (208 - h) / 2), "{}pp".format(pp), defaultBoldFont)
        r = " PB#{}!".format(toprank)
        w , h = adraw.textsize(r,getFont("NotoSansSemiBold", 12))
        adraw.text(((842 - w) / 2, (258 - h) / 2), r, getFont("NotoSansSemiBold", 12))
    else:
        w, h = adraw.textsize(str(pp),defaultBoldFont)
        adraw.text(((832 - w) / 2, (228 - h) / 2), "{}pp".format(pp), defaultBoldFont)
    # Draw if FC Stats
    new300 = int(res[num]['count300']) + int(res[num]['countmiss'])
    iffcstats = {"count50": res[num]['count50'], "count100": res[num]['count100'], "count300": new300, "countmiss": 0}
    iffcacc = round(calculate_acc(iffcstats), 2)
    iffcinfo = await get_pyttanko(map_id=res[num]['beatmap_id'], accs=[iffcacc], mods=int(res[num]['enabled_mods']),
                                  fc=True)
    iffcpp = round(float(iffcinfo['pp'][0]), 2)
    w, h = adraw.textsize(str(iffcpp),defaultFont)
    adraw.text(((832 - w) / 2, (350 - h) / 2), "{}pp".format(iffcpp), defaultFont)
    w, h = adraw.textsize(str(iffcacc),getFont("NotoSansLight",10))
    adraw.text(((800 - w) / 2, (410 - h) / 2), "If FC with {}%".format(iffcacc), smallestFont)
    # Draw URL
    adraw.text((13, 282), "Generated using Cubchoo: https://github.com/dain98/Cubchoo-disc", smallestFont)
    # Draw Difficulty
    adraw.text((404, 19), "{}*".format(srating),bigFont)
    # Draw Map completion
    adraw.text((271, 192), "{:.2f}%".format(complete), getFont("NotoSansLight",16))
    # Draw Accuracy
    adraw.text((150, 193), "{:.2f}%".format(acc), getFont("NotoSansSemiBold",16))
    # Draw Beatmap information
    if "DT" in mods:
        lnth = round(float(apibmapinfo[0]['total_length']) / 1.5)
        bpm = str(round(float(apibmapinfo[0]['bpm']) * 1.5, 2)).rstrip("0")
    elif "HT" in mods:
        lnth = round(float(apibmapinfo[0]['total_length']) / 0.75)
        bpm = str(round(float(apibmapinfo[0]['bpm']) * 0.75, 2)).rstrip("0")
    else:
        lnth = float(apibmapinfo[0]['total_length'])
        bpm = str(round(float(apibmapinfo[0]['bpm']), 2)).rstrip("0")
        if bpm.endswith("."):
            bpm = bpm[:-1]
    length = str(datetime.timedelta(seconds=lnth))
    if length[:1] == "0":
        length = length[2:]
    ar = str(round(bmapinfo['ar'], 2)).rstrip("0")
    if bpm.endswith("."):
        bpm = bpm[:-1]
    if ar.endswith("."):
        ar = ar[:-1]
    od = str(round(bmapinfo['od'], 2)).rstrip("0")
    if od.endswith("."):
        od = od[:-1]
    cs = str(round(bmapinfo['cs'], 2)).rstrip("0")
    if cs.endswith("."):
        cs = cs[:-1]
    hp = str(round(bmapinfo['hp'], 2)).rstrip("0")
    if hp.endswith("."):
        hp = hp[:-1]
    adraw.text((20, 255), "Length: {}, AR {}, OD {}, CS {}, HP {}, {} BPM".format(length, ar, od, cs, hp, bpm),getFont("NotoSansLight", 12))
    # Flush aggdraw
    adraw.flush()
    # Draw Pie
    labels = []
    incomplete = 100 - complete
    sizes = [complete,incomplete]
    colors = ['#A5A5A5',"#42454C"]
    plt.pie(sizes,colors=colors,shadow=False,startangle=90,counterclock=False)
    plt.axis('equal')
    # plt.tight_layout()
    img_id = random.randint(0, 50)
    filepath = 'cache/pie{}.png'.format(img_id)
    plt.savefig(filepath,transparent=True)
    pie = Image.open(filepath)
    pie.thumbnail((40,40), Image.ANTIALIAS)
    self.rtemplate.paste(pie, (234,189), pie)
    os.remove(filepath)
    # Draw User Image
    try:
        urllib.request.urlretrieve("https://a.ppy.sh/{}".format(user[0]['user_id']),
                                   "cache/user_{}.png".format(user[0]['user_id']))
        userimage = Image.open("cache/user_{}.png".format(user[0]['user_id']))
        userimage.thumbnail((54, 54), Image.ANTIALIAS)
        self.rtemplate.paste(userimage, (525, 107))
        os.remove("cache/user_{}.png".format(user[0]['user_id']))
    except:
        pass
    # Draw Beatmap Image
    try:
        urllib.request.urlretrieve("https://b.ppy.sh/thumb/" + str(apibmapinfo[0]['beatmapset_id']) + "l.jpg",
                                   'cache/map_{}.png'.format(apibmapinfo[0]['beatmapset_id']))
        mapimage = Image.open("cache/map_{}.png".format(apibmapinfo[0]['beatmapset_id']))
        mapimage.thumbnail((104, 78), Image.ANTIALIAS)
        self.rtemplate.paste(mapimage, (498, 7))
        os.remove("cache/map_{}.png".format(apibmapinfo[0]['beatmapset_id']))
    except:
        # print("Couldn't find a beatmap image for {}.".format(apibmapinfo[0]['beatmapset_id']))
        pass
    rankimage = Image.open("rankletters/rank" + res[num]['rank'] + ".png")
    rankimage.thumbnail((100, 100), Image.ANTIALIAS)
    self.rtemplate.paste(rankimage, (250, 70), rankimage)
    code = random.randint(100000000, 999999999)
    self.rtemplate.save("cache/score_{}.png".format(code))
    return code

def getFont(type,size,measure=False):
    font = getType(type)
    if measure:
        return ImageFont.truetype(font, size)
    else:
        return aggdraw.Font((255, 255, 255), font, size=size, opacity=255)

def getType(type):
    return "/root/Cubchoo-disc/fonts/{}.otf".format(type)

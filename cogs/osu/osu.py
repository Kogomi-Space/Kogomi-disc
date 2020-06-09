import discord
import os, sys
from .osuAPI import OsuAPI as User
from .functions import *
from .DBFunctions import *
from .MPComparer import *
from .GenerateRecentImage import _gen_rs_img, _gen_rb_img
from .SearchForUser import *
from .ommfunc import *
from redbot.core import commands, Config, checks
import math
import pandas as pd
import aiohttp
import json
import asyncio
import pyoppai
import decimal
from pbwrap import Pastebin
import textwrap
import pytesseract
import random
import pyttanko
import aggdraw
import numpy as np
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
BaseCog = getattr(commands, "Cog", object)
os.chdir("/root/Cubchoo-disc/cogs/osu/data")

# TODO:
#    > Add option for embed response, rather than image

class Osu(BaseCog):
    """Show stuff using osu!"""

    def __init__(self,bot):
        self.bot = bot
        self.header = {"User-Agent": "User_Agent"}
        self.template = Image.open("templates/template.png")
        self.rtemplate = Image.open("templates/recent.png")
        self.config = Config.get_conf(self, identifier=842364413)
        default_global = {
            "apikey": None
        }
        self.config.register_global(**default_global)
        self.config.register_user(
            username=None
        )
        self.config.register_channel(
            rmap=None
        )
        self.db = Database()

    async def message_triggered(self,message):
        if "https://osu.ppy.sh/beatmapsets/" in message.content:
            await message.add_reaction("🗺️")
            def check(reaction, user):
                return self.bot.user != user and message.channel == reaction.message.channel and str(reaction.emoji) == '🗺️'
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=600.0,check=check)
            except asyncio.TimeoutError:
                await message.remove_reaction('🗺️',self.bot.user)

            else:
                id = message.content
                id = id.split("https://osu.ppy.sh/beatmapsets/")[1].split(" ")[0].split("#osu/")[1]
                key = await self.config.apikey()
                embed = await beatmap_embed(self,key,id)
                await message.channel.send(embed=embed)

        if "https://osu.ppy.sh/ss/" in message.content:
            possible = None
            possibleDiff = None
            definite = None
            definiteDiff = None
            mapper = None
            code = random.randint(100000000,999999999)
            urllib.request.urlretrieve(message.content,"cache/ss_{}.png".format(code))
            res = pytesseract.image_to_string(Image.open("cache/ss_{}.png".format(code)),lang="eng+Aller")
            os.remove("cache/ss_{}.png".format(code))
            res = res.split("\n")
            try:
                name = res[0].split('[')
                diff = name[1].strip()
                diff = diff[:-1]
                name = name[0].strip()
                name = name.replace(' –',' -')
                name = name.replace(' –',' -')
                name = name.replace(' —',' -')
                artist = name.split(' - ')
                title = artist[1]
                artist = artist[0]
            except Exception as e:
                await couldNotFind(self,message)
                return
            try:
                for i in res:
                    if "Beatmap by" in i:
                        mapper = i.split("by")
                        mapper = mapper[1].strip()
            except:
                mapper = None
            search = "{}".format(title)
            res1 = await try_api(self,"https://bloodcat.com/osu/?mod=json&q=" + search + "&c=b&s=&m=0")
            if len(res1) == 0:
                search = "{}".format(mapper)
                res1 = await try_api(self,"https://bloodcat.com/osu/?mod=json&q=" + search + "&c=u&s=&m=0")
                if len(res1) == 0:
                    search = "{}".format(artist)
                    res1 = await try_api(self,"https://bloodcat.com/osu/?mod=json&q=" + search + "&c=b&s=&m=0")
                    if len(res1) == 0:
                        search = "{}".format(diff)
                        res1 = await try_api(self,"https://bloodcat.com/osu/?mod=json&q=" + search + "&c=s&s=&m=0")
                        if len(res1) == 0:
                            await couldNotFind(self,message)
                            return
            done = False
            for map in res1:
                if levenshtein_ratio_and_distance(map['artist'].lower(),artist.lower(),ratio_calc=True) > .8:
                    if levenshtein_ratio_and_distance(map['title'].lower(),title.lower(),ratio_calc=True) > .8:
                        for beatmap in map['beatmaps']:
                            if levenshtein_ratio_and_distance(beatmap['name'].lower(),str(diff).lower(),ratio_calc=True) > .8:
                                possible = map
                                possibleDiff = beatmap
                                if mapper is not None and levenshtein_ratio_and_distance(map['creator'].lower(),mapper.lower(),ratio_calc=True) > .8:
                                    definite = map
                                    definiteDiff = beatmap
                                    done = True
                                    break
                if done:
                    break
            if possible is None and definite is None:
                await couldNotFind(self,message)
                return
            await message.add_reaction("❗")
            def check(reaction, user):
                return self.bot.user != user and message.channel == reaction.message.channel and str(reaction.emoji) == '❗'
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=600.0,check=check)
            except asyncio.TimeoutError:
                await message.remove_reaction('❗',self.bot.user)

            else:
                if definite is not None:
                    final = definite
                    finalDiff = definiteDiff
                else:
                    final = possible
                    finalDiff = possibleDiff
                embed = await beatmap_embed(self,await self.config.apikey(),finalDiff['id'])
                await message.channel.send(embed=embed)

    @commands.command(pass_context=True)
    async def omms(self,ctx,*username_list):
        osu = User(username_list,ctx.author.id)
        if not osu.user:
            await ctx.send("**User not set, please set your osu! username using -osuset [Username]. ❌**")
            return
        res = await fetchOmmData(osu.user)
        embed = discord.Embed()
        embed.colour = 0x00FFFF
        embed.set_author(name=f"osu!matchmaking Information for {res['osuName']}",url=f"https://osu.ppy.sh/users/{res['osuId']}",icon_url=f"https://osu.ppy.sh/images/flags/{res['countryCode']}.png")
        f = []
        f.append(f"Rank: #**{res['rank']}** **{res['divisionName']}**")
        f.append(f"Rating: **{int(res['currentVisualRating'])}**")
        f.append("⸻⸻⸻⸻")
        f.append(f"**{res['wins']}**W/**{res['losses']}**L **{round(res['wins'] / (res['wins'] + res['losses']) * 100,2)}**%")
        f.append(f"Max Winstreak: **{res['maxWinstreak']}** Current Streak: **{res['currentWinstreak']}**")
        f.append("⸻⸻⸻⸻")
        f.append("**Mod Statistics**")
        f.append(fetchWinrate("Nomod",res))
        f.append(fetchWinrate("Hidden",res))
        f.append(fetchWinrate("Hard Rock",res))
        f.append(fetchWinrate("Double Time",res))
        f.append(fetchWinrate("Freemod",res))
        f.append(fetchWinrate("Tiebreaker",res))
        f.append("⸻⸻⸻⸻")
        f.append("**Most Recent Matches**")
        for match in reversed(res['lastPlayedMatches']):
            res2 = fetchMatch(await fetchOmmMatch(match),res['osuId'])
            if res2['ratingChange'] > 0:
                ratingChange = f" GAINED **{int(res2['ratingChange'])}** rating"
            elif res2['ratingChange'] < 0:
                ratingChange = f"LOST **{int(res2['ratingChange']) * -1}** rating"
            if res2['won']:
                f.append(f" ▸ vs **{res2['opponentName']}**: (**{res2['playerScore']}** - {res2['opponentScore']}) {ratingChange}")
            else:
                f.append(f" ▸ vs **{res2['opponentName']}**: ({res2['playerScore']} - **{res2['opponentScore']}**) {ratingChange}")
        embed.description = "\n".join(f)
        embed.set_thumbnail(url=f"https://a.ppy.sh/{res['osuId']}")
        lastMatch = datetime.datetime.utcfromtimestamp(res['lastPlayedMatchDate']//1000).replace(microsecond=res['lastPlayedMatchDate']%1000*1000).strftime("%b %d, %Y, %H:%M")
        embed.set_footer(text=f"Most recent match played at {lastMatch}")
        await ctx.send(embed=embed)

    @commands.command(pass_context=True)
    async def compare_mp(self,ctx):
        await ctx.send("Please input your team's MP link in this format: **[MP Link] [your team color(Blue = 1, Red = 2)]**")
        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author
        try:
            res = await self.bot.wait_for('message', check=check)
        except asyncio.TimeoutError:
            await ctx.send("Response timed out. (You took too long to respond)")
            return
        ourmp = await fetchScores(res)
        if ourmp == "InvalidURLError":
            await ctx.send("Invalid URL! :x:")
            return
        elif ourmp == "InvalidTeamIDError":
            await ctx.send("Wrong Team ID. (Blue = 1, Red = 2)")
            return
        await ctx.send("Please input their MP link. Same format.")
        theirmp = await fetchScores(res)
        if theirmp == "InvalidURLError":
            await ctx.send("Invalid URL! :x:")
            return
        elif theirmp == "InvalidTeamIDError":
            await ctx.send("Wrong Team ID. (Blue = 1, Red = 2)")
            return
        print(ourmp)
        # await ctx.send("**Result: <{}>**".format(MPCompareRes(ourmp,theirmp)))

    @commands.command(pass_context=True)
    async def sformat(self,ctx,mapID,mods = "nm"):
        mods = mods.lower()
        modnum = 0
        if mods == "hr":
            modnum = 16
        elif mods == "dt":
            modnum = 64
        res = await get_pyttanko(map_id=mapID,mods=modnum)
        key = await self.config.apikey()
        res2 = await try_api(self,f"https://osu.ppy.sh/api/get_beatmaps?k={key}&b={mapID}")
        if mods == "dt":
            lnth = round(float(res2[0]['total_length']) / 1.5)
            bpm = str(round(float(res2[0]['bpm']) * 1.5,2)).rstrip("0")
        else:
            lnth = float(res2[0]['total_length'])
            bpm = str(round(float(res2[0]['bpm']),2)).rstrip("0")
        if bpm.endswith("."):
            bpm = bpm[:-1]
        length = str(datetime.timedelta(seconds=lnth))
        if length[:1] == "0":
            length = length[2:]
        ar = str(round(res['ar'],2)).rstrip("0")
        if bpm.endswith("."):
            bpm = bpm[:-1]
        if ar.endswith("."):
            ar = ar[:-1]
        od = str(round(res['od'],2)).rstrip("0")
        if od.endswith("."):
            od = od[:-1]
        cs = str(round(res['cs'],2)).rstrip("0")
        if cs.endswith("."):
            cs = cs[:-1]
        f = []
        f.append("```")
        f.append("=HYPERLINK(\"https://osu.ppy.sh/b/{} \",\"{} - {} [{}]\")".format(mapID,res['artist'],res['title'],res['version']))
        f.append("{}".format(mapID))
        if mods == "fm":
            reshr = await get_pyttanko(map_id=mapID,mods=16)
            ar2 = str(round(reshr['ar'],2)).rstrip("0")
            if ar2.endswith("."):
                ar2 = ar2[:-1]
            od2 = str(round(reshr['od'],2)).rstrip("0")
            if od2.endswith("."):
                od2 = od2[:-1]
            cs2 = str(round(reshr['cs'],2)).rstrip("0")
            if cs2.endswith("."):
                cs2 = cs2[:-1]
            f.append("{} ★ | {} ★".format(round(float(res['stars']),2),round(float(reshr['stars']),2)))
            f.append("{}".format(bpm))
            f.append("{}".format(length))
            f.append("CS {}/{}".format(cs,cs2))
            f.append("OD {}/{}".format(od,od2))
            f.append("AR {}/{}".format(ar,ar2))
        else:
            f.append("{} ★".format(round(float(res['stars']),2)))
            f.append("{}".format(bpm))
            f.append("{}".format(length))
            f.append("CS {}".format(cs))
            f.append("OD {}".format(od))
            f.append("AR {}".format(ar))
        f.append("```")
        await ctx.send("\n".join(f))

    @commands.command(pass_context=True)
    async def osuset(self,ctx,*username_list):
        """Set your osu! username."""
        apikey = await self.config.apikey()
        if apikey is None:
            await ctx.send("No API key! Please let me know at Dain#0727.")
            return

        username = " ".join(username_list)
        if username == "":
            await ctx.send("Username can't be blank! :x:")
            return
        res = await use_api(self,ctx,"https://osu.ppy.sh/api/get_user?k={}&u={}".format(apikey,username))
        if len(res) == 0:
            await ctx.send("User not found in osu! database! :x:")
            return
        result = self.db.change_osuid(ctx.author.id,res[0]['user_id'])
        if result is True:
            await ctx.send("Added, your osu! username is set to " + res[0]['username'] + ". ✅")
        else:
            await ctx.send("Something went wrong. Contact Dain#0727 for help.")

    @commands.command()
    async def osu(self, ctx,*username_list):
        """Shows an osu user!"""
        osu = User(username_list, ctx.author.id)
        if not osu.user:
            await ctx.send("**User not set, please set your osu! username using -osuset [Username]. ❌**")
            return

        osu = await osu.getUser()

        if osu:
            # Build Embed
            embed = discord.Embed()
            embed.title = osu[0]["username"]
            embed.url = "https://osu.ppy.sh/u/{}".format(osu[0]["user_id"])
            embed.set_footer(text="Powered by osu!")
            embed.add_field(name="Join date", value=osu[0]["join_date"][:10])
            embed.add_field(name="Accuracy", value=osu[0]["accuracy"][:6])
            embed.add_field(name="Level", value=osu[0]["level"][:5])
            embed.add_field(name="Ranked score", value=osu[0]["ranked_score"])
            embed.add_field(name="Rank", value=osu[0]["pp_rank"])
            embed.add_field(name="Country rank ({})".format(osu[0]["country"]), value=osu[0]["pp_country_rank"])
            embed.add_field(name="Playcount", value=osu[0]["playcount"])
            embed.add_field(name="Total score", value=osu[0]["total_score"])
            embed.add_field(name="Total seconds played", value=osu[0]["total_seconds_played"])
            file, rankgraph = await rank_graph(osu[0]['user_id'],0)
            embed.set_image(url='attachment://{}'.format(rankgraph))
            embed.set_thumbnail(url="https://a.ppy.sh/{}".format(osu[0]["user_id"]))
            await ctx.send(file=file,embed=embed)
        else:
            await ctx.send("No results.")

    @commands.command(pass_context=True)
    async def match_costs(self,ctx,url,warmups=2):
        """Shows how well each player did in a multi lobby."""
        await _matchcosts(self,ctx,url,warmups)

    @commands.command(pass_context=True)
    async def mc(self,ctx,url,warmups=2):
        """Shows how well each player did in a multi lobby."""
        await _matchcosts(self,ctx,url,warmups)

# Grouping recent Commands
    @commands.command(pass_context=True)
    async def recent(self,ctx,*username_list):
        """Get your most recent score! -recent [count] [username]"""
        await _rcommand(self,ctx,*username_list)

    @commands.command(pass_context=True)
    async def rs(self,ctx,*username_list):
        """Get your most recent score! -recent [count] [username]"""
        await _rcommand(self,ctx,*username_list)

    @commands.command(pass_context=True)
    async def recentlist(self,ctx,*username_list):
        await _rlist(self,ctx,*username_list)

    @commands.command(pass_context=True)
    async def rslist(self,ctx,*username_list):
        await _rlist(self,ctx,*username_list)

    @commands.command(pass_context=True)
    async def rb(self,ctx,*username_list):
        await _rbcommand(self,ctx,*username_list)

    @commands.command(pass_context=True)
    async def recentbest(self,ctx,*username_list):
        await _rbcommand(self,ctx,*username_list)

    @commands.command(pass_context=True)
    async def rpassed(self,ctx,*username_list):
        await _rpassed(self,ctx,*username_list)

    @commands.command(pass_context=True)
    async def compare(self,ctx,*username_list):
        """Compare the last -recent score with your own."""
        await _cmp(self,ctx,*username_list)

    @commands.command(pass_context=True)
    async def c(self,ctx,*username_list):
        await _cmp(self,ctx,*username_list)

# Simpler Commands
    @commands.command(pass_context=True)
    async def acc(self,ctx,c300,c100,c50,cMisses):
        """Calculates your accuracy! Format: -acc [300s] [100s] [50s] [misses]"""
        temp = {
            'count300' : c300,
            'count100' : c100,
            'count50' : c50,
            'countmiss' : cMisses
        }
        await ctx.send("Your accuracy for [**{}**/**{}**/**{}**/**{}**] is **{}%**.".format(c300,c100,c50,cMisses,round(calculate_acc(temp),2)))

    @commands.command(pass_context=True)
    async def bws(self,ctx,rank,bcount):
        """Check your Badge Weighted Seeding rank. -bws [rank] [badgecount]"""
        bcount = int(bcount)
        rank = int(rank)
        newrank = bcount ** 2
        newrank = 0.9937 ** newrank
        newrank = rank ** newrank
        newrank = round(newrank)
        await ctx.send("Previous Rank: **{}**    Badge Count: **{}**".format(rank,bcount))
        await ctx.send("Rank after BWS: **{}**".format(newrank))

    @commands.command(pass_context=True)
    async def petbws(self,ctx,rank,bcount):
        """Check your Badge Weighted Seeding rank for Pls Enjoy Tournament. -petbws [rank] [badgecount]"""
        bcount = int(bcount)
        rank = int(rank)
        newrank = 1 + bcount
        newrank **= 1.06
        newrank = 0.7 ** newrank
        newrank = (0.09 * rank) ** newrank
        newrank = (0.9 * rank) / newrank
        newrank = rank - newrank
        newrank = round(newrank)
        await ctx.send("Previous Rank: **{}**    Badge Count: **{}**".format(rank,bcount))
        await ctx.send("Rank after BWS: **{}**".format(newrank))

    @commands.command()
    @checks.is_owner()
    async def osukey(self, ctx, key):
        """Set osu! api key"""

        # Load config
        config_boards = await self.config.apikey()

        # Set new config
        await self.config.apikey.set(key)
        await ctx.send("The apikey has been added.")

    async def refreshdb(self):
        await self.db.refresh()

def levenshtein_ratio_and_distance(s, t, ratio_calc = False):
    # Initialize matrix of zeros
    rows = len(s)+1
    cols = len(t)+1
    distance = np.zeros((rows,cols),dtype = int)

    # Populate matrix of zeros with the indeces of each character of both strings
    for i in range(1, rows):
        for k in range(1,cols):
            distance[i][0] = i
            distance[0][k] = k

    # Iterate over the matrix to compute the cost of deletions,insertions and/or substitutions
    for col in range(1, cols):
        for row in range(1, rows):
            if s[row-1] == t[col-1]:
                cost = 0 # If the characters are the same in the two strings in a given position [i,j] then the cost is 0
            else:
                # In order to align the results with those of the Python Levenshtein package, if we choose to calculate the ratio
                # the cost of a substitution is 2. If we calculate just distance, then the cost of a substitution is 1.
                if ratio_calc == True:
                    cost = 2
                else:
                    cost = 1
            distance[row][col] = min(distance[row-1][col] + 1,      # Cost of deletions
                                 distance[row][col-1] + 1,          # Cost of insertions
                                 distance[row-1][col-1] + cost)     # Cost of substitutions
    if ratio_calc == True:
        # Computation of the Levenshtein Distance Ratio
        Ratio = ((len(s)+len(t)) - distance[row][col]) / (len(s)+len(t))
        return Ratio
    else:
        # print(distance) # Uncomment if you want to see the matrix showing how the algorithm computes the cost of deletions,
        # insertions and/or substitutions
        # This is the minimum number of edits needed to convert string a to string b
        return "The strings are {} edits away".format(distance[row][col])

async def _matchcosts(self,ctx,url,warmups=2):
    apikey = await self.config.apikey()
    if 'https://osu.ppy.sh/community/matches' in url:
        try:
            url = url.split("matches/")
        except:
            await ctx.send("Invalid URL! :x:")
            return
        url = url[1]
    async with ctx.typing():
        res = await use_api(self, ctx, "https://osu.ppy.sh/api/get_match?k={}&mp={}".format(apikey, url))
        if res['match'] == 0:
            await ctx.send("Invalid URL! :x:")
            return
        if warmups <= 0:
            pass
        else:
            try:
                for i in range(warmups):
                    del res['games'][0]
            except Exception as e:
                pass
        if int(res['games'][0]['team_type']) == 2:
            teamVS = True
        else:
            teamVS = False
        res['games'], playerlist = parse_match(res['games'], teamVS)
        try:
            if ":" in res['match']['name']:
                name = res['match']['name'].split(":")
            else:
                name = res['match']['name'].split("(", 1)
        except:
            name = res['match']['name']
        try:
            tname = name[0]
            team1 = name[1].split("vs")
            team2 = team1[1]
            team1 = team1[0]
            team1 = ''.join(c for c in team1 if c not in ' ()')
            team2 = ''.join(c for c in team2 if c not in ' ()')
        except:
            try:
                del team1
                del team2
                del tname
            except:
                pass
            name = res['match']['name']

        if teamVS:
            userlist0, pointlist0 = sortdict(playerlist[1])
            userlist1, pointlist1 = sortdict(playerlist[2])
            f = []
            f.append(":blue_circle: **Blue Team** :blue_circle:")
            for index, player in enumerate(userlist0):
                try:
                    username = await get_username(self, ctx, player)
                except:
                    username = player + " (Banned)"
                f.append("**{}**: {:15} - **{:0.2f}**".format(index + 1, username, pointlist0[index]))
            f.append("")
            f.append(":red_circle: **Red Team** :red_circle:")
            for index, player in enumerate(userlist1):
                try:
                    username = await get_username(self, ctx, player)
                except:
                    username = player + " (Banned)"
                f.append("**{}**: {:15} - **{:0.2f}**".format(index + 1, username, pointlist1[index]))
            f = "\n".join(f)
            try:
                embed = discord.Embed(title="<a:mLoading:529680784194404352> {}: {} vs {}".format(tname, team1, team2),
                                      url="https://osu.ppy.sh/mp/" + url,
                                      description=f)
            except:
                embed = discord.Embed(title="<a:mLoading:529680784194404352> {}".format(name),
                                      url="https://osu.ppy.sh/mp/" + url,
                                      description=f)
        else:
            userlist, pointlist = sortdict(playerlist)
            f = []
            for index, player in enumerate(userlist):
                try:
                    username = await get_username(self, ctx, player)
                except:
                    username = player + " (Banned)"
                f.append("**{}**: {:15} - **{:0.2f}**".format(index + 1, username, pointlist[index]))
            f = "\n".join(f)
            try:
                embed = discord.Embed(title="<a:mLoading:529680784194404352> {}: {} vs {}".format(tname, team1, team2),
                                      url="https://osu.ppy.sh/mp/" + url,
                                      description=f)
            except:
                embed = discord.Embed(title="<a:mLoading:529680784194404352> {}".format(name),
                                      url="https://osu.ppy.sh/mp/" + url,
                                      description=f)

        await ctx.send(embed=embed)

async def _rlist(self,ctx,*username_list):
    username = get_osuid(*username_list,db=self.db,discid=ctx.author.id)
    if not username:
        await ctx.send("**User not set! Please set your osu! username using -osuset [Username]! ❌**")
        return
    async with ctx.typing():
        apikey = await self.config.apikey()
        user = await use_api(self,ctx,"https://osu.ppy.sh/api/get_user?k={}&u={}".format(apikey,username))
        if len(user) == 0:
            await ctx.send("User not found! :x:")
            return
        res = await use_api(self,ctx,"https://osu.ppy.sh/api/get_user_recent?k={}&u={}".format(apikey,username))
        if len(res) == 0:
            await ctx.send("No recent plays found for {}. :x:".format(username))
            return
        embed=discord.Embed(description="Recent scores for [{}](https://osu.ppy.sh/users/{})".format(user[0]['username'],user[0]['user_id']),color=0x00ffff)
        embed.set_thumbnail(url="https://a.ppy.sh/{}".format(user[0]['user_id']))
        for idx,i in enumerate(res):
            acc = round(calculate_acc(res[idx]),2)
            totalhits = (int(res[idx]['count50']) + int(res[idx]['count100']) + int(res[idx]['count300']) + int(res[idx]['countmiss']))
            if res[idx]['perfect'] == 1:
                fc = True
            else:
                fc = False
            res2 = await get_pyttanko(res[idx]['beatmap_id'],accs=[int(acc)],mods=int(res[idx]['enabled_mods']),misses=int(res[idx]['countmiss']),combo=int(res[idx]['maxcombo']),completion=totalhits,fc=fc)
            embed.add_field(name="**{}.** {} - {} [{}] {}".format(idx + 1,res2['artist'],res2['title'],res2['version'],rank_to_emote(res[0]['rank'])), value="◆ **{}** ◆ **{}**/{}x ◆ **{}**%".format(format(int(res[idx]['score']),',d'),res[idx]['maxcombo'],res2['max_combo'],acc), inline=False)
            if idx == 4:
                break
        await ctx.send(embed=embed)

async def _rcommand(self,ctx,*username_list):
    apikey = await self.config.apikey()
    try:
        if username_list[0].isdigit():
            num = int(username_list[0]) - 1
            username_list = username_list[1:]
        else:
            num = 0
    except:
        num = 0
        pass
    username = get_osuid(*username_list,db=self.db,discid=ctx.author.id)
    if not username:
        await ctx.send("**User not set! Please set your osu! username using -osuset [Username]! ❌**")
        return
    async with ctx.typing():
        user = await use_api(self,ctx,"https://osu.ppy.sh/api/get_user?k={}&u={}".format(apikey,username))
        if len(user) == 0:
            await ctx.send("User not found! :x:")
            return
        userbest = await use_api(self,ctx,"https://osu.ppy.sh/api/get_user_best?k={}&u={}&limit=100".format(apikey,username))
        if len(userbest) == 0:
            await ctx.send("User not found! :x:")
            return
        res = await use_api(self,ctx,"https://osu.ppy.sh/api/get_user_recent?k={}&u={}".format(apikey,username))
        if len(res) == 0:
            await ctx.send("No recent plays found for {}. :x:".format(username))
            return
        if len(res) <= num:
            await ctx.send("**{}** doesn't seem to have a #{} recent play. The latest score I could find was #{}.".format(username,num + 1,len(res)))
            return
        code = await _gen_rs_img(self,ctx,num,user,apikey,userbest,res,True)
        msg = await ctx.send(file=discord.File('cache/score_{}.png'.format(code)))
    await self.config.channel(ctx.channel).rmap.set(res[num]['beatmap_id'])
    await msg.add_reaction("🗺️")
    def check(reaction, user):
        return self.bot.user != user and msg.id == reaction.message.id and str(reaction.emoji) == '🗺️'
    try:
        reaction, user = await self.bot.wait_for('reaction_add', timeout=600.0,check=check)
    except asyncio.TimeoutError:
        await msg.remove_reaction('🗺️',self.bot.user)

    else:
        async with ctx.typing():
            embed = await beatmap_embed(self,apikey,res[num]['beatmap_id'])
            await ctx.send(embed=embed)
    os.remove('cache/score_{}.png'.format(code))

async def _rpassed(self,ctx,*username_list):
    apikey = await self.config.apikey()
    try:
        if username_list[0].isdigit():
            num = int(username_list[0]) - 1
            username_list = username_list[1:]
        else:
            num = 0
    except:
        num = 0
        pass
    username = get_osuid(*username_list,db=self.db,discid=ctx.author.id)
    if not username:
        await ctx.send("**User not set! Please set your osu! username using -osuset [Username]! ❌**")
        return
    async with ctx.typing():
        user = await use_api(self,ctx,"https://osu.ppy.sh/api/get_user?k={}&u={}".format(apikey,username))
        if len(user) == 0:
            await ctx.send("User not found! :x:")
            return
        userbest = await use_api(self,ctx,"https://osu.ppy.sh/api/get_user_best?k={}&u={}&limit=100".format(apikey,username))
        if len(userbest) == 0:
            await ctx.send("User not found! :x:")
            return
        res = await use_api(self,ctx,"https://osu.ppy.sh/api/get_user_recent?k={}&u={}".format(apikey,username))
        if len(res) == 0:
            await ctx.send("No recent plays found for {}. :x:".format(username))
            return
        while(True):
            if len(res) <= num:
                break
            elif res[num]['rank'] == "F":
                num += 1
            else:
                break
        if len(res) <= num:
            await ctx.send("**{}** doesn't seem to have a #{} recent play. The latest score I could find was #{}.".format(username,num + 1,len(res)))
            return
        tempid = res[num]['beatmap_id']

        code = await _gen_rs_img(self,ctx,num,user,apikey,userbest,res,False)
        msg = await ctx.send(file=discord.File('cache/score_{}.png'.format(code)))
    await self.config.channel(ctx.channel).rmap.set(res[num]['beatmap_id'])
    await msg.add_reaction("🗺️")
    def check(reaction, user):
        return self.bot.user != user and msg.channel == reaction.message.channel and str(reaction.emoji) == '🗺️'
    try:
        reaction, user = await self.bot.wait_for('reaction_add', timeout=600.0,check=check)
    except asyncio.TimeoutError:
        await msg.remove_reaction('🗺️',self.bot.user)

    else:
        async with ctx.typing():
            embed = await beatmap_embed(self,apikey,res[num]['beatmap_id'])
            await ctx.send(embed=embed)
    os.remove('cache/score_{}.png'.format(code))

async def _rbcommand(self,ctx,*username_list):
    apikey = await self.config.apikey()
    try:
        if username_list[0].isdigit():
            num = int(username_list[0]) - 1
            username_list = username_list[1:]
        else:
            num = 0
    except:
        num = 0
        pass
    username = get_osuid(*username_list,db=self.db,discid=ctx.author.id)
    if not username:
        await ctx.send("**User not set! Please set your osu! username using -osuset [Username]! ❌**")
        return
    async with ctx.typing():
        user = await use_api(self,ctx,"https://osu.ppy.sh/api/get_user?k={}&u={}".format(apikey,username))
        if len(user) == 0:
            await ctx.send("User not found! :x:")
            return
        temp = await use_api(self,ctx,"https://osu.ppy.sh/api/get_user_best?k={}&u={}&limit=100".format(apikey,username))
        if len(temp) == 0:
            await ctx.send("User not found! :x:")
            return
        res = sorted(temp, key=lambda x: datetime.datetime.strptime(x['date'], '%Y-%m-%d %H:%M:%S'), reverse=True)
        code = await _gen_rb_img(self,ctx,num,user,apikey,temp,res)
        msg = await ctx.send(file=discord.File('cache/score_{}.png'.format(code)))
    await self.config.channel(ctx.channel).rmap.set(res[num]['beatmap_id'])
    await msg.add_reaction("🗺️")
    def check(reaction, user):
        return self.bot.user != user and msg.channel == reaction.message.channel and str(reaction.emoji) == '🗺️'
    try:
        reaction, user = await self.bot.wait_for('reaction_add', timeout=600.0,check=check)
    except asyncio.TimeoutError:
        await msg.remove_reaction('🗺️',self.bot.user)

    else:
        async with ctx.typing():
            embed = await beatmap_embed(self,apikey,res[num]['beatmap_id'])
            await ctx.send(embed=embed)
    os.remove('cache/score_{}.png'.format(code))

async def _cmp(self,ctx,*username_list):
    apikey = await self.config.apikey()
    rmap = await self.config.channel(ctx.channel).rmap()
    username = get_osuid(*username_list,db=self.db,discid=ctx.author.id)
    if not username:
        await ctx.send("**User not set! Please set your osu! username using -osuset [Username]! ❌**")
        return
    if rmap is None:
        await ctx.send("**No previous -recent command found for this channel.**")
        return
    async with ctx.typing():
        scores = await use_api(self,ctx,"https://osu.ppy.sh/api/get_scores?k={}&u={}&b={}".format(apikey,username,rmap))
        if len(scores) == 0:
            await ctx.send("**No scores found for this map. :x:**")
            return
        f = []
        count = 1
        for i in scores:
            mods = str(",".join(num_to_mod(i['enabled_mods'])))
            if mods == "":
                mods = "NoMod"
            acc = round(calculate_acc(i),2)
            mapinfo = await get_pyttanko(map_id=rmap,accs=[acc],misses=int(i['countmiss']),mods=int(i['enabled_mods']),combo=int(i['maxcombo']))
            f.append("**" + str(count) + "**: **" + mods + "** [**" + str(round(mapinfo['stars'],2)) + "***]")
            rank = rank_to_emote(i['rank'])
            if i['pp'] is None:
                pp = round(mapinfo['pp'][0],2)
            else:
                pp = round(float(i['pp']),2)

            if int(i['perfect']) == 1:
                f.append(" ▸ " + rank + " ▸ **" + str(pp) + "pp** ▸ " + str(acc) + "%")
            else:
                new300 = int(i['count300']) + int(i['countmiss'])
                fcstats = { "count50":i['count50'],"count100":i['count100'],"count300":new300,"countmiss":0 }
                fcacc = round(calculate_acc(fcstats),2)
                fcinfo = await get_pyttanko(map_id=rmap,accs=[fcacc],mods=int(i['enabled_mods']),fc=True)
                fcpp = round(float(fcinfo['pp'][0]),2)
                f.append(" ▸ " + rank + " ▸ **" + str(pp) + "pp** (" + str(fcpp) + "pp for " + str(fcacc) + "% FC) ▸ " + str(acc) + "%")

            f.append("▸ " + i['score'] + " ▸ x" + i['maxcombo'] + "/" + str(mapinfo['max_combo']) + " ▸ [" + i['count300'] + "/" + i['count100'] + "/" + i['count50'] + "/" + i['countmiss'] + "]")
            timeago = time_ago(datetime.datetime.utcnow() + datetime.timedelta(hours=0), datetime.datetime.strptime(i['date'], '%Y-%m-%d %H:%M:%S'))
            f.append("▸ Score set {} Ago".format(timeago))
            count+=1
        embed = discord.Embed(colour=0xD3D3D3,title="",description="\n".join(f))
        embed.set_author(name=mapinfo['artist'] + " - " + mapinfo['title'] + "[" + mapinfo['version'] + "]",url="https://osu.ppy.sh/b/{}".format(rmap),icon_url="https://a.ppy.sh/{}".format(scores[0]['user_id']))
        tempres = await use_api(self,ctx,"https://osu.ppy.sh/api/get_beatmaps?k={}&b={}".format(apikey,rmap))
        embed.set_thumbnail(url="https://b.ppy.sh/thumb/" + str(tempres[0]['beatmapset_id']) + "l.jpg")
        await ctx.send(embed=embed)

async def couldNotFind(self,message):
    await message.add_reaction("❓")
    def check(reaction, user):
        return self.bot.user != user and message.channel == reaction.message.channel and str(reaction.emoji) == '❓'
    try:
        reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0,check=check)
    except asyncio.TimeoutError:
        await message.remove_reaction('❓',self.bot.user)
        return

    else:
        await message.channel.send("When I react to an osu! scorepost with ❓, it means that I couldn't find a link to the beatmap. If I react with a ❗, click the reaction and I'll try my best to get the beatmap to you!")
        return

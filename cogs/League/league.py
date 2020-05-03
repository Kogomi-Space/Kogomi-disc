import discord
from .emotelist import *
from redbot.core import commands, Config, checks
import os
import math
import aiohttp
import asyncio
import decimal
import json
import textwrap
import cassiopeia as cass
import random
import aggdraw
import time
import pycountry
import datetime
from PIL import Image, ImageDraw, ImageFont
import urllib.request
from redbot.core.utils.menus import menu, commands, DEFAULT_CONTROLS

BaseCog = getattr(commands, "Cog", object)

class League(BaseCog):
    """A League of Legends cog"""

    def __init__(self):
        self.header = {"User-Agent": "User_Agent"}
        self.defaultPath = "Minccino/cogs/CogManager/cogs/league/data/"
        self.config = Config.get_conf(self, identifier=298374538)
        default_global = {
            "apikey": None
        }
        self.config.register_global(**default_global)
        default_user = {
            "summoner": None,
            "region": None
        }
        self.config.register_user(**default_user)
        with open('Minccino/cogs/CogManager/cogs/League/apikey.json', 'r') as f:
            res = json.loads(f.read())
        cass.set_riot_api_key(str(res['apikey']))


    async def message_triggered(self,message):
        return

    @commands.command(pass_context=True)
    async def champ(self,ctx,key):
        """Don't worry about this"""
        champ = cass.get_champion(key=key)
        await ctx.send(champ_to_emote(champ.name))

    @commands.command(pass_context=True)
    async def summoner(self,ctx,*summoner_list):
        """Look up a summoner."""
        summoner = " ".join(summoner_list)
        defSummoner = await self.config.user(ctx.author).summoner()
        region = await self.config.user(ctx.author).region()
        if region is None:
            await ctx.send("Your region is not set! Set your region with -setregion [region]. :x:")
            return
        if summoner == "":
            if defSummoner is None:
                await ctx.send("Your summoner is not set! Set your region with -setsummoner [summoner]. :x:")
                return
            summoner = defSummoner
        async with ctx.typing():
            summ = cass.get_summoner(name=summoner,region=region)
            if not summ.exists:
                await ctx.send("Summoner not found! :x:")
                return
            rank = summ.ranks
            entries = summ.league_entries
            # lastRank = summ.rank_last_season
            embed = discord.Embed()
            embed.colour = 0xC0C0C0
            if region == "KR":
                embed.set_author(name="Summoner Information for {}".format(summ.name),url="https://op.gg/summoner/userName={}".format(summ.name.replace(" ","%20")))
            else:
                embed.set_author(name="Summoner Information for {}".format(summ.name),url="https://{}.op.gg/summoner/userName={}".format(region.lower(),summ.name.replace(" ","%20")))
            f = []
            f.append("Region **{}**".format(region))
            f.append("Level **{}**".format(summ.level))
            if len(entries) is not 0:
                f.append("⸻⸻⸻⸻")
                f.append("**Current Season:**")
            for league in entries:
                f.append(" ▸ **{}**:".format(prettier_rank(league.queue.value)))
                f.append(" ▸ ⠀{}, {}**{}** **{}LP**".format(league.league.name,tier_to_emote(league.tier),league.division,league.league_points))
                if league.promos is not None:
                    series = league.promos.progress
                    f.append(" ▸ ⠀{}".format(convert_series(series)))
                winrate = league.wins + league.losses
                winrate = league.wins / winrate
                winrate *= 100
                f.append(" ▸ ⠀**{}**W/**{}**L **{}**% {}".format(league.wins,league.losses,round(winrate,2),convert_signs(league.fresh_blood,league.hot_streak,league.inactive,league.veteran)))
            f.append("⸻⸻⸻⸻")
            f.append("**Top 3 Champion Masteries**")
            cMastery = summ.champion_masteries
            i = 0
            while i < 3:
                f.append(" ▸ **{}** **{}** | **{:,}** points".format(mastery_to_emote(cMastery[i].level),champ_to_emote(cMastery[i].champion.name),cMastery[i].points))
                i+=1
            embed.description = "\n".join(f)
            embed.set_thumbnail(url=summ.profile_icon.url)
            embed.set_footer(text="{} | Default Summoner: {} | Default Region: {}".format(ctx.author,defSummoner,region))
            await ctx.send(embed=embed)

    @commands.command(pass_context=True)
    async def setregion(self,ctx,region):
        """Set your default region."""
        region = region.upper()
        if check_region(region) is False:
            await ctx.send("That's not a valid region! :x:")
            return
        await self.config.user(ctx.author).region.set(region)
        await ctx.send("Your region has been set to {}. :white_check_mark:".format(region))

    @commands.command(pass_context=True)
    async def setsummoner(self,ctx,*summoner_list):
        """Set your default summoner."""
        summoner = " ".join(summoner_list)
        if summoner == "":
            await ctx.send("Summoner cannot be blank! :x:")
            return
        await self.config.user(ctx.author).summoner.set(summoner)
        await ctx.send("Your summoner has been set to {}. :white_check_mark:".format(summoner))

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def leaguekey(self,ctx,key):
        """Don't worry about this either"""
        cass.set_riot_api_key(key)
        await self.config.apikey.set(key)
        await ctx.send("Your API key has been set.")

def check_region(region):
    if region == "NA": return True
    if region == "BR": return True
    if region == "EUNE": return True
    if region == "EUW": return True
    if region == "LAN": return True
    if region == "TR": return True
    if region == "LAS": return True
    if region == "OCE": return True
    if region == "RU": return True
    if region == "KR": return True
    if region == "JP": return True
    return False

def convert_signs(new,streak,inactive,veteran):
    emotes = ""
    if new:
        emotes += ":new: "
    if streak:
        emotes += ":fire: "
    if inactive:
        emotes += ":skull_crossbones: "
    if veteran:
        emotes += ":older_man: "
    return emotes
def convert_series(series):
    emotes = ""
    i = 0
    while i < 5:
        if i >= len(series):
            emotes += ":white_large_square: "
        elif series[i] is True:
            emotes += ":white_check_mark: "
        elif series[i] is False:
            emotes += ":negative_squared_cross_mark: "
        i+=1

    return emotes

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

def prettier_rank(rank):
    if rank == "RANKED_SOLO_5x5": return "Solo Queue"
    if rank == "RANKED_FLEX_SR": return "Flex Queue"
    if rank == "RANKED_TFT": return "Teamfight Tactics"

    return rank

async def set_key(self):
    key = await self.config.apikey()
    await self.config.apikey.set(key)

import discord
import time
import requests
import json
import os
import random
from redbot.core import commands, Config, checks
import matplotlib.pyplot as plt
import aiohttp
import urllib.request
from bs4 import BeautifulSoup
import re
import datetime
import subprocess
from random import seed
from random import randint
from .DBFunctions import *

from redbot.core.utils.menus import menu, commands, DEFAULT_CONTROLS
seed(1)
BaseCog = getattr(commands, "Cog", object)


class Simpletools(BaseCog):
    """Just testing out V3"""

    def __init__(self):
        self.config = Config.get_conf(self, identifier=192837472)
        self.defaultPath = "cogs/CogManager/cogs/osu/data/"
        default_global = {"userid": ""}
        self.config.register_global(**default_global)
        self.config.register_user(
            username=None
        )

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def checkinfo(self,ctx,discid):
        res = fetch_info(discid)
        await ctx.send("\n".join(res))

    @commands.command(pass_context=True)
    async def fetch_data(self, ctx):
        if ctx.message.guild:
            await ctx.send("This command is only available through DMs.")
            return
        res = fetch_info(ctx.author.id)
        if not res:
            await ctx.send("You don't seem to have any data saved onto Kogomi.")
            return
        await ctx.send("\n".join(res))

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def pull(self,ctx):
        cmd = ['git','pull','origin']
        os.chdir("/root/Cubchoo-disc")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        o, e = proc.communicate()
        await ctx.send("Output: {}".format(o.decode('ascii')))
        await ctx.send("Error: {}".format(e.decode('ascii')))
        await ctx.send("Code: {}".format(proc.returncode))

    async def cmd_triggered(self,ctx):
        if randint(0,20) == 0:
            await ctx.send(":sneezing_face:...")
            time.sleep(0.5)

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def cdownsec(self,ctx,seconds):
        seconds = int(seconds)
        mins, secs = divmod(seconds,60)
        timeformat = '{:02d}:{:02d}'.format(mins, secs)
        msg = await ctx.send(timeformat)
        while seconds:
            mins, secs = divmod(seconds,60)
            timeformat = '{:02d}:{:02d}'.format(mins, secs)
            await msg.edit(content=timeformat)
            time.sleep(1)
            seconds -= 1
        await msg.edit(content="00:00")

    @commands.command(pass_context=True)
    async def testembed(self,ctx):
        embed=discord.Embed(description="by [Hollow Wings](https://osu.ppy.sh/users/416662)\nDownload: [official](https://osu.ppy.sh/d/180138) ([no vid](https://osu.ppy.sh/d/180138n)) ", color=0x00ffff)
        embed.set_author(name="Halozy - Genryuu Kaiko",url="https://osu.ppy.sh/beatmapsets/180138#osu/433005")
        embed.set_thumbnail(url="https://b.ppy.sh/thumb/180138l.jpg")
        embed.add_field(name="Higan Torrent", value="◆ 7.3***** ◆ **Length:** 5:02\n◆ **AR** 9.6, ◆ **OD** 8, ◆ **HP** 6, ◆ **CS** 4\n◆ **474.68pp** for 95%, ◆ **529.64pp** for 99%, ◆ **557.12pp** for SS", inline=False)
        await ctx.send(embed=embed)

    @commands.command(pass_context=True)
    async def generate(self,ctx):
        try:
            vcid = ctx.message.author.voice.channel.id
            serverid = ctx.message.guild.id
            async with ctx.typing():
                embed = discord.Embed()
                embed.title = "Video Chat/Screen Share Link"
                embed.description = "[Click Here!](https://discordapp.com/channels/{}/{})".format(serverid,vcid)
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send("You're not in a voice channel! :x:")
            print(e)


    @commands.command(pass_context=True)
    async def degenerate(self,ctx):
        await ctx.send("-__               -")

    @commands.command(pass_context=True)
    async def timeutc(self,ctx):
        time = datetime.datetime.utcnow()
        await ctx.send("The current time is **{}/{}/{} {:02d}:{:02d}** UTC.".format(time.month,time.day,time.year,time.hour,time.minute))

    @commands.command(pass_context=True)
    async def tocelsius(self,ctx,fahrenheit):
        celsius = int(fahrenheit) - 32
        celsius *= (5/9)
        await ctx.send("{:d}°F is {:d}°C. ".format(fahrenheit,celsius))

    @commands.command(pass_context=True)
    async def tofahrenheit(self,ctx,celsius: int):
        fahrenheit = (int(celsius) * (9/5)) + 32
        await ctx.send("{:d}°C is {:d}°F. ".format(celsius,fahrenheit))

    @commands.command(pass_context=True)
    async def getgraph(self,ctx,*username_list):
        """Returns URL for osu! user header"""
        username = " ".join(username_list)
        async with aiohttp.ClientSession() as session:
            async with session.get('https://osu.ppy.sh/users/{}/{}'.format(username,'osu')) as resp:
                text = await resp.read()
                res = BeautifulSoup(text.decode('utf-8'),'lxml')
        script = res.find("script", {"id": "json-rankHistory"}, type='application/json')
        web_data = json.loads(script.text)
        rank_data = web_data['data']
        base = datetime.datetime.today()
        date_list = [base - datetime.timedelta(days=x) for x in range(0, 90)]
        date_list = date_list[::-1]
        fig = plt.figure(figsize=(6, 2))
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
        filepath = self.defaultPath + 'cache/rank_{}.png'.format(img_id)
        fig.savefig(filepath, transparent=True)
        plt.close()
        await ctx.send(file=discord.File(filepath))
        os.remove(filepath)

    @commands.command(pass_context=True)
    async def avatar(self, ctx, user: discord.Member = None):
        """Returns the user's avatar"""
        if user == None:
            user = ctx.message.author
            avURL = user.avatar_url
        else:
            avURL = user.avatar_url
        embed = discord.Embed()
        async with ctx.typing():
            time.sleep(1)
            embed.title = "{}'s Avatar".format(user)
        embed.set_image(url=avURL)
        await ctx.send(embed=embed)

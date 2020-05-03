import discord
import time
import requests
import json
import coc
import os
import random
from redbot.core import commands, Config, checks
import matplotlib.pyplot as plt
import aiohttp
import urllib.request
from bs4 import BeautifulSoup
import re
import datetime
from redbot.core.utils.menus import menu, commands, DEFAULT_CONTROLS

BaseCog = getattr(commands, "Cog", object)


class Coc(BaseCog):
    """Just testing out V3"""

    def __init__(self):
        self.config = Config.get_conf(self, identifier=209348585)
        with open('cogs/coc/apikey.json', 'r') as f:
            res = json.loads(f.read())
        client = coc.login(str(res['user']),str(res['pass']),client=coc.EventsClient)
        default_global = {"userid": ""}
        self.config.register_global(**default_global)
        self.config.register_user(
            username=None
        )

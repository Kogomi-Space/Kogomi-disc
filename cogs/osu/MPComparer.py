from pastebin import PastebinAPI
from .functions import *

def MPCompareRes(mp1,mp2):
    f = []
    for match in mp1['games']:
        for match2 in mp2['games']:
            if match2['beatmap_id'] == match['beatmap_id']:
                mod = num_to_mod(match['mods'])

async def fetchScores(res):
    res = res.content.split()
    if 'https://osu.ppy.sh/community/matches' in res[0]:
        try:
            url = res[0].split("matches/")
        except:
            return "InvalidURLError"
        mp = url[1]
        mp = await popotherteam(mp, res[1])
        if not mp:
            return "InvalidTeamIDError"
        return mp

async def popotherteam(mpurl, teamID):
    if teamID != 1 or teamID != 2:
        return False
    print(teamID)
    mp = try_api(await fetch_json(mpurl))
    mp.pop('match')
    for idx,game in enumerate(mp['games']):
        if game['team_type'] != 2:
            mp['games'].pop(idx)
        for idx2,score in enumerate(games['scores']):
            if score['team'] == 0:
                mp['games'].pop(idx)
            elif int(scores['team']) != teamID:
                mp['games'][idx]['scores'].pop(idx2)
    return mp
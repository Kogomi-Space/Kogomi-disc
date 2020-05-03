from .DBFunctions import *

def get_osuid(*username_list,discid):
    username = " ".join(username_list)
    if username == "":
        user = fetch_osuid(discid)
        return user
    return username
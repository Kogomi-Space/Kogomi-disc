def get_osuid(*username_list,db,discid):
    username = " ".join(username_list)
    if username == "":
        user = db.fetch_osuid(discid)
        return user
    return username
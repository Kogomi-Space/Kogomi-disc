import mysql.connector
from pbwrap import Pastebin
import asyncio
import os

class Database():
    def __init__(self):
        self.db = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd=os.environ['DEFAULTPWORD'],
            database="Cubchoo"
        )
        self.cursor = self.db.cursor()

    def fetch_pb(self):
        pb = Pastebin('')
        pb.authenticate(os.environ['DEFAULTUSER'],os.environ['PBINKEY'])
        return pb

    async def refresh(self):
        while True:
            print("Refreshing DB...")
            self.db = mysql.connector.connect(
                host="localhost",
                user="root",
                passwd=os.environ['DEFAULTPWORD'],
                database="Cubchoo"
            )
            self.cursor = self.db.cursor()
            print("Complete.")
            await asyncio.sleep(86400)

    def fetch_osuid(self,discid):
        sql = "SELECT osuid FROM users WHERE discid = '{}'".format(discid)
        self.cursor.execute(sql)
        res = self.cursor.fetchall()
        if len(res) == 0:
            return False
        return res[0][0]

    def change_osuid(self,discid,osuid):
        try:
            if not self.create_user(discid,osuid):
                sql = "UPDATE users SET osuid = '{}' WHERE discid = '{}'".format(osuid,discid)
                self.cursor.execute(sql)
                self.db.commit()
            return True
        except Exception as e:
            print(e)
            return False

    def create_user(self,discid,osuid = None,loluser = None,lolregion = None):
        self.cursor.execute("SELECT * FROM users WHERE discid = '{}'".format(discid))
        res = self.cursor.fetchall()
        print(res)
        if len(res) == 0:
            sql = "INSERT INTO users (discid, osuid, loluser, lolregion) VALUES (%s, %s, %s, %s)"
            val = (discid,osuid,loluser,lolregion)
            self.cursor.execute(sql,val)
            self.db.commit()
            return True
        return False

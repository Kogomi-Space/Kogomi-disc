import mysql.connector
import os
db = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd=os.environ['DEFAULTPWORD'],
        database="Cubchoo"
    )
cursor = db.cursor()

def fetch_info(discid):
    cursor.execute("SHOW COLUMNS FROM users")
    columns = cursor.fetchall()
    cursor.execute("SELECT * FROM users WHERE discid ='{}'".format(discid))
    data = cursor.fetchall()
    if len(data) == 0:
        return False
    f = []
    f.append("```")
    idx = 0
    for columnname in columns:
        f.append("{}: {}".format(columnname[0],data[0][idx]))
        idx += 1
    f.append("```")
    return f

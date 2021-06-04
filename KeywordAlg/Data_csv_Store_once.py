# coding: utf-8
import mysql.connector
import pandas as pd

'''
創立summary資料庫存放新聞標題/內容/向量/分群

#db = mysql.connector.connect(
#  host = "127.0.0.1",
#  user = "root",
#  password = "Asfgjk123465",
#  )
#cursor=db.cursor()
#cursor.execute('CREATE DATABASE summary')
#db.close()
'''

#------------------------------------------------------------------------
db_settings = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": 'Asfgjk123465',
    "db": "summary",
    "charset": "utf8mb4"
}

##讀 csv 資料-------------------------------------------------------------------------
udn= pd.read_csv('C://Users//user/Desktop/Summary_YuTing/KeywordAlg/udn.csv')
udn_hl_tk = udn['headline_tk'].tolist()
udn_body_tk = udn['body_tk'].tolist() #print(udn_body_tk[0]) for 檢查

db = mysql.connector.connect(**db_settings)
cursor=db.cursor() # 建立Cursor物件
cursor.execute("DROP TABLE udn")
cursor.execute('CREATE TABLE udn ( id SERIAL PRIMARY KEY, headline LONGTEXT, body LONGTEXT, vector LONGTEXT, cluster INTEGER)') #建立udn Table

with db.cursor() as cursor:
    command = "INSERT INTO udn (headline, body) VALUES (%s,%s)" #一筆一筆將udn標題跟內文資料加入
    for hl, body in zip(udn_hl_tk, udn_body_tk):
        cursor.execute(
            command, (hl, body))
    db.commit() # 儲存變更

with db.cursor() as cursor:
    cursor.execute("DELETE FROM udn WHERE id IS NULL") #刪除空白資料
    db.commit()

db.close()




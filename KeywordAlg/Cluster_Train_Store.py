# coding: utf-8
import mysql.connector, pickle

import numpy as np
from collections import Counter
from random import randint

from sklearn.cluster import AgglomerativeClustering
from sklearn.svm import LinearSVC


# 資料庫設定
db_settings = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": 'Asfgjk123465',
    "db": "summary",
    "charset": "utf8mb4"
}

db = mysql.connector.connect(**db_settings)
cursor=db.cursor()
cursor.execute('SELECT vector FROM udn')#從table選向量資料
vecs = cursor.fetchall()#讀取資料存

udn_vec = []
for i,row in enumerate(vecs):#轉換向量為list of floats
    try:
        vector = row[0].split(' ')
        vector = [float(element) for element in vector]
        udn_vec.append(vector)
    except:
        print(i, row)
del vecs
db.commit()
db.close()
print('finish reading data')

#抽樣25000篇文章做分群 (抽全部記憶體不夠,若聯合報可以在server上跑的話, 可以用全部或多一點. 效果會較好)
index_sample = np.random.choice([i for i in range(len(udn_vec))],size = 25000, replace = False)
udn_vec_sample = [udn_vec[i] for i in index_sample]
udn_vec = np.array(udn_vec) #array為預測群之X需要的輸入格式
udn_vec_sample = np.array(udn_vec_sample) #array為分群需要的輸入格式

cluster_sample = list(AgglomerativeClustering(n_clusters = None, distance_threshold = 0.3, linkage = 'average', affinity = 'cosine').fit(udn_vec_sample).labels_)
cluster_sample = np.array(cluster_sample) #array為預測群之y需要的輸入格式

# 用抽樣的doc2vec向量當X, 群當y, 建立一個support vector machine model
svc = LinearSVC().fit(udn_vec_sample, cluster_sample)

#存模型
with open('./KeywordAlg/models/clustermodel.pickle', 'wb') as f:
    pickle.dump(svc, f)
f.close()

del udn_vec_sample, cluster_sample #釋放記憶體

#讀模型
with open('./KeywordAlg/models/clustermodel.pickle', 'rb') as f:
    svc = pickle.load(f)
f.close()

#用模型預測全部資料的所屬群
cluster = []
for i,vec in enumerate(udn_vec):
    cluster.append(int(svc.predict(np.array([list(vec)]))))
    if i % 10000 == 0:
        print(i)
print(len(cluster))

#分群結果存入mysql summary database 之 udn table
db = mysql.connector.connect(**db_settings)

with db.cursor() as cursor:
    cursor.execute('SET GLOBAL innodb_buffer_pool_size=268435456')
    db.commit()
    command = "UPDATE udn set cluster = (%s) where id = (%s)"

    try:
        for i in range(len(cluster)):
            c = cluster[i]
            cursor.execute(command, (c,i + 1))
            if i % 10000 == 0:
                print(i,c)
    except Exception as e:
        print(i, e)

    db.commit()
db.close()










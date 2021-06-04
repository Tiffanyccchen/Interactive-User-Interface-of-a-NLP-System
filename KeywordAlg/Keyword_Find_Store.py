# coding: utf-8
import logging
import random
import numpy as np
from math import log, exp
from collections import Counter
import mysql.connector

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level = logging.INFO)
logger = logging.getLogger('info_log')

def initOneCate(category, tmpCateName):
    '''
    建立一個類別的dictionary keys : docNum, df, score
    '''
    try:
        cate_tmp = category[tmpCateName]
    except:
        logging.info('input documents of this topic: %s'%tmpCateName)
        cate_tmp = category[tmpCateName] = {}
        cate_tmp['docNum'] = 0
        cate_tmp['df'] = {} #calculate every term's frequency
        cate_tmp['score'] = {}
    return category, cate_tmp

def computeDf(cate_tmp, termList, term_tmp, termLengthBound):
    '''
    疊加某文章所屬類別的term frequency
    '''
    for term in termList:
        if (len(term) <= termLengthBound) | (term == ''):
            continue
        try:
            if term not in term_tmp:
                (cate_tmp['df'][term]) += 1 
        except:
            (cate_tmp['df'][term]) = 1
        term_tmp.add(term)
    return cate_tmp, term_tmp

def computeLLRVar(category, tmpCateName, docLine, docNum, termLengthBound):
    '''
    增加輸入文章docLine之所屬類別tmpCateName之字典category資訊
    category: dict
    tmpCateName:輸入文章所屬類別名稱
    docLine : 文章 [word1, word2, ..., wordn]
    docNum:目前為止總文章數量
    termLengthBound: 詞彙最低要求長度
    '''
    category, cate_tmp = initOneCate(category, tmpCateName)
    term_tmp = set()
    cate_tmp, term_tmp = computeDf(cate_tmp, docLine.split(' '), term_tmp, termLengthBound)
    if len(term_tmp) > 0:
        cate_tmp['docNum'] += 1
    docNum += 1
    return category, docNum

def computeEn(docNum, sumNum):
    if not docNum:
        return 0
    tmp = float(docNum)/sumNum
    return tmp*log(tmp)

'''
def computeLLR(category, docNum):
    #for cateName in category:
        #cate_tmp = category[cateName]
        #for term in cate_tmp['df']:
            #n = cate_tmp['docNum']#docNum_i
            #n11 = cate_tmp['df'][term]
            #n10 = n - n11
            #n01 = 0
            #for cateName2 in category:
                #if ((cateName2 != cateName) and (term in category[cateName2]['df'])):
                    #n01 += category[cateName2]['df'][term]
            #n00 = docNum - n - n01
            #tmpScore = computeEn(n11,docNum)+computeEn(n10,docNum)+computeEn(n01,docNum)+computeEn(n00,docNum)
            #tmpScore -= (computeEn(n11+n10,docNum)+computeEn(n01+n00,docNum)+computeEn(n11+n01,docNum)+computeEn(n10+n00,docNum))
            #cate_tmp['score'][term] = 2.0*docNum*tmpScore
    #return category
'''
   
def computeLLR_fast(clus, category, docNum):
    '''
    建立一個類別的dictionary keys : docNum, df, score
    '''
    cate_tmp = category[clus]
    logging.info(str(clus)) # 顯示進度

    for term in cate_tmp['df']:
        n = cate_tmp['docNum'] #該類別中文章數量
        n11 = cate_tmp['df'][term] #該類別中含有該term的文章數量
        n10 = n - n11 #該類別中沒有該term的文章數量

        try:
            n01 = category[10000]['df'][term] #另一類別(在此為剩下其他所有類別抽樣1000篇)中有該term的文章數量
        except: 
            n01 = 0

        n00 = docNum - n - n01 #另一類別(在此為剩下其他所有類別抽樣1000篇)中沒有該term的文章數量
        tmpScore = computeEn(n11,docNum) + computeEn(n10,docNum) + computeEn(n01,docNum) + computeEn(n00,docNum)
        tmpScore -= (computeEn(n11+n10,docNum)+computeEn(n01+n00,docNum)+computeEn(n11+n01,docNum)+computeEn(n10+n00,docNum))
        cate_tmp['score'][term] = 2.0*docNum*tmpScore #該term的log likelihood ratio
    
    return category

    
if __name__ == '__main__':

    db_settings = {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "root",
        "password": 'Asfgjk123465',
        "db": "summary",
        "charset": "utf8mb4"
    }
    logging.info('extract keywords')
    
    db = mysql.connector.connect(**db_settings)
    cursor=db.cursor()
    cursor.execute('DROP TABLE udncluster')
    cursor.execute('CREATE TABLE udncluster ( id SERIAL PRIMARY KEY, cluster INTEGER, keyword_and_value LONGTEXT, doc_num INTEGER)')
    cursor.execute('SELECT body, cluster from udn') #將內文, 分群從資料裡撈出來
    bodies_clusters = cursor.fetchall() 
    db.commit()
    db.close()

    udn_body = []
    udn_cluster = []
    for row in bodies_clusters:
        try:
            udn_body.append(row[0])
            udn_cluster.append(int(row[1]))
        except:
            print(row)
    length = len(udn_body)

    #確認每群文章數量的中位數
    clus_docnum_dict = Counter(udn_cluster)
    median = np.median(list(clus_docnum_dict.values()))
    print(median)

    #read a line...
    logging.info('Training Data: '+str(len(udn_body)) + ' ' + str(len(udn_cluster)))

    db = mysql.connector.connect(**db_settings)
    cursor = db.cursor()
    cursor.execute('SET GLOBAL innodb_buffer_pool_size=268435456')
    command = "INSERT INTO udncluster (cluster, keyword_and_value, doc_num) VALUES (%s, %s, %s)"
    
    order_cluster = sorted(list(set(udn_cluster))) #群從小到大排列

    for clus in order_cluster:
        category = {}
        docNum=0

        clus_indexes = [i for i in range(length) if udn_cluster[i] == clus] #找出屬於該群的文章索引
        
        sample = []
        while len(sample) < 500:
            x = random.sample(range(0,length),1)
            if x not in clus_indexes and x not in sample: # 找出500篇不屬於某群的總文章數量
                sample.append(x[0])

        for index in clus_indexes:
            body = udn_body[index]
            category, docNum = computeLLRVar(category, clus, body, docNum, 1)  # 建立該群的dict

        for index in sample:
            body = udn_body[index]
            category, docNum = computeLLRVar(category, 10000, body, docNum, 1) # 建立500篇不屬於某群(一律用群10000表示)的dict
  
        category = computeLLR_fast(clus, category, docNum) #計算該群所有出現字詞的LLR

        sorted_category = sorted(category[clus]['score'].items() , key=lambda d:d[1],  reverse = True) 
        sorted_category = sorted_category[:round(len(sorted_category)*0.01)] #拿出前 1% 高 LLR 的詞彙
        logging.info(str(len(sorted_category)))

        sorted_category_str = []
        for word_val in sorted_category:
            sorted_category_str.append(word_val[0] + ' ' + str(word_val[1]))
        sorted_category_str = '\t'.join(sorted_category_str) #將詞彙串連並以str表示以便存取

        cursor.execute(command, (clus, sorted_category_str, clus_docnum_dict[clus]))

    db.commit()
    db.close()
    logging.info('keyword extraction complete')

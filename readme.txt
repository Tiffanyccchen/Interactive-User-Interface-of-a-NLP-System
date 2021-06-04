---前置作業--- 
#安裝packages:
random/ io/ imp/ sys/ os/ logging/ pickle/ json/ collections/ numpy/ pandas/ math
gensim/ sklearn/ mysql.connector/ prefixspan/ extratools/ func_timeout/ textdistance/ flask (建立本地伺服器將python演算法與前端串接)
ckiptagger/ opencc/ jieba/ pyltp

其中4種語言工具說明如下：
l. opencc : a tool for converting traditional Chinese charaters into simplified Chinese charaters.
https://github.com/yichen0831/opencc-python

2. jieba : an efficient simplified Chinese tokenization tool.
https://github.com/fxsjy/jieba

3. ckiptagger : an efficient traditional Chinese tokenization tool.
https://github.com/ckiplab/ckiptagger

4. pyltp : a traditional Chinese language preprocessing utility containing tokenization, p.o.s. tagging, ne recognition , dependency parsing, etc. tools.
https://github.com/HIT-SCIR/pyltp


#安裝軟體:
MySQL

#預跑程式:
Keyword_Find_Store 裡面所有檔案, 順序：
Data_csv_Store_once.py -> Doc2Vec_Train_Store.py -> Cluster_Train_Store.py -> Keyword_Find_Store.py

---執行--- 
PIESim_kernel.py 程式 -> 顯示 Running on xxxxx 即可輸入網址 xxxxx 跑出網頁進行摘要

---資料庫設定--- -> 這部分可能都要改, 根據你的設定
db_settings = {
    #本地電腦主機 
    "host": "127.0.0.1",
    "port": 3306,

    "user": "root",

    #資料庫密碼
    "password": 'Asfgjk123465',

    #我用的database名稱
    "db": "summary",

    #使資料庫可以存中文字
    "charset": "utf8mb4"
}

---進步部分--- 

#關鍵字產生
用隨機一部分文章(25000/ 492997)下去分群
用隨機一部分文章(500 篇 不屬於某群的總文章數量)下去分群找關鍵字
因為記憶體的限制

->改進方向
在server上跑或平行運算(?
分群跟關鍵字找尋品質應可大大提升 (目前的觀察是並沒有很準確)

#壓縮演算法/ 核心演算法調整
看懂了以後就可以再去根據聯合報要求做更客製化、有效的修改(如果有需要的話)
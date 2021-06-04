# coding: utf-8
import mysql.connector
from d2v_helper import train_doc2vec, get_doc2vec_model, infer_vecs, dmdbow_str

'''
從資料庫讀取全部udn資料並且訓練doc2vec模型，得到每一篇文章的向量

#db = mysql.connector.connect(**db_settings)
#cursor=db.cursor()
#cursor.execute('SELECT body FROM udn')
#udn_body = cursor.fetchall()
#udn_body_tk = []
#for row in udn_body:
    #udn_body_tk.append(row[0].split(' '))
#del udn_body
#db.commit()
#db.close()

#t = time.time()
#train_doc2vec(udn_body_tk, "d2v_dm.model", VEC_SIZE = 50, WINDOW = 3, DM = 1, EPOCHS = 10)
#print('Time to train the model: {} mins'.format(round((time.time() - t) / 60, 2)))

#t = time.time()
#train_doc2vec(udn_body_tk, "d2v_dbow.model", VEC_SIZE = 50, WINDOW = 3, DM = 0, EPOCHS = 10)
#print('Time to train the model: {} mins'.format(round((time.time() - t) / 60, 2)))
#del udn_body_tk
'''

#讀Doc2vec models---------------------------------------------
model_dm = get_doc2vec_model('C:/Users/user\Desktop\Summary_YuTing\KeywordAlg\models\d2v_dm.model')
model_dbow = get_doc2vec_model('C:/Users/user\Desktop\Summary_YuTing\KeywordAlg\models\d2v_dbow.model')
docs_length = len(model_dm.docvecs)

db_settings = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": 'Asfgjk123465',
    "db": "summary",
    "charset": "utf8mb4"
}
db = mysql.connector.connect(**db_settings)


#存入所有文章向量資料------------------------------------------
with db.cursor() as cursor:
    cursor.execute('SET GLOBAL innodb_buffer_pool_size=268435456') #為了update全部資料
    db.commit()
    command = "UPDATE udn set vector = (%s) where id = (%s)"
    try:
        for i in range(docs_length):
            vec = dmdbow_str(i, model_dm, model_dbow)
            cursor.execute(
            command, (vec,i + 1))
            #記錄進度
            if i % 10000 == 0:
                print(i,len(vec))
    except Exception as e:
        print(i, e)
    db.commit()
db.close()

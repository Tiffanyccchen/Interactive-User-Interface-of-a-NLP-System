# -*- coding: utf-8 -*-
import re,imp, os
import numpy as np

from SummaryHelpers.rep_score_text import rep_text_func, rep_query_title_func, rep_compressiontext_func, sort_sent_func, insert_compression, score_coverage_func, score_outside_func
import SummaryHelpers.summary_generation
imp.reload(SummaryHelpers.summary_generation)
from SummaryHelpers.summary_generation import find_single_news_summary_PIESim

from KeywordAlg.d2v_helper import get_doc2vec_model, infer_vecs
from sklearn.svm import LinearSVC
model_dm = get_doc2vec_model('C:/Users/user\Desktop\Summary_YuTing\KeywordAlg\models\d2v_dm.model')
model_dbow = get_doc2vec_model('C:/Users/user\Desktop\Summary_YuTing\KeywordAlg\models\d2v_dbow.model')

import pickle
#load cluster prediction model
with open('./KeywordAlg/models/clustermodel.pickle', 'rb') as f:
    svc = pickle.load(f)
f.close()

import mysql.connector
db_settings = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": 'Asfgjk123465',
    "db": "summary",
    "charset": "utf8mb4"
}

from flask import Flask, render_template, request
import json
app = Flask(__name__)

#只要.js file 有更新refresh後都會實時載入
def dir_last_updated(folder):
    return str(max(os.path.getmtime(os.path.join(root_path, f))
                   for root_path, dirs, files in os.walk(folder)
                   for f in files))

# record last vals -> 若在同一篇多次做不同設定 -> 實時載入
last_text, last_rep_text, last_user_text, last_paragraph_text, last_sent_punc_text, last_keyword_value_dict_text  = [], [], [], [], [], {}
last_compression_text, last_compression_word_idxs, last_user_compression_text, last_user_compression_word_idxs, last_compression_float, last_pos_text = [], [], [], [], [], []

last_text_mat, last_text_val = [], []
last_query, last_rep_query, last_query_val = [], [], []
last_query_no, last_rep_query_no, last_query_val_no = [], [], []
last_title, last_rep_title, last_title_val = [], [], []

sum_idxs, sum_text = [], ''

@app.route('/def', methods = ['POST'])
def highlight():
    '''
    滑鼠按到需參照該文字框內容highlight原文時的函數 : 標題、關鍵字、摘要
    '''
    text = request.form['text']
    selector = request.form['selector']
    match_idxs = []

    if selector == 'summary highlightref':
        global sum_idxs, last_sent_punc_text, last_user_text, last_compression_float, last_user_compression_word_idxs
        
        cum_len = 0
        last_idx = -1

        # 若壓縮程度為 0 (直接選句子)
        if last_compression_float == 0.0:
            for idx in sum_idxs: 

                # 加上上一次選擇的句子到這次選擇的句子間的長度
                if last_idx == -1:
                    cum_len += sum([len(last_sent_punc_text[i]) for i in range(0, 2 * idx)])
                else:
                    cum_len += sum([len(last_sent_punc_text[i]) for i in range(2 * last_idx, 2 * idx)])

                match_idxs.append((cum_len, cum_len + len(''.join(last_user_text[idx]))))
                last_idx = idx
        else:
            for idx in sum_idxs: 
                ext_sent = last_user_text[idx]

                #算每個詞不包括自己前面詞累積的總長度
                ext_sent_cumlen = [sum([len(word) for word in ext_sent[:i]]) for i in range(len(ext_sent))]

                # 加上上一次選擇的句子到這次選擇的句子間的長度
                if last_idx == -1:
                    cum_len += sum([len(last_sent_punc_text[i]) for i in range(0, 2 * idx)])
                else:
                    cum_len += sum([len(last_sent_punc_text[i]) for i in range(2 * last_idx, 2 * idx)])

                for word_idx in last_user_compression_word_idxs[idx]:  
                    start_idx = ext_sent_cumlen[word_idx]
                    match_idxs.append((cum_len + start_idx, cum_len + start_idx + len(ext_sent[word_idx])))   
               
                last_idx = idx        

    else:
        global last_title, last_rep_title, last_query, last_rep_query, last_query_no, last_rep_query_no
        context = request.form['highlightreftext']

        #滑鼠點在標題
        if  selector == 'title highlightref':
            if last_title != context :
                rep_context = rep_query_title_func(context, False)
                last_title, last_rep_title = context, rep_context
            else:
                rep_context = last_rep_title

        #滑鼠點在關鍵詞    
        elif selector == 'neckeywordls[] highlightref':
            if last_query != context :
                rep_context = rep_query_title_func(context, True)
                last_query, last_rep_query = context, rep_context
            else:
                rep_context = last_rep_query
        else:
            if last_query_no != context :
                rep_context = rep_query_title_func(context, True)
                last_query_no, last_rep_query_no = context, rep_context
            else:
                rep_context = last_rep_query_no

        rep_context_word = set([word for sent in rep_context for word in sent])  

        for word in rep_context_word:
            match_idxs.extend([(index.start(), index.start() + len(word)) for index in re.finditer(word, text)])
        
        match_idxs = sorted(match_idxs, key = lambda pair : pair[0])

        #確認無要標示的片段範圍無前後重疊 (會發生的情形 ex. 我們 我)
        delete_idxs, add_idxs = set(),  set()
        for i, base_match in enumerate(match_idxs):
            for check_match in match_idxs[i + 1:]:
                if base_match[1] > check_match[0]:
                    add_idxs.add((base_match[0], check_match[1]))
                    delete_idxs.add(base_match)
                    delete_idxs.add(check_match)

        for pair in delete_idxs:
            match_idxs.remove(pair)
        for pair in add_idxs:
            match_idxs.append(pair)

        match_idxs = sorted(match_idxs, key = lambda pair : pair[0])

    return {'match_idxs' : json.dumps(match_idxs)}

@app.route('/abc', methods = ['POST'])
def refresh():
    '''
    按摘要按鈕時的執行函式
    '''
    # declare global variables
    global last_text, last_rep_text, last_user_text, last_paragraph_text, last_sent_punc_text, last_keyword_value_dict_text
    global last_compression_text, last_compression_word_idxs, last_user_compression_text, last_user_compression_word_idxs, last_compression_float, last_pos_text
    global last_text_mat, last_text_val
    global last_query, last_rep_query, last_query_val, last_query_no, last_rep_query_no, last_query_val_no, last_title, last_rep_title, last_title_val        
    global sum_idxs, sum_text

    # update 標題
    title = request.form['titletext']
    if last_title != title :
        rep_title = rep_query_title_func(title, False) 
    else:
        rep_title = last_rep_title
    
    # update原文輸入
    text = request.form['text']
    if last_text != text:
        user_text, paragraph_text, sent_punc_text = rep_text_func(text, False, False, False)

        #doc2vec input: 沒有分句 -> a list of words
        user_text_docvecinput = [word for sent in user_text for word in sent]

        #store sql/ find/ retrivekeywords
        #docvec-> svcfindcluster-> retrivekeywordsifdocnum < 10-> addtocompression-> patternselection
        docvec_text = infer_vecs(user_text_docvecinput, model_dm, model_dbow)
        clus_text = int(svc.predict(np.array([docvec_text])))

        db = mysql.connector.connect(**db_settings)
        with db.cursor() as cursor:
            command = "INSERT INTO udn (headline, body, vector, cluster) VALUES (%s,%s,%s,%s)"
            rep_title_str = ' '.join([' '.join(sent) for sent in rep_title])
            user_text_str = ' '.join([' '.join(sent) for sent in user_text])
            docvec_text_str = ' '.join([str(d) for d in docvec_text])
            cursor.execute(command, (rep_title_str, user_text_str, docvec_text_str, clus_text))
            command = "SELECT keyword_and_value, doc_num from udncluster where cluster = (%s)"
            cursor.execute(command, (clus_text,))
            keyword_and_value_doc_num = cursor.fetchall()[0]
            keyword_and_value = keyword_and_value_doc_num[0]
            doc_num = keyword_and_value_doc_num[1]
            db.commit()
        db.close()
        del rep_title_str, user_text_str, docvec_text_str, clus_text, keyword_and_value_doc_num

        #該群要有keyword 且 文章數量 要 >= 10 才會考慮 (有足夠代表性)
        if len(keyword_and_value) > 0 and doc_num >= 10:
            keyword_and_value = keyword_and_value.split('\t')
            keyword_and_value = [(key_val.split(' ')[0], float(key_val.split(' ')[1])) for key_val in keyword_and_value]
            keyword_value_dict_text = dict(keyword_and_value)
            del keyword_and_value

            min_val = min(list(keyword_value_dict_text.items()), key = lambda x : x[1])[1]
            max_val = max(list(keyword_value_dict_text.items()), key = lambda x : x[1])[1]
            
            #scale down keyword value range 從 1-2
            keyword_value_dict_text = dict([(word, round((val - min_val) / (max_val - min_val) + 1, 4)) for word, val in keyword_value_dict_text.items()])

            rep_text = rep_text_func(text, True, True, keyword_value_dict_text)
        else:
            keyword_value_dict_text = {}
            rep_text = rep_text_func(text, True, False, False)
        
        #得到文章句子相似度矩陣集分數
        text_mat, text_val = score_coverage_func(rep_text) 
    
    #文章跟上次按摘要時一樣 -> 直接取用上次運算結果
    else:
        rep_text, user_text, paragraph_text, sent_punc_text, keyword_value_dict_text, compression_text, compression_word_idxs, pos_text = last_rep_text, last_user_text, last_paragraph_text, last_sent_punc_text, last_keyword_value_dict_text, last_compression_text, last_compression_word_idxs, last_pos_text
        text_mat, text_val = last_text_mat, last_text_val

    # update使用者輸入
    query = request.form['querytext']
    if last_query != query:
        rep_query = rep_query_title_func(query, True)
    else:
        rep_query = last_rep_query      
        
    # update使用者輸入 no
    query_no = request.form['querynotext']
    if last_query_no != query_no:
        rep_query_no = rep_query_title_func(query_no, True)
    else:
        rep_query_no = last_rep_query_no

    title_val = score_outside_func(user_text, rep_title) 
    query_val = score_outside_func(user_text, rep_query)  
    query_val_no = score_outside_func(user_text, rep_query_no)     
    
    # update 壓縮內容跟詞位置 based on keywords and queries
    if 'compressionval' in request.form.keys():  
        compression_float = float(request.form['compressionval'])
    else:
        compression_float = 0.0
    
    #得到壓縮內容、詞在原句位置、原句中每詞的詞性
    if last_text != text or last_compression_float != compression_float:
        compression_text, compression_word_idxs, pos_text  = rep_compressiontext_func(user_text, compression_float)  
    else:     
        compression_text, compression_word_idxs, pos_text = last_compression_text, last_compression_word_idxs, last_pos_text
    
    #若沒有使用者輸入關鍵字或分群關鍵字 -> 不用安插關鍵字到有含關鍵字的句子
    if rep_query == [[]] and rep_query_no == [[]] and keyword_value_dict_text == {}:
        user_compression_text, user_compression_word_idxs = compression_text, compression_word_idxs
    else:
        if rep_query != [[]] or keyword_value_dict_text != {}:
            #只有分群關鍵字
            if rep_query == [[]]:
                inserts = list(keyword_value_dict_text) 
            #一定有輸入關鍵字
            else:
                inserts = rep_query + list(keyword_value_dict_text)
            #安插關鍵字到有含關鍵字的句子, update 詞位置 
            user_compression_text, user_compression_word_idxs = insert_compression(inserts, user_text, compression_text, compression_word_idxs ,True)
        
        if rep_query_no != [[]]:
            #移除關鍵字到有含關鍵字且壓縮後該詞有被選的句子, update 詞位置 
            user_compression_text, user_compression_word_idxs = insert_compression(rep_query_no, user_text, user_compression_text, user_compression_word_idxs ,False)
    
    # update parameters  
    if 'queryval' in request.form.keys():  
        query_float = float(request.form['queryval'])# 必要關鍵詞(句)強度
    else:
        query_float = 0.25

    if 'querynoval' in request.form.keys():  
        query_no_float = float(request.form['querynoval'])# 省略關鍵詞(句)強度
    else:
        query_no_float = 0.25

    if 'centval' in request.form.keys():  
        cent_float = float(request.form['centval'])# 相關詞(句)覆蓋強度
    else:
        cent_float = 0.75

    if 'positionval' in request.form.keys():  
        position_float = float(request.form['positionval'])# 第一段落強度
    else:
        position_float = 0.25

    if 'redundantval' in request.form.keys():      
        redundant_float = float(request.form['redundantval'])# 省略重複字(詞)強度
    else:
        redundant_float = 0.25

    if 'charnumval' in request.form.keys() and request.form['charnumval'] != '':      
        char_num_float = float(request.form['charnumval'])# 字數  
    else:
        char_num_float = 150
    
    # store data in global variables
    last_text, last_rep_text, last_user_text, last_paragraph_text, last_sent_punc_text, last_keyword_value_dict_text = text, rep_text, user_text, paragraph_text, sent_punc_text, keyword_value_dict_text
    last_compression_text, last_compression_word_idxs, last_user_compression_text, last_user_compression_word_idxs, last_compression_float, last_pos_text = compression_text, compression_word_idxs, user_compression_text, user_compression_word_idxs, compression_float, pos_text
    last_text_mat, last_text_val = text_mat, text_val    
    last_query, last_rep_query, last_query_val = query, rep_query, query_val
    last_query_no, last_rep_query_no, last_query_val_no = query_no, rep_query_no, query_val_no
    last_title, last_rep_title, last_title_val = title, rep_title, title_val

    # update摘要  
    if compression_float == 0.0 : 
        (sum_idxs, sum_text, paragraph_cumlen) = find_single_news_summary_PIESim(cent_float, query_float, query_no_float, position_float, redundant_float, char_num_float, text_val, query_val, query_val_no, title_val, user_text, user_text, paragraph_text, text_mat, pos_text)  
    else : 
        (sum_idxs, sum_text, paragraph_cumlen) = find_single_news_summary_PIESim(cent_float, query_float, query_no_float, position_float, redundant_float, char_num_float, text_val, query_val, query_val_no, title_val, user_compression_text, user_text, paragraph_text, text_mat, pos_text)    

    # 摘要選句間若有跨段落 -> 標示在摘要輸出中
    if text : 

        last_sent_par_idx = 0
        last_idx = 0
        return_sum_text = []

        #iterate 所有選到的句子indexes
        for i, idx in enumerate(sum_idxs):
            j = 0
            # 若該選句大於現在這個段落 -> 移到下一個段落 -> 跨段落了
            while idx > paragraph_cumlen[j]:
                j += 1
                
            #若上一個選的句子不是某段落的終結句 (為何檢查： 因為如此的話本身自帶換行 ->  就不用加了)
            if j > last_sent_par_idx and last_idx not in paragraph_cumlen:
                return_sum_text.append('\n\n' + ''.join(sum_text[i]) + sent_punc_text[2 *idx + 1]) 
            else:
                return_sum_text.append(''.join(sum_text[i]) + sent_punc_text[2 *idx + 1]) 

            last_sent_par_idx = j
            last_idx = idx

        #最後一個句子的標點符號長度 * -1
        last_punc_len = int(len(sent_punc_text[2 *sum_idxs[-1] + 1]) * -1)

        #將最後一句標點符號刪掉並加上句號
        return {'summary':''.join(return_sum_text)[:last_punc_len] + '。'}

    else:
        return {'error':'沒有輸入內容!'}

@app.route('/')
def index():
    return render_template('PIESim.html',last_updated=dir_last_updated('./static'))

if __name__ == '__main__':
    app.run()     
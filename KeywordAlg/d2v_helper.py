# coding: utf-8
import os, logging
from gensim.test.utils import common_texts
from gensim.models.doc2vec import Doc2Vec, TaggedDocument

def train_doc2vec(CORPUS, MODEL_NAME, VEC_SIZE=50, DM = 1, WINDOW =3, min_count = 1, EPOCHS=100):
    '''
    訓練模型
    corpus : [word 1, word 2,...,...word n]
    vec_size, window, min_count, epochs 都可調整
    '''
    model = Doc2Vec(vector_size=VEC_SIZE, DM = DM, window = WINDOW, min_count = min_count, worker = 1)
    documents = [TaggedDocument(doc, [i]) for i, doc in enumerate(CORPUS)]
    model.build_vocab(documents)
    model.corpus_count
    model.train(documents, total_examples=model.corpus_count, epochs=EPOCHS)
    model.save(MODEL_NAME)
    
    print("model finished")


def get_doc2vec_model(MODEL_NAME):
    '''
    得到儲存在路徑下的doc2vec model
    '''
    model = Doc2Vec.load(MODEL_NAME)
    return model

def infer_vecs(words, model_dm, model_dbow):
    '''
    得到一篇新文章向量 (目前是輸出list type, 也可改成 string type)
    '''
    vecs = []
    model_dm.random.seed(0)
    model_dbow.random.seed(0)
    vec_dm = model_dm.infer_vector(words)
    vec_dbow = model_dbow.infer_vector(words)
    vec_all = list(vec_dm) + list(vec_dbow)
    vecs += list(vec_all)
    return vecs

def dmdbow_str(i, model_dm, model_dbow):
    '''
    得到模型裡面第i篇文章之向量
    '''
    D = list(model_dm.docvecs[i]) + list(model_dbow.docvecs[i])
    d2v = " ".join([str(d) for d in D])
    return d2v
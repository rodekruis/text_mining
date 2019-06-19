# -*- coding: utf-8 -*-
"""
Created on Wed May 22 16:09:09 2019

@author: LuisaB
"""


import os
import nltk
from nltk import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet

#code partly from here: https://simonhessner.de/lemmatize-whole-sentences-with-python-and-nltks-wordnetlemmatizer/

#Function for assigning POS tags
lemmatizer = WordNetLemmatizer()

def nltk2wn_tag(nltk_tag):
    if nltk_tag.startswith('J'):
        return wordnet.ADJ
    elif nltk_tag.startswith('V'):
        return wordnet.VERB
    elif nltk_tag.startswith('N'):
        return wordnet.NOUN
    elif nltk_tag.startswith('R'):
        return wordnet.ADV
    else:          
        return None   

#Function for tokenizing file, removing stopwords and lemmatization
def tok_stop_lem(file):
    #lemmatization
    lemmatizer = WordNetLemmatizer()
    nltk_tagged = nltk.pos_tag(nltk.word_tokenize(file))  
    wn_tagged = map(lambda x: (x[0], nltk2wn_tag(x[1])), nltk_tagged)
    res_words = []
    for word, tag in wn_tagged:
        if tag is None:            
          res_words.append(word)
        else:
          res_words.append(lemmatizer.lemmatize(word, tag))
    new_doc = " ".join(res_words)
    #tokenizing
    tokenized_doc = word_tokenize(new_doc)
    #removing stopwords
    stop_words = nltk.corpus.stopwords.words('english')
    new_doc = [w for w in tokenized_doc if not w in stop_words]
    joined_doc = ' '.join(new_doc)
    return joined_doc
    
    
#Applying the functions to all files
directory = os.chdir(#path to folder with files)
documents = os.listdir(os.getcwd())
NLP_dir = #path to new folder

for i in documents:
    path = os.getcwd() + '\\' + i
    print(path)
    doc = open(path, 'r', encoding='utf-8')
    content_doc = doc.read()
    NLP_file = tok_stop_lem(content_doc)
    new_filename = NLP_dir + '\\' + i
    os.makedirs(os.path.dirname(new_filename), exist_ok=True)
    with open(new_filename, "w", encoding='utf-8') as f:
        f.write(NLP_file)
    doc.close()    


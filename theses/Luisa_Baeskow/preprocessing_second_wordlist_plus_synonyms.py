# -*- coding: utf-8 -*-
"""
Created on Wed May 22 16:44:08 2019

@author: LuisaB
"""

#Applying NLP to wordlist from Red Cross and creating synonyms

import os
import nltk
from nltk import word_tokenize
from nltk.stem import WordNetLemmatizer
import pandas as pd



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

path = #path to wordlist

opening_doc = open(path, 'r', encoding='utf-8')
content_doc = opening_doc.read()
new_doc = tok_stop_lem(content_doc)
with open(path, "w", encoding='utf-8') as f:
    f.write(new_doc)
print(new_doc)
opening_doc.close()

#Splitting the string into a list of words
word_list = new_doc.split()
print(word_list)



#Create dataframe out of the list
df_conseq_words = pd.DataFrame(word_list, columns=['keyterms'])
#Setting the index to the first column to get rid of the indices
df_conseq_words.set_index('keyterms',inplace=True)
#Turning the rows into columns
df_conseq_words = df_conseq_words.transpose()
#Saving as csv file
df_conseq_words.to_csv(#path to new file)

word_list = pd.read_csv(#path to df_conse_words file)


#Reading all VCA files at once
directory = os.chdir(#path to all files)
documents = os.listdir(os.getcwd())

content_all_docs = []
for i in documents:
    path = os.getcwd() + '\\' + i
    print(path)
    doc = open(path, 'r', encoding='utf-8')
    content_doc = doc.read()
    content_all_docs.append(content_doc)
    doc.close()
print(content_all_docs)


print(word_list)
content_all_docs = str(content_all_docs)

#Checking if trigger word appears in any file
clean_list = []
for i in word_list:
    if i in content_all_docs:
        clean_list.append(i)
print(clean_list)

#Create dataframe out of the list
df_clean_words = pd.DataFrame(clean_list, columns=['keyterms'])
#Setting the index to the first column to get rid of the indices
df_clean_words.set_index('keyterms',inplace=True)
#Turning the rows into columns
df_clean_words = df_clean_words.transpose()
#Saving as csv file
df_clean_words.to_csv(#path to new file)
        
        

## ----- Creating Synonyms -------

#Loading the consequence words
conseq_words = pd.read_csv(#path to file)

list_conseq_words = list(conseq_words)
print(list_conseq_words)


##Creating a list of synonyms for consequence words
from nltk.corpus import wordnet

synonyms = []

for i in conseq_words:
    for syn in wordnet.synsets(i):
        for l in syn.lemmas():
            synonyms.append(l.name())
        

synonyms = set(synonyms)
synonyms = list(synonyms)

#Applying NLP function on the list of words
from nltk import word_tokenize
import nltk
from nltk.stem import WordNetLemmatizer 
import pandas as pd


synonym_str = ""
for i in synonyms:
    synonym_str += i+" "
print(synonym_str)
    
synonym_str = synonym_str.lower()
synonyms_nlp = tok_stop_lem(synonym_str)

#Splitting the string into a list of words
syn_list = synonyms_nlp.split()
print(syn_list)


#Check if they appear somewhere in the VCA documents
directory = os.chdir(#path to folder of VCA files)
documents = os.listdir(os.getcwd())

content_all_docs = []
for i in documents:
    path = os.getcwd() + '\\' + i
    print(path)
    doc = open(path, 'r', encoding='utf-8')
    content_doc = doc.read()
    content_all_docs.append(content_doc)
    doc.close()
print(content_all_docs)

content_all_docs = str(content_all_docs)

clean_list = []
for i in syn_list:
    if i in content_all_docs:
        clean_list.append(i)
print(clean_list)

automatic_wordlist_df = pd.DataFrame(clean_list, columns=['keyterms'])

#Creating a dataframe out of the keywords

#Setting the index to the first column to get rid of the indices
automatic_wordlist_df.set_index('keyterms',inplace=True)

#Using the column values as column names
automatic_wordlist_df = automatic_wordlist_df.transpose()

#Saving the final syn list
automatic_wordlist_csv = automatic_wordlist_df.to_csv(#path to new csv file)

automatic_syns = pd.read_csv(#path to automatic_wordlist_csv file)
automatic_syns = automatic_syns.drop(columns="Unnamed: 0")

automatic_syns_list = list(automatic_syns)


#Counting how often the syn words appear in the docs

output_conseq = pd.DataFrame()
for i in documents:
    path = os.getcwd() + '\\' + i
    print(path)
    frame = pd.read_csv(path)
    frame['filename'] = os.path.basename(path)
    doc = open(path, 'r', encoding='utf-8')
    content = doc.read()
    content_split = content.split()
    mylist = [item for item in content_split if item in automatic_syns_list]
    print(mylist)
    counts = dict()
    counts['VCA file name'] = i #This adds the column with the filename
    for j in mylist:
        counts[j] = counts.get(j, 0) + 1

    output_conseq = output_conseq.append(counts, ignore_index=True)

print(output_conseq)



#Replacing missing values with zeros, so that they are not represented as empty fields in the csv file

output_conseq.fillna(0, inplace=True)

output_conseq_csv = output_conseq.to_csv(#path to new file)

#Merge specific keywords and general keywords
#Using the manually shortened list of keywords with count >= 5

cyclone_values = pd.read_csv(#path to file)
syn_count = pd.read_csv(#path to file)

cyclone_auto_syn = pd.merge(cyclone_values, syn_count, left_on='VCA file name_x', right_on='VCA file name')
cyclone_auto_syn.to_csv(#path to new file)

     
        

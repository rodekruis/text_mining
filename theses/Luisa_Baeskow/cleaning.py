# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 09:54:38 2019

@author: LuisaB
"""

##Cleaning the files from unwanted characters, spaces etc.

import regex as re
import os

#Cleaning function
#Special thanks to Wilco Draijer for help with the regex!
def clean(file):
    nonascii = re.compile(r'[^\pL\s\d.,\/\\#!$%\^&\*;:{}=\-+`~()\[\]\'\"\?]+')
    punc_marks = re.compile(r'[.,\/\\#!$%\^&\*;:{}=\-+`~()\[\]\'\"\?]')                         
    noenter = re.compile(r'\\n')
    no_t = re.compile(r'\\t')
    doublespacing = re.compile(r'[ ]+')
    word_number = re.compile(r'([a-z]+)([0-9]+)')
    number_word = re.compile(r'([0-9]+)([a-z]+)')
    spaces = re.compile(r'\s+')
    others = re.compile(r'xa 0+')
    single_letters1 = re.compile(r'\s+[a-z]\s+')
    single_letters2 = re.compile(r'\s+[a-z]\s+')
    single_letters3 = re.compile(r'\s+[a-z]\s+')
    with open(file, 'r', encoding ='utf-8') as doc:
        new_content = doc.read().lower()
        text = noenter.sub(r' ',new_content)
        text = noenter.sub(r'\n', text)
        text = no_t.sub(r' ', text)
        text = no_t.sub(r'\t', text)
        text = nonascii.sub(r'',text)
        text = punc_marks.sub(r'',text)
        text = word_number.sub(r'\1 \2',text)
        text = number_word.sub(r'\1 \2',text)
        text = single_letters1.sub(r' ',text)
        text = single_letters2.sub(r' ',text)
        text = single_letters3.sub(r' ',text)
        text = spaces.sub(r' ',text)
        text = others.sub(r' ', text)
        text = doublespacing.sub(r' ',text)
    return text


#Looping over all the txt files, apply cleaning function and save in new directory.
directory = os.chdir(#path to directory)
documents = os.listdir(os.getcwd())
clean_dir = #path to new directory

for i in documents:
    try:
        path = os.getcwd() + '\\' + i
        print(path)
        doc = open(path, 'r', encoding='utf-8')
        cleaned_file = clean(path)
        print(cleaned_file)
        new_filename = clean_dir + '\\' + 'cleaned_' + i
        os.makedirs(os.path.dirname(new_filename), exist_ok=True)
        with open(new_filename, "w", encoding='utf-8') as f:
            f.write(cleaned_file)
        doc.close()
    except:
        print(path)


#Example with a single file,for demonstration purposes.  

path = #path of file
print(path)
doc = open(path, 'r', encoding='utf-8')
cleaned_file = clean(path)
print(cleaned_file)
doc.close()


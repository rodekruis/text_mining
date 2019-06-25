# -*- coding: utf-8 -*-
"""
Created on Mon Apr 29 11:23:53 2019

@author: LuisaB
"""

import wikipedia


section = wikipedia.WikipediaPage('Typhoon Saola (2012)').section('Philippines')
print(section)


#Save article as txt file
path = #path to file

with open(path + ".txt", "w", encoding='utf-8') as file1: #Opening and writing the txt files
    file1.write(section)



import regex as re


#Cleaning the file
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


path = #path to file
print(path)
doc = open(path, 'r', encoding='utf-8')
cleaned_file = clean(path)
print(cleaned_file)
with open(path, "w", encoding='utf-8') as f:
            f.write(cleaned_file)
doc.close()
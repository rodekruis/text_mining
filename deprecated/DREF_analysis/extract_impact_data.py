#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 29 17:23:42 2019

@author: jacopo
"""

import spacy
import os
from word2number import w2n
import re

#converts pdf, returns its text content as a string
def get_object(ent, sentence, doc_text):
    """get what an entity refers to within a sentence
    """
    object = ''

    # get all tokens of which entity is composed
    tokens_in_ent = []
    for idx, word in enumerate(ent):
        tokens_in_ent.append(word)

    # get last token in sentence
    for idx, word in enumerate(sentence):
        if word.text == tokens_in_ent[-1].text:
            # first attempt: look for head of type NOUN
            if word.head.pos_ == 'NOUN':
                object = word.head.text
                break
            # second attempt: navigate the children list, look for an 'of'
            for possible_of in word.children:
                if possible_of.text == 'of':
                    for possible_object in possible_of.children:
                        object = 'of ' + possible_object.text
                        break

    return object

def process_number_words(text_raw):
    """convert text into an actual number
    """

    # make lowercase, remove commas
    text = text_raw.lower()
    text = re.sub('\n', '', text)
    text = re.sub(',', '', text)
    text = text.strip()
    # print('start process_number_words on ', text)

    # fix misspelling: '30millions' --> '30 millions'
    for (number, word) in re.findall('([0-9\.]+)([a-z]+)', text):
        text = re.sub(str(number+word), str(number+' '+word), text)

    # special case: 'between x and y' --> '(x+y)/2'
    for (x_text, y_text) in re.findall('between\s([0-9a-z\s\-]+)\sand\s([0-9a-z\s\-]+)', text):
        try:
            x = w2n.word_to_num(x_text)
            y = w2n.word_to_num(y_text)
            text = str((x+y)/2.)
            return text
        except ValueError:
            print('number conversion failed (special case *between*): ', text)
            return text

    # special case: 'x per cent'
    for perc in re.findall('([0-9a-z\-]+)\sper\scent', text):
        try:
            text = str(w2n.word_to_num(perc)) + '%'
            return text
        except ValueError:
            print('number conversion failed (special case *per cent*): ', text)
            return text

    # word_to_num not working, need to convert string to number
    for (number, word) in re.findall('([0-9\.]+)\s([a-z]+)', text):
        number_old = number
        if 'billion' in word:
            number = str(float(number)*1000000000)
        if 'million' in word:
            number = str(float(number)*1000000)
        if 'thousand' in word:
            number = str(float(number)*1000)
        text = re.sub(str(number_old+' '+word), number, text)

    # try first if it can be directly converted
    try:
        text = str(w2n.word_to_num(text))
    except ValueError:
        # remove words that cannot be converted to numbers: 'more than seven' --> 'seven'
        text_clean = ''
        for word in re.findall('[a-z0-9\-]+', text):
            try:
                w2n.word_to_num(word)
                text_clean += word
                if re.search(r'\d', word) is None:
                    text_clean += ' '
            except ValueError:
                continue

        # try to convert what is left into one number
        try:
            text = str(w2n.word_to_num(text_clean))
        except ValueError:
            # if we have a vague number word: assign a reasonable number
            if 'billions' in text:
                text = '2000000000'
            elif 'millions' in text:
                text = '2000000'
            elif 'hundreds of thousands' in text:
                text = '200000'
            elif 'tens of thousands' in text:
                text = '20000'
            elif 'thousands' in text:
                text = '2000'
            elif 'hundreds' in text:
                text = '200'
            elif 'dozens' in text:
                text = '24'
            elif 'tens' in text:
                text = '20'
            elif 'dozen' in text:
                text = '12'
            else:
                print('number conversion failed (', text, ') !!!')
                text = re.sub('[^0-9\.]+', '', text)
    return text
    
#converts all pdfs in directory pdfDir, saves all resulting txt files to txtdir
def extract_impact_data(txtDir):
    
    # load pre-train nlp model
    nlp = spacy.load('en_core_web_sm')
    
    for text_file_name in os.listdir(txtDir): #iterate through text files
        fileExtension = text_file_name.split(".")[-1]
        fileName = ''.join(text_file_name.split(".")[:-1])
        
        if fileExtension == "txt" and 'clean' in fileName:
            text_file = open(txtDir+text_file_name,"r")
            text = text_file.read()
    
            doc = nlp(text)
            
            # loop over sentences
            for sentence in doc.sents:
                
                # ******************************************************************
                # loop over numerical entities,
                # check if it's impact data and if so, add to dataframe
                for ent in filter(lambda w: (w.label_ == 'CARDINAL'), sentence.as_doc().ents):
                    
                    # get entity text and clean it
                    ent_text = re.sub('\n', '', ent.text).strip()
                    if ent_text == '':
                        continue
                    number = '' # number associated to entity
                    
                    # get what the number refers to
                    object  = get_object(ent, sentence, text)
                    number = process_number_words(ent_text)
                    
                    if (object != '') & (number != ''):
                        print(number, object)
    
            text_file.close()
            
txtDir = "./data/"
extract_impact_data(txtDir)

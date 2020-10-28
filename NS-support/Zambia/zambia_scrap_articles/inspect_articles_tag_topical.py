#!/usr/bin/env python
# coding: utf8
from __future__ import unicode_literals, print_function

import plac
import random
from pathlib import Path
import spacy
import re
import os
import codecs
from nltk.tokenize import sent_tokenize
import json
import sys
from spacy import displacy
from newspaper import Article
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import pandas as pd
pd.set_option('display.max_columns', 5)
pd.set_option('max_colwidth', 18)
pd.set_option('expand_frame_repr', True)
from dateutil.parser import parse
from datetime import datetime
from types import *

def main():
    """Inspect articles and decide if relevant
    add corresponding boolean (topical) to dataframe
    """

    newspaper_titles = ['TimesOfZambia', 'ZambiaDailyMail', 'ZambianWatchdog', 'LusakaTimes']
    # newspaper_titles = ['ZambianObserver']

    for newspaper_title in newspaper_titles:
        df_articles = pd.read_hdf('Articles/'+newspaper_title+'/articles_all.h5')
        print("Analysing {0}".format('Articles/'+newspaper_title+'/articles_all.h5'))
        var_topical_bool = []

        for index, article in df_articles.iterrows():
            print(article['title'])
            var_topical = input("Is it topical? t (True), f (False), i (Inspect text)  ")
            if var_topical == 'i':
                print(article['text'])
                var_topical = input("Is it topical? t (True), f (False)  ")
            var_topical_bool.append(var_topical=='t')

        print(df_articles.head())
        df_articles_topical = df_articles.assign(topical = var_topical_bool)
        print(df_articles_topical.head())

        output_dir_topical = 'Articles/'+newspaper_title+'/articles_all_topical.h5'
        print("Saving all articles to {0}".format(output_dir_topical))
        df_articles_topical.to_hdf(output_dir_topical, key='df', mode='w')

if __name__ == '__main__':
    plac.call(main)

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
pd.set_option('display.max_columns', 4)
pd.set_option('max_colwidth', 18)
pd.set_option('expand_frame_repr', True)
from dateutil.parser import parse
from datetime import datetime
from types import *
from datetime import datetime
from dateutil.parser import parse

with open('zambia_wards_districts/Zambia_locations.json', "r") as f:
    locations = json.loads(f.read())
wards = locations['Wards']
districts = locations['Districts']
provinces = locations['Provinces']
titles = ['Mr', 'Mrs', 'Ms', 'Miss', 'Senator', 'President', 'Minister', 'Councillor', 'Mayor', 'Governor', 'Secretary', 'Attorney', 'Chancellor', 'Judge', 'Don', 'Father', 'Dr', 'Doctor', 'Prof', 'Professor']

def FindLocations(target_text):
    """Find locations of interest in a given text,
    after applying some preprocessing
    """

    target_text_edit = target_text
    # filter names with titles (Mr., Ms. ...)
    # important: some people have names of towns!
    for title in titles:
        target_text_edit = re.sub(title+'\.\s[A-Za-z]+\s[A-Z][a-z]+', '', target_text_edit)
        target_text_edit = re.sub(title+'\s[A-Za-z]+\s[A-Z][a-z]+', '', target_text_edit)
        target_text_edit = re.sub(title+'\.\s[A-Za-z]+', '', target_text_edit)
        target_text_edit = re.sub(title+'\s[A-Za-z]+', '', target_text_edit)
    # print(target_text_edit)

    # filter article signatures (ZambiaDailyMail)
    pattern_signatures_head = re.compile(r'[A-Z]+\s[A-Z]+\,\s[A-Za-z]+') # e.g. MONICA KAYOMBO, Ndola
    target_text_edit = re.sub(pattern_signatures_head, '', target_text_edit)
    pattern_signatures_foot = re.compile(r'[A-Z]+\s[A-Z]+\n\n[A-Za-z]+') # e.g. MONICA KAYOMBO \n\n Ndola
    target_text_edit = re.sub(pattern_signatures_foot, '', target_text_edit)
    # print(target_text_edit)

    # find locations
    locations_found = []
    locations_found_re = [re.search(re.compile(ward), target_text_edit) for ward in wards]
    locations_found = [word.group(0) for word in locations_found_re if word is not None]
    locations_found_re = [re.search(re.compile(district), target_text_edit) for district in districts]
    locations_found.extend([word.group(0) for word in locations_found_re if word is not None])
    locations_found_re = [re.search(re.compile(province), target_text_edit) for province in provinces]
    locations_found.extend([word.group(0) for word in locations_found_re if word is not None])
    # print(locations_found)
    return locations_found

def main():
    """Convert a list of articles from a pandas dataframe
    into a list of "events" (what, when, where, source), save as csv
    """

    df_events = pd.DataFrame(columns=['event_type', 'date', 'locations', 'source'])

    newspaper_titles = ['TimesOfZambia', 'ZambiaDailyMail', 'ZambianWatchdog', 'LusakaTimes']

    # loop over newspapers
    for newspaper_title in newspaper_titles:
        df_articles = pd.read_hdf('Articles/'+newspaper_title+'/articles_all_topical.h5')

        # select only relevant articles
        df_articles = df_articles[df_articles['topical']==True]
        print('articles:')
        print(df_articles.loc[:])

        # for each article, get publish date, list of locations and url
        for index, article in df_articles.iterrows():
            locations = FindLocations(article['text'])
            locations = list(set(locations))
            if len(locations)>0:
                df_events.loc[len(df_events)] = ['flood', pd.to_datetime(article['publish_date']), locations, article['url']]

    print('events:')
    print(df_events.loc[:])

    # save to csv
    df_events.to_csv('Zambia_flood_events.csv', date_format='%d-%m-%Y', mode='w', encoding='utf-8', index=False)

if __name__ == '__main__':
    plac.call(main)

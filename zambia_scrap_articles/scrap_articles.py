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
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
pd.set_option('display.max_columns', 4)
pd.set_option('max_colwidth', 20)
from dateutil.parser import parse
from datetime import datetime
from types import *
import time

def ProcessPage(vBrowser, vArticles_all):
    """Process search result page
    get articles and save them to a pandas dataframe (articles_page)
    (1) list results from page
    (2) loop over results, get article and store it
    (3) return dataframe
    """

    # output: pandas dataframe with title, publishing date, article text and url
    articles_page = pd.DataFrame(columns=['title', 'publish_date', 'text', 'url'])

    # 1) list results
    search_result_page_source = vBrowser.page_source
    # for ZambianObserver *********************************
    regex = re.compile('https:\/\/www\.zambianobserver\.com\/(?=\S*[-])([0-9a-zA-Z-]+)\/')
    search_results = list(set([ match[0] for match in regex.finditer(search_result_page_source) if "flood" in match[0].lower()]))
    # for TimesOfZambia ***********************************
    # search_results_we = vBrowser.find_elements_by_class_name("readmore");
    # search_results = [search_result.get_attribute("href") for search_result in search_results_we]
    # for Lusakatimes ***********************************
    # search_results_we = vBrowser.find_elements_by_class_name("td-image-wrap");
    # regex_prefilter = re.compile(r'flood', re.IGNORECASE)
    # search_results = [search_result.get_attribute("href") for search_result in search_results_we if re.search(regex_prefilter, search_result.get_attribute("title")) is not None]
    # for ZambiaDailyMail ***********************************
    # regex = re.compile('http:\/\/www\.daily-mail\.co\.zm\/(?=\S*[-])([0-9a-zA-Z-]+)\/')
    # search_results = list(set([ match[0] for match in regex.finditer(search_result_page_source) if "flood" in match[0].lower()]))
    # for ZambianWatchdog ***********************************
    # regex = re.compile('https:\/\/www\.zambiawatchdog\.com\/(?=\S*[-])([0-9a-zA-Z-]+)\/')
    # search_results = list(set([ match[0] for match in regex.finditer(search_result_page_source) if "flood" in match[0].lower()]))

    if len(search_results) > 0:
        print("found article(s):")
        for title in search_results:
            print("url: {0}".format(title))

    # 2) for each result, get article and save it
    for idx, search_result in enumerate(search_results):

        # download article
        article = Article(search_result)
        article.download()
        while article.download_state != 2: #ArticleDownloadState.SUCCESS is 2
            time.sleep(1)
        article.parse()

        # select articles with "flood"
        regex = re.compile(r'flood', re.IGNORECASE)

        if re.search(regex, article.title) is not None:

            # get date
            date = article.publish_date
            if date is not None:
                date_str = date.strftime('%m/%d/%Y')
            else:
                # for TimesOfZambia *******************************************
                # date_re = re.search('[a-zA-z]\w+\s[0-9][0-9]\,\s[0-9]{4}', article.html)
                # date_str = date_re[0]
                # for ZambiaDailyMail, LusakaTimes ****************************
                dates_all = [m.group(0) for m in re.finditer(r'[a-zA-z]\w+\s[0-9]+\,\s[0-9]{4}', article.html)]
                if len(dates_all) > 1:
                    date_str = dates_all[1]
                else:
                    date_str = ""
                # for ZambianWatchdog *****************************************
                # dates_all = [m.group(0) for m in re.finditer(r'[a-zA-z]\w+\s[0-9]+\,\s[0-9]{4}', article.html)]
                # if len(dates_all) > 1:
                #     date_str = dates_all[0]
                # else:
                #     date_str = ""
                # *************************************************************

            # fix title, if necessary (only for LusakaTimes)
            article.title = re.sub('Zambia : ', '', article.title)

            # add to dataframe
            articles_page.loc[idx] = [article.title, date_str, article.text, article.url]

            # print dataframe head, to check that things make sense
            if idx == 3:
                print(articles_page.head())

    # 3) return dataframe
    vArticles_all = vArticles_all.append(articles_page, ignore_index=True)
    return vArticles_all


@plac.annotations(
    model=("Model name. Defaults to blank 'en' model.", "option", "m", str),
    output_dir=("Optional output directory", "option", "o", Path))

def main(model='en_core_web_sm', output_dir='Articles/ZambianObserver'):
    """Scrap articles from Zambian online newspapers
    save article in pandas dataframe (articles_all)
    """

    # initialize webdriver
    opts = Options()
    opts.set_headless()
    assert opts.headless  # operating in headless mode
    browser = Firefox() # Firefox(options=opts)
    browser.get('https://www.zambianobserver.com/?s=flood') #ZambianObserver
    # browser.get('http://www.times.co.zm/?s=flood') #TimesOfZambia
    # browser.get('https://www.lusakatimes.com/ruralnews/') #LusakaTimes
    # browser.get('https://www.lusakatimes.com/other-news/') #LusakaTimes
    # browser.get('http://www.daily-mail.co.zm/?s=flood') #ZambiaDailyMail
    # browser.get('https://www.zambiawatchdog.com/?s=flood') #ZambianWatchdog

    # initialize output: pandas dataframe with title, publishing date, article text and url
    articles_all = pd.DataFrame(columns=['title', 'publish_date', 'text', 'url'])

    # process first results page
    print("Begin to process page 1 ({0})".format(browser.current_url))
    articles_all = ProcessPage(browser, articles_all)

    # start looping over all pages of results
    page_number = 2
    while True:
        time.sleep(2)
        try:
            print("Trying to open page {0} ...".format(page_number))
            # for ZambianObserver, LusakaTimes ********************************
            links = browser.find_elements_by_link_text(str(page_number))
            if len(links) == 0:
                print('Not found!')
                break
            for link in links:
                if link.get_attribute("class") == "page":
                    link.click()
            # for TimesOfZambia, ZambiaDailyMail, ZambianWatchdog *************
            # link = browser.find_element_by_link_text(str(page_number))
            # browser.get(link.get_attribute("href"))
            # *****************************************************************
        except NoSuchElementException:
            print('Not found!')
            break
        print("Begin to process page {0} ({1})".format(page_number, browser.current_url))
        articles_all = ProcessPage(browser, articles_all)
        page_number += 1
        # if page_number >= 10:
        #     break

    print("\nFINISHED PROCESSING *****************************")
    print("\nSummary")
    print(articles_all.describe())

    # save dataframe to hdf5
    output_dir_all = Path(output_dir)
    output_dir_all = output_dir_all / "articles_all.h5"
    print("Saving all articles to {0}".format(output_dir_all))
    articles_all.to_hdf(output_dir_all, key='df', mode='w')

if __name__ == '__main__':
    plac.call(main)

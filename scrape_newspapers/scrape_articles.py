#!/usr/bin/env python
# coding: utf8
from __future__ import unicode_literals, print_function

import plac
from pathlib import Path
import re
import os
import sys
from newspaper import Article
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
pd.set_option('display.max_columns', 4)
pd.set_option('max_colwidth', 20)
from datetime import datetime
import time

keyword = 'flood'
keyword_search = 'flood'
keyword_in_url = 'flood'
country='Uganda'

def is_date(string):
    try:
        pd.to_datetime(string)
        return True
    except ValueError:
        return False

def ProcessPage(vBrowser, vNews_name, vNews_url):
    """
    Process search result page
    get articles and save them to a pandas dataframe (articles_page)
    (1) list results from page
    (2) loop over results, get article
    (3) return dataframe
    """

    # output: pandas dataframe with title, publishing date, article text and url
    articles_page = pd.DataFrame(columns=['title', 'publish_date', 'text', 'url'])

    # 1) list results
    search_result_page_source = vBrowser.page_source

    # make url regex-usable
    url_any = vNews_url
    url_any = re.sub(re.escape('?s='+keyword_search), '', url_any)
    url_any = re.sub(re.escape('search?k='+keyword_search), '', url_any)
    url_any = re.sub('\?m\=[0-9]{6}', '', url_any)
    url_any = re.escape(url_any) + '(?=\S*[-])([0-9a-zA-Z-\/\.]+)'
    regex = re.compile(url_any)
    print('searching for ', url_any)
    search_results = list(set([ match[0] for match in regex.finditer(search_result_page_source) if keyword_in_url in match[0].lower()]))

    if vNews_name in ['NewVision']:
        regex = re.compile('\/new\_vision\/news\/(?=\S*[-])([0-9a-zA-Z-\/\.]+)')
        search_results = list(set([ match[0] for match in regex.finditer(search_result_page_source) if keyword_in_url in match[0].lower()]))
        search_results = ['https://www.newvision.co.ug' + search_result for search_result in search_results]

    if len(search_results) > 0:
        print("found {0} article(s):".format(len(search_results)))
        for title in search_results:
            print("url: {0}".format(title))
    else:
        print('no articles found')

    # 2) for each result, get article and save it
    for idx, search_result in enumerate(search_results):

        print('processing ', search_result)
        # download article
        article = Article(search_result)
        article.download()
        attempts = 0
        while (article.download_state != 2) & (attempts<5): #ArticleDownloadState.SUCCESS is 2
            attempts += 1
            time.sleep(1)
        if article.download_state != 2:
            print('unable to download article: ', search_result)
            continue
        article.parse()

        article_html = str(article.html)

        # select articles with keyword
        regex = re.compile(keyword, re.IGNORECASE)

        if re.search(regex, article.title) is not None:

            # print(article_html)

            # get date
            date = article.publish_date
            date_str = ""
            if date is not None:
                date_str = date.strftime('%m/%d/%Y')
            if (date is None) | (pd.to_datetime(date_str).date() == pd.to_datetime(datetime.today()).date()):
                regex_date = re.compile('[a-zA-z]\w+\s[0-9]+\,\s[0-9]{4}')
                date_re = list(set([match[0] for match in regex_date.finditer(article_html)]))
                date_re = [date for date in date_re if is_date(date)]
                if (date_re is None) | (all(pd.to_datetime(date_str).date() == pd.to_datetime(datetime.today()).date() for date_str in date_re)):
                    regex_date = re.compile('[a-zA-z]\w+\s[0-9]+\s[0-9]{4}')
                    date_re = list(set([match[0] for match in regex_date.finditer(article_html)]))
                    date_re = [date for date in date_re if is_date(date)]
                if (date_re is None) | (all(pd.to_datetime(date_str).date() == pd.to_datetime(datetime.today()).date() for date_str in date_re)):
                    regex_date = re.compile('[0-9]\w+\s[a-zA-Z]+\,\s[0-9]{4}')
                    date_re = list(set([match[0] for match in regex_date.finditer(article_html)]))
                    date_re = [date for date in date_re if is_date(date)]
                if (date_re is None) | (all(pd.to_datetime(date_str).date() == pd.to_datetime(datetime.today()).date() for date_str in date_re)):
                    regex_date = re.compile('[0-9]\w+\s[a-zA-Z]+\s[0-9]{4}')
                    date_re = list(set([match[0] for match in regex_date.finditer(article_html)]))
                    date_re = [date for date in date_re if is_date(date)]
                if (date_re is None) | (all(pd.to_datetime(date_str).date() == pd.to_datetime(datetime.today()).date() for date_str in date_re)):
                    regex_date = re.compile('[0-9]{2}\/[0-9]{2}\/[0-9]{4}')
                    date_re = list(set([match[0] for match in regex_date.finditer(article_html)]))
                    date_re = [date for date in date_re if is_date(date)]
                if (date_re is None) | (all(pd.to_datetime(date_str).date() == pd.to_datetime(datetime.today()).date() for date_str in date_re)):
                    regex_date = re.compile('[0-9]{2}\-[0-9]{2}\-[0-9]{4}')
                    date_re = list(set([match[0] for match in regex_date.finditer(article_html)]))
                    date_re = [date for date in date_re if is_date(date)]
                if date_re is not None:
                    for res in date_re:
                        if (pd.to_datetime(res).date() != pd.to_datetime(datetime.today()).date()):
                            date_str = res
                            break

            if (date_str == "") | (pd.to_datetime(date_str).date() == pd.to_datetime(datetime.today()).date()):
                print('Publication date not found or wrongly assigned, skipping article')
                continue

            # if no text is present (e.g. only video), use title as text
            article_text = article.text
            if len(str(article.text)) == 0:
                article_text = article.title

            # add to dataframe
            print(article.title, ' : ', date_str)
            articles_page.loc[idx] = [article.title, date_str, article_text, article.url]

    # 3) return dataframe
    if len(search_results) > 0:
        print(articles_page.head())
    return articles_page

################################################################################

@plac.annotations(
    model=("Model name. Defaults to blank 'en' model.", "option", "m", str),
    output_dir=("Optional output directory", "option", "o", Path))

def main(model='en_core_web_sm', output_dir='Articles_'+keyword+'_'+country):
    """
    Scrape articles from online newspapers
    save article in pandas dataframe (articles_all)
    """

    # if output directory does not exist, create it
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    # initialize webdriver
    opts = Options()
    opts.set_headless()
    assert opts.headless  # operating in headless mode
    browser = Firefox()

    # get newspapers urls
    browser.get('http://www.abyznewslinks.com/mali.htm')
    newspaper_elements = browser.find_elements_by_css_selector('a')
    newspaper_urls = [el.get_attribute('href') for el in newspaper_elements]
    newspaper_names = [el.get_attribute('text') for el in newspaper_elements]
    Newspapers = dict(zip(newspaper_names, newspaper_urls))
    Newspapers = {key:val for key, val in Newspapers.items() if 'abyznewslinks' not in val}

    # loop over newspapers
    for news_name, news_url in Newspapers.items():

        articles_news = pd.DataFrame(columns=['title', 'publish_date', 'text', 'url'])

        print('**********************************************************************************')
        print('Accessing ' + news_name + ' (' + news_url + ')')
        news_url += '?s='+keyword_search
        browser.get(news_url)

        # process first results page
        print("Begin to process page 1 ({0})".format(browser.current_url))
        articles_page = ProcessPage(browser, news_name, news_url)
        articles_news = articles_news.append(articles_page)

        # start looping over all pages of results
        page_number = 2
        while True:
            print("Trying to open page {0} ...".format(page_number))
            try:
                link = browser.find_element_by_link_text(str(page_number))
                browser.get(link.get_attribute("href"))
            except NoSuchElementException:
                url_next_page = news_url
                url_next_page = re.sub(re.escape('?s='+keyword_search), '', url_next_page)
                url_next_page = re.sub(re.escape('search?k='+keyword_search), '', url_next_page)
                url_next_page = re.escape(url_next_page) + 'page\/' + str(page_number) + '.*?(?=")'
                regex = re.compile(url_next_page)
                print('link not found, trying explicit regex: ', url_next_page)
                search_result_next_page = re.search(regex, browser.page_source)
                if search_result_next_page is None:
                    print('Not found!')
                    break
                else:
                    print(search_result_next_page[0])
                    browser.get(search_result_next_page[0])

            print("Begin to process page {0} ({1})".format(page_number, browser.current_url))
            try:
                articles_page = ProcessPage(browser, news_name, news_url)
            except:
                print('Unexpected error: ', sys.exc_info()[0])
                continue
            articles_news = articles_news.append(articles_page)
            page_number += 1

        ## save dataframe to csv
        print('Saving articles from ' + news_name)
        print(articles_news.describe())
        print('*********************************************************')
        output_dir_news = str(output_dir) + '/articles_' + keyword_in_url + '_' + news_name + '.csv'
        articles_news.to_csv(output_dir_news, sep='|')


    print("\nFINISHED PROCESSING *****************************")
    # print("\nSummary")
    # print(articles_all.describe())
    #
    # ## save dataframe to hdf5
    # output_dir_all = str(output_dir) + "/articles_" + keyword_in_url + "_all.h5"
    # print("Saving all articles to {0}".format(output_dir_all))
    # articles_all.to_hdf(output_dir_all, key='df', mode='w')

if __name__ == '__main__':
    plac.call(main)

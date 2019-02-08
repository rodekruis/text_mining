# -*- coding: utf-8 -*-
"""
Created on Fri Feb 8 14:56:54 2019

@author: Jacopo.Margutti
"""

import os
from selenium import webdriver
from selenium.webdriver import Firefox
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
pd.set_option('display.max_columns', 4)
pd.set_option('max_colwidth', 20)
import time
import re
import plac

"""
Script to download a set of documents from a webpage
using selenium and chromedriver.
get selenium with:
    pip install selenium
get chromedriver:
    download https://chromedriver.storage.googleapis.com/index.html?path=73.0.3683.20/
    move it somewhere stable (see chromedriver_location below)
    
working example on the appeals of IFRC appeals
<http://www.ifrc.org/appeals>
"""

chromedriver_location = '/usr/local/bin/chromedriver'

def main():
    
    # initialize webdriver
    ChromeOptions = webdriver.ChromeOptions()
    ChromeOptions.add_argument('--disable-browser-side-navigation')
    browser = webdriver.Chrome(chromedriver_location, chrome_options=ChromeOptions)
    
    # get webpage
    browser.get('http://www.ifrc.org/appeals')
    # wat a sec until it's fully loaded
    time.sleep(2)
    # find and downloads all links in page
    process_page(browser)
    
    # loop over all pages and do the same
    page_number = 1
    while True:
        time.sleep(2)
        try:
            print("trying to open page {0} ...".format(page_number))
            # need to use regex because f*****g selenium doesn't get page elements
            page_source = browser.page_source
            regex = re.compile('(?<=href=").+?(?=">Next)')
            urls = [match[0] for match in regex.finditer(page_source)]
            next_page_url = 'http://www.ifrc.org'+urls[0]
            browser.get(next_page_url)
        except NoSuchElementException:
            print('not found!')
            break
        print("begin to process page {0} ({1})".format(page_number, browser.current_url))
        process_page(browser)
        page_number += 1
    
###############################################################################
    
def process_page(current_browser):
    # save current url (we need to get back at the end)
    page_url = current_browser.current_url
    # find and downloads all links in page
    elems = current_browser.find_elements_by_xpath("//a[@href]")
    links = [elem.get_attribute("href") for elem in elems]
    for link in links:
        # download files
        if ('Download' in link or '/docs/' in link):
            print('downloading', link)
            current_browser.get(link)
    # get back to original page
    current_browser.get(page_url)         
            
if __name__ == '__main__':
    plac.call(main)

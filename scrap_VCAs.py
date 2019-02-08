# -*- coding: utf-8 -*-
"""
Created on Fri Feb 8 14:53:54 2019

@author: Jacopo.Margutti
"""

from selenium import webdriver
import time

"""
Script to download a set of documents from a webpage
using selenium and chromedriver.
get selenium with:
    pip install selenium
get chromedriver:
    download https://chromedriver.storage.googleapis.com/index.html?path=73.0.3683.20/
    move it somewhere stable (see chromedriver_location below)
    
working example on the VULNERABILITY CAPACITY ASSESSMENT (VCA) of IFRC
<http://vcarepository.info/find>
"""

chromedriver_location = '/usr/local/bin/chromedriver'

# initialize webdriver
ChromeOptions = webdriver.ChromeOptions()
ChromeOptions.add_argument('--disable-browser-side-navigation')
browser = webdriver.Chrome(chromedriver_location, chrome_options=ChromeOptions)

# get webpage
browser.get('http://vcarepository.info/find')
# wat a sec until it's fully loaded
time.sleep(5)
# find all links in page
elems = browser.find_elements_by_xpath("//a[@href]")
for elem in elems:
    link = elem.get_attribute("href")
    # download files
    if 'http://vcarepository.info/api/file/' in link:
        print('downloading', link)
        browser.get(link)

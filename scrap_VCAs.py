# -*- coding: utf-8 -*-
"""
Created on Fri Feb 8 14:53:54 2019

@author: Jacopo.Margutti
"""
# coding: utf8
from __future__ import unicode_literals, print_function

import os
from selenium import webdriver
from selenium.webdriver import Firefox
import pandas as pd
pd.set_option('display.max_columns', 4)
pd.set_option('max_colwidth', 20)
import time

"""
Script to download a set of documents from a webpage
using selenium webdriver.
working example on the VULNERABILITY CAPACITY ASSESSMENT (VCA) of IFRC
<http://vcarepository.info/find>

"""
# initialize webdriver
firefoxProfile = webdriver.FirefoxProfile()
firefoxProfile.set_preference("browser.download.folderList", 2)
firefoxProfile.set_preference("browser.download.manager.showWhenStarting", False)
firefoxProfile.set_preference("browser.download.dir", os.getcwd())
firefoxProfile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
firefoxProfile.set_preference("pdfjs.disabled", True)
firefoxProfile.set_preference("plugin.scan.Acrobat", "99.0")
firefoxProfile.set_preference("plugin.scan.plid.all", False)
browser = Firefox(firefox_profile=firefoxProfile)

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

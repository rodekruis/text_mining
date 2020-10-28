from selenium import webdriver
import time

chromedriver_location = '/usr/bin/chromedriver'
chrome = webdriver.Chrome(chromedriver_location)
 
def facebook():
    """login to facebook, access a page,
    scroll down and do stuff """
    
    # login
    chrome.get('https://www.facebook.com/login')
    user = chrome.find_element_by_css_selector('#email')
    user.send_keys('<facebook-user-name>')
    password = chrome.find_element_by_css_selector('#pass')
    password.send_keys('<facebook-password>')
    login = chrome.find_element_by_css_selector('#loginbutton')
    login.click()
 
    # get some facebook page
    chrome.get('<some-facebook-page-url>')
    time.sleep(2)
    
    # scroll until you can
    while True:
        chrome.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        
    # do stuff
    # ...

    
def twitter():
    """login to twitter, access a page,
    scroll down and do stuff """
    
    # login
    chrome.get('https://www.twitter.com')
    user = chrome.find_element_by_css_selector('[placeholder="Phone, email, or username"]')
    user.send_keys('<twitter-user-name>')
    password = chrome.find_element_by_css_selector('[placeholder="Password"]')
    password.send_keys('<twitter-password>')
    login = chrome.find_element_by_css_selector('[value="Log in"]')
    login.click()
 
    # get some twitter page
    chrome.get('<some-twitter-page-url>')
    time.sleep(2)

    # scroll until you can
    while True:
        chrome.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        
    # do stuff
    # ...
 


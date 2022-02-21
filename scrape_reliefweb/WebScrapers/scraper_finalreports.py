import csv
import platform
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

option = webdriver.ChromeOptions()

# disables the opening of images
chrome_prefs = {}
option.add_argument('headless')  # Run code without opening window
option.experimental_options["prefs"] = chrome_prefs
chrome_prefs["profile.default_content_settings"] = {"images": 2}
chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}

# Choose path
if platform.system() == "Windows":
    PATH = "../chromedriver.exe"
if platform.system() == "Darwin":
    PATH = "../chromedriver_mac2"
if platform.system() == "Linux":
    PATH = "../chromedriver_linux"
else:
    PATH = None
    print("Error occured: OS not supported")


# IMPORTANT: BECAUSE THE PIPELINE KEPT FAILING THE DRIVER IS COMMENTED OUT, IN ORDER TO BE ABLE TO RUN THE CODE
# ONE SHOULD REMOVE THE #'S IN LINES 31,32 and 35 AND REMOVE "driver = PATH" (line 35)

# Setting up the driver
# driver = webdriver.Chrome(executable_path=PATH, options=option)
# driver.implicitly_wait(10)

URL = "https://reliefweb.int/updates?advanced-search=%28S1242%29_%28F10%29&search=final+report"
# driver.get(URL)
driver = PATH

# NOTE: I couldn't break up this function into smaller ones because it requires a "page". If you make separate
# functions you'll need to reload the page which is very time consuming.
def obj_to_list(obj):
    """Returns a list of elements from a given object"""
    elem_list = []
    for item in obj:
        elem_list.append(item.text)
    if len(elem_list) == 0:
        elem_list = None
    return elem_list


def get_data(url):
    """Retrieves pdf download link and disaster type from given url"""
    web_page = webdriver.Chrome(PATH, options=option)
    web_page.implicitly_wait(1)
    web_page.get(url)

    # Extract all disaster types and add it to a list
    try:
        disasters_obj = web_page.find_elements_by_tag_name("dd.disaster_type a")
        print(disasters_obj)
        disasters_list = obj_to_list(disasters_obj)
    # If no disaster types are found, set equal to None
    except NoSuchElementException:
        print("Disaster type on page - " + url + " - not found!")
        disasters_list = None

    # Extract primary country
    try:
        primary_country_obj = web_page.find_elements_by_tag_name("dd.primary_country a")
        primary_country_list = obj_to_list(primary_country_obj)
    except NoSuchElementException:
        print("Primary country on page - " + url + " - not found!")
        primary_country_list = None

    # Extract other countries
    try:
        other_country_obj = web_page.find_elements_by_tag_name("dd.country a")
        other_country_list = obj_to_list(other_country_obj)
    except NoSuchElementException:
        print("Other countries on page - " + url + " - not found!")
        other_country_list = None

    # Extract pdf link
    try:
        pdf_link = web_page.find_element_by_css_selector("section.report [href]").get_attribute('href')
    # If no pdf link available, set equal to None
    except NoSuchElementException:
        print("Primary country on page - " + url + " - not found!")
        pdf_link = None

    return pdf_link, disasters_list, primary_country_list, other_country_list


def get_links():
    """"Returns a list of links to disaster pages of a search page"""
    elements = driver.find_elements_by_css_selector("h4.title a")
    for element in elements:
        url = element.get_attribute("href")
        pdf_link, disasters, primary_country, other_countries = get_data(url)
        # Write to csv file
        write_to_csv(url, pdf_link, disasters, primary_country, other_countries)


def write_to_csv(url, pdf_link, disasters, primary_country, other_countries):
    """Writes a line in a csv file"""
    with open('test.csv', "a", newline='') as file:
        writer = csv.writer(file)
        writer.writerow([url, pdf_link, disasters, primary_country, other_countries])

CURR = 1

# For now i set CURR = 1, the code works for all pages if while loop is set to: while True:
if __name__ == "__main__":
    while CURR <= 1:
        try:
            get_links()
            link = driver.find_element_by_link_text("Next")  # goes to Next page
            link.click()
            print(f"page {CURR} done")
            # print("Navigating to Next Page")
            CURR += 1
        except NoSuchElementException:
            print("Last page reached")
            break

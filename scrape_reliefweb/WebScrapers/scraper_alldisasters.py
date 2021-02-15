import csv
import itertools
import platform
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

# Choose path
if platform.system() == "Windows":
    PATH = "../chromedriver.exe"
elif platform.system() == "Linux":
    PATH = "../chromedriver_linux"
elif platform.system() == "Darwin":
    PATH = "../chromedriver_mac2"
else:
    print("Error occured: OS not supported")
    PATH = None

# Setting up the webdriver
chrome_prefs = {}
option = webdriver.ChromeOptions()

option.add_argument('headless')  # Run code without opening window
option.experimental_options["prefs"] = chrome_prefs
chrome_prefs["profile.default_content_settings"] = {"images": 2}
chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}

# IMPORTANT: BECAUSE THE PIPELINE KEPT FAILING THE DRIVER IS COMMENTED OUT, IN ORDER TO BE ABLE TO RUN THE CODE
# ONE SHOULD REMOVE THE #'S IN LINE 30 and 31 AND REMOVE "driver = PATH" (line 32)

# driver = webdriver.Chrome(executable_path=PATH, options=option)
# driver.implicitly_wait(10)
driver = PATH

# Dictionairy of all disaster types and its corresponding link
disaster_types = {"Cold Wave": "https://reliefweb.int/disasters?advanced-search=%28TY4653%29",
                  "Drought": "https://reliefweb.int/disasters?advanced-search=%28TY4672%29",
                  "Earthquake": "https://reliefweb.int/disasters?advanced-search=%28TY4628%29",
                  "Epidemic": "https://reliefweb.int/disasters?advanced-search=%28TY4642%29",
                  "Extratropical Cyclone": "https://reliefweb.int/disasters?advanced-search=%28TY4719%29",
                  "Fire": "https://reliefweb.int/disasters?advanced-search=%28TY5706%29",
                  "Flash Flood": "https://reliefweb.int/disasters?advanced-search=%28TY4624%29",
                  "Flood": "https://reliefweb.int/disasters?advanced-search=%28TY4611%29",
                  "Heat Wave": "https://reliefweb.int/disasters?advanced-search=%28TY4930%29",
                  "Insect Infestation": "https://reliefweb.int/disasters?advanced-search=%28TY5255%29",
                  "Land Slide": "https://reliefweb.int/disasters?advanced-search=%28TY4728%29",
                  "Mud Slide": "https://reliefweb.int/disasters?advanced-search=%28TY4814%29",
                  "Other": "https://reliefweb.int/disasters?advanced-search=%28TY5042%29",
                  "Severe Local Storm": "https://reliefweb.int/disasters?advanced-search=%28TY4656%29",
                  "Snow Avalanche": "https://reliefweb.int/disasters?advanced-search=%28TY4764%29",
                  "Storm Surge": "https://reliefweb.int/disasters?advanced-search=%28TY5549%29",
                  "Technological Disaster": "https://reliefweb.int/disasters?advanced-search=%28TY4620%29",
                  "Tropical Cyclone": "https://reliefweb.int/disasters?advanced-search=%28TY4618%29",
                  "Tsunami": "https://reliefweb.int/disasters?advanced-search=%28TY4687%29",
                  "Volcano": "https://reliefweb.int/disasters?advanced-search=%28TY4615%29",
                  "Wild Fire": "https://reliefweb.int/disasters?advanced-search=%28TY4648%29"}


def get_data(disaster_type):
    """Retreives the desired information of a website with as input its disaster type"""
    disaster_names = driver.find_elements_by_css_selector("h4.title a")
    # Check whether there are disasters found
    if len(disaster_names) > 0:
        # Create objects to retreive country and amount of countries
        disaster_countries = driver.find_elements_by_css_selector("dd.country a")
        multiple_countries = driver.find_elements_by_css_selector("dt.country")
        for (name, country, more) in itertools.zip_longest(disaster_names, disaster_countries,
                                                           multiple_countries):
            d_name = name.text
            d_date = get_date(d_name)
            # If there are multiple countries affected for a given disaster, visit disaster page (via get_all_countries)
            if more.text == "Affected countries":
                try:
                    d_countries = get_all_countries(name.get_attribute("href"))
                    # For every country write a line in a csv file (via write_to_csv)
                    for element in d_countries:
                        write_to_csv(d_name, d_date, disaster_type, element)
                except NoSuchElementException:
                    print("Error occurred in multiple countries function for: " + d_name)
            else:
                try:
                    # Write a line in csv file for given disaster
                    d_country = country.text
                    write_to_csv(d_name, d_date, disaster_type, d_country)
                except NoSuchElementException:
                    print("Error occurred in single countries function for: " + d_name)
    else:
        print("No disasters found in this category")


def get_all_countries(url_link):
    """Opens a page (the passed url_link) and returns a list of countries which are stated on the website"""
    try:
        # Initialise webdriver
        page = webdriver.Chrome(executable_path=PATH, options=option)
        page.implicitly_wait(10)
        page.get(url_link)
        content = page.find_elements_by_id("countries")
        countries = []
        for country in content:
            countries.append(country.text)
        return countries[0].splitlines()[1:]
    except NoSuchElementException:
        print("Error found in get_all_countries for: " + url_link)
        return None


def get_date(name):
    """Returns a date from the name of a disaster"""
    try:
        return name.split("- ")[1]
    # If name is not of the same structure throw an error
    except IndexError:
        print("Index Error occurred for: " + name)
        return None

def write_to_csv(d_name, d_date, disaster_type, d_country):
    """"Writes a line in a csv file"""
    # FORMAT: Disaster Name | Disaster date | Disaster type | Disaster country
    with open('test.csv', "a", newline='') as file:
        writer = csv.writer(file)
        writer.writerow([d_name, d_date, disaster_type, d_country])

# Only run code if its called directly
if __name__ == "__main__":
    for d_type in disaster_types:
        driver.get(disaster_types[d_type])
        # Give a signal that the scraper starts scraping a certain disaster type
        print("Start scraping disasters of type: " + d_type)
        while True:
            try:
                get_data(d_type)
                link = driver.find_element_by_link_text("Next")  # goes to Next page
                link.click()
            except NoSuchElementException:
                # All disasters of a given type are scraped, give this signal
                print("All disasters scraped of type: " + d_type)
                break

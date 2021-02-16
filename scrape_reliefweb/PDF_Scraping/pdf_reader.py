import pandas as pd
import ssl
import csv
from requests.exceptions import MissingSchema, InvalidURL
from project.PDF_Scraping.pdf_processing import delete_file, pdf_download
from project.PDF_Scraping.pdf_miner import find_date, pdf_search
from project.PDF_Scraping.location_miner import find_cities

# Error handling for pdf download
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# data initialization
var = {'Url': [], 'Glide n°': [], 'Type of disaster': [], 'Operation start date': [], 'Operation end date': [],
       'budget': [],
       'people affected': [], 'people assisted': [], 'Affected Countries': []}
var_list = ['people affected', 'Glide n°', 'Operation start date', 'Operation end date', 'budget',
            'people assisted', 'cities']
data = pd.DataFrame(data=var)
data.info()

with open('all_links.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    count = 0

    # These lines can be used to test a subset of the links file
    # for _ in range(500):  # skip the first 500 rows for testing purposes
    #     next(csv_reader)
    #     count += 1

    for row in csv_reader: # Every row corresponds to a different final report
        print(count)
        count += 1  # Use counter to track progress
        url = row[1]
        url_web = row[0]

        # These lines can be used to stop scraping before the end of the rows
        # if count == 40:  # for testing purposes
        #     break

        try:  # invalid url exception for download error handling
            filename = pdf_download(url)
        except (MissingSchema, InvalidURL):
            continue

        temp = {'Url': url, 'Type of disaster': [], 'Operation start date': [], 'Operation end date': [], 'budget': [],
                'people affected': [], 'people assisted': [], 'Affected Countries': [], 'cities': []}
        for i in var_list:
            a = pdf_search(i, filename)  # use pdf search to find a variable in the table
            if a:
                temp[i] = a

        date = find_date(filename) # Find the date of the disaster
        temp['Date'] = date

        temp['Type of disaster'] = row[2]
        temp['Affected Countries'] = row[3]

        url_web = row[0]
        country = (row[3]).strip("'[]'")
        temp['cities'] = find_cities(url_web, country)  # Find the cities of the affected country mentioned

        data = data.append(temp, ignore_index=True)

        delete_file(filename) # Delete csv file

    data.to_csv('impact_data.csv', index=False) # export data into a csv file

## General

The files serve to scrape information from https://reliefweb.int/ on disasters that have
occured in the past. More specifically it scraps "Final Disaster Reports" and general
information on disasters.

## Important
Both files "scraper_alldisasters.py" and "scraper_finalreports.py" are unable to work properly. This is because of a
pipeline failure on Gitlab. However if one adjusts the code in both files (the part 'driver = ...') the code will
work properly. This is also explained in a comment on line 27 in both files.


## Different files and functioning of the program

The "scraper_finalreports.py" scraps the pdf link of the final report,
the links containing the final report in html format, the type of disaster and the countries
where the disaster has occured. All this 4 types of information are collected from https://reliefweb.int/
if information cannot be scraped an exception is thrown. All the links are stored in an
.csv file, which is named here "links58.csv". For testing this is set to test.csv, but can be easily changed in the
function "write_to_csv"


The file "scraper_alldisaster.py" is also a webscraper, however it goes through all disasters
listed on https://reliefweb.int/ not just Final Reports as is the case for "new_very_fast_macintosh_webscraper.py".
The "scraper_alldisaster.py", however only collects information on the disaster name, date of disaster occurance,
disaster type and countries it has occured. All this scraped information is saved into a csv file,
which in this case is all_disasters.csv


The "chromedriver" files are used to launch the google chrome webdriver for the webscraper

## Automated Tests

The folder "test" contains automated tests for the webscrapers.
For now the tests for which a webdriver is used are skipped.These test work, but the GitLab pipeline fails because
of some configuration

project: ifrc_scraper

install requirements:
$ pip install --user Scrapy
$ pip install --user pandas

execute:
$ scrapy crawl ifrc_spider -o contacts.csv

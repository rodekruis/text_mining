import re
import os
from datetime import datetime
import time
import logging

import plac
from newspaper import Article
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import \
    NoSuchElementException, TimeoutException, InvalidArgumentException, WebDriverException
import pandas as pd
import dateparser

from utils import utils


logger = logging.getLogger(__name__)
for package in ['selenium', 'urllib3']:
    logging.getLogger(package).setLevel(max(logger.level, getattr(logging, 'INFO')))

pd.set_option('display.max_columns', 4)
pd.set_option('max_colwidth', 20)

TIMEOUT = 30
NEWSPAPER_URL_BASE = 'abyznewslinks'
DATE_FORMAT = '%d/%m/%Y'


def is_date(txt, lng):
    output = dateparser.parse(txt, languages=[lng])
    if output:
        return True
    else:
        return False


def remove_newspaper_name_from_title(article_title, news_name):
    # Match on possible punctuation (some kind of separator like an en-dash or •),
    # 0 or more spaces, a possible word for newspaper like "journal" (can be expanded for other cases),
    # 0 or more spaces, the name of the newspaper with and without added hyphens,
    # and a possible '.abc' to catch URLs.

    match_string = r'[^\w\d\s]?\s*({newspaper_word})?\s*({news_name}|{news_name_hyphen})(\.\w*)?'
    match_string = match_string.format(newspaper_word='journal',
                                       news_name=re.escape(news_name.strip()),
                                       news_name_hyphen=re.sub(' ', '-', re.escape(news_name.strip())))
    article_title = re.sub(match_string, '', article_title, flags=re.IGNORECASE).strip()
    return article_title


def ProcessPage(keyword, vBrowser, vNews_name, vNews_url, language):
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
    url_any = re.sub(re.escape('?s='+keyword), '', url_any)
    url_any = re.sub(re.escape('search?k='+keyword), '', url_any)
    url_any = re.sub('\?m\=[0-9]{6}', '', url_any)
    url_any = re.escape(url_any) + '(?=\S*[-])([0-9a-zA-Z-\/\.]+)'
    regex = re.compile(url_any)
    logger.info('searching for {}'.format(url_any))
    search_results = list(set([match[0] for match in
                               regex.finditer(search_result_page_source)
                               if keyword in match[0].lower()]))

    if vNews_name in ['NewVision']:
        regex = re.compile('\/new\_vision\/news\/(?=\S*[-])([0-9a-zA-Z-\/\.]+)')
        search_results = list(set([ match[0] for match in regex.finditer(search_result_page_source) if keyword in match[0].lower()]))
        search_results = ['https://www.newvision.co.ug' + search_result for search_result in search_results]

    if len(search_results) > 0:
        logger.info("found {0} article(s):".format(len(search_results)))
        for title in search_results:
            logger.info("url: {0}".format(title))
    else:
        logger.info('no articles found')

    # 2) for each result, get article and save it
    for idx, search_result in enumerate(search_results):

        logger.info('processing {}'.format(search_result))
        # download article
        article = Article(search_result, keep_article_html=True)
        article.download()
        attempts = 0
        while (article.download_state != 2) & (attempts<5): #ArticleDownloadState.SUCCESS is 2
            attempts += 1
            time.sleep(1)
        if article.download_state != 2:
            logger.warning('unable to download article: {}'.format(search_result))
            continue
        article.parse()

        article_html = str(article.html)

        # select articles with keyword
        regex = re.compile(keyword, re.IGNORECASE)

        if re.search(regex, article.html) is not None:

            logger.debug('{}'.format(article_html))

            # get date
            date = article.publish_date
            date_str = ""
            search_date = False

            if date is not None:
                # keep date found only if older than today
                if pd.to_datetime(date_str).date() < pd.to_datetime(datetime.today()).date():
                    date_str = date.strftime(DATE_FORMAT)
                else:
                    search_date = True
            else:
                search_date = True

            if search_date:
                article_html = re.sub('\s+', ' ', article_html)
                dates_found = []

                res_date = [re.compile('[a-zA-ZÀ-ÿ]\w+\s[0-9]+\,\s[0-9]{4}'),
                            re.compile('[a-zA-ZÀ-ÿ]\w+\s[0-9]+\s[0-9]{4}'),
                            re.compile('[0-9]\w+\s[a-zA-ZÀ-ÿ]+\,\s[0-9]{4}'),
                            re.compile('[0-9]\w+\s[a-zA-ZÀ-ÿ]+\s[0-9]{4}'),
                            re.compile('[0-9]+\s[a-zA-ZÀ-ÿ]+\,\s[0-9]{4}'),
                            re.compile('[0-9]+\s[a-zA-ZÀ-ÿ]+\s[0-9]{4}'),
                            re.compile('[0-9]{2}\/[0-9]{2}\/[0-9]{4}'),
                            re.compile('[0-9]{2}\-[0-9]{2}\-[0-9]{4}'),
                            re.compile('[0-9]{2}\.[0-9]{2}\.[0-9]{4}')]
                for re_date in res_date:
                    for match in re_date.finditer(article_html):
                        if is_date(match.group(), language):
                            dates_found.append((match.start(), match.group()))
                if len(dates_found) > 0:
                    logger.info('{}'.format(dates_found))
                    dates_found.sort(key=lambda tup: tup[0])
                    for res in dates_found:
                        res_date = dateparser.parse(res[1], languages=[language]).date()
                        if (res_date < pd.to_datetime(datetime.today()).date()
                            and res_date > pd.to_datetime('30/04/1993', format="%d/%m/%Y").date()):
                            date_str = res_date.strftime(DATE_FORMAT)
                            break

            if date_str == "":
                logger.warning('Publication date not found or wrongly assigned, skipping article')
                continue
            else:
                logger.info('Publication date assigned: {}'.format(date_str))

            # Take newspaper name out of article title
            article.title = remove_newspaper_name_from_title(article.title, vNews_name)

            # if no text is present (e.g. only video), use title as text
            article_text = article.text
            if len(str(article.text)) == 0:
                article_text = article.title

            # add to dataframe
            logger.info('{0} : {1}'.format(article.title, date_str))
            articles_page.loc[idx] = [article.title, date_str, article_text, article.url]

    # 3) return dataframe
    if len(search_results) > 0:
        logger.info('{}'.format(articles_page.head()))
    return articles_page

################################################################################


@plac.annotations(
    config_file="Configuration file",
    debug=("Set log level to debug", "flag", "d")
)
def main(config_file, debug=False):
    """
    Scrape articles from online newspapers
    save article in pandas dataframe (articles_all)
    """
    config = utils.get_config(config_file)

    # Log output to a file
    log_filename = 'scrape_articles_{country}_{keyword}_{timestamp}.log'
    log_filename = log_filename.format(country=config['country'], keyword=config['keyword'],
                                       timestamp=time.strftime('%Y%m%d-%H%M%S'))
    utils.set_log_level(debug, log_filename=log_filename)

    # if output directory does not exist, create it
    output_dir = utils.get_scraped_article_output_dir(config)
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    # initialize webdriver
    opts = Options()
    opts.headless = True
    assert opts.headless  # operating in headless mode
    browser = Firefox(options=opts)
    browser.set_page_load_timeout(TIMEOUT)

    # get newspapers urls
    newspaper_database_url = 'http://{newspaper_url_base}.com/{country}.htm'.format(
        newspaper_url_base=NEWSPAPER_URL_BASE, country=config['country'][:5].lower())
    browser.get(newspaper_database_url)
    newspaper_elements = browser.find_elements_by_css_selector('a')
    newspaper_urls = [el.get_attribute('href') for el in newspaper_elements]
    newspaper_names = [el.get_attribute('text') for el in newspaper_elements]
    Newspapers = dict(zip(newspaper_names, newspaper_urls))
    Newspapers = {key:val for key, val in Newspapers.items() if NEWSPAPER_URL_BASE not in val}

    # blacklist
    del Newspapers['Niarela']

    # loop over newspapers
    for news_name, news_url in Newspapers.items():

        articles_news = pd.DataFrame(columns=['title', 'publish_date', 'text', 'url'])

        logger.info('**********************************************************************************')
        logger.info('Accessing {0} ({1})'.format(news_name, news_url))
        news_url += '?s='+config['keyword']
        try:
            browser.get(news_url)
        except (TimeoutException, WebDriverException):
            logger.error('Unable to access, skipping')
            continue

        # process first results page
        logger.info("Begin to process page 1 ({0})".format(browser.current_url))
        articles_page = ProcessPage(config['keyword'], browser, news_name, news_url, language=config['language'][:2])
        articles_news = articles_news.append(articles_page)

        # start looping over all pages of results
        page_number = 2
        while True:
            logger.info("Trying to open page {0} ...".format(page_number))
            try:
                link = browser.find_element_by_link_text(str(page_number))
                browser.get(link.get_attribute("href"))
            except NoSuchElementException:
                url_next_page = news_url
                url_next_page = re.sub(re.escape('?s='+config['keyword']), '', url_next_page)
                url_next_page = re.sub(re.escape('search?k='+config['keyword']), '', url_next_page)
                url_next_page = re.escape(url_next_page) + 'page\/' + str(page_number) + '.*?(?=")'
                regex = re.compile(url_next_page)
                logger.info('link not found, trying explicit regex: {}'.format(url_next_page))
                search_result_next_page = re.search(regex, browser.page_source)
                if search_result_next_page is None:
                    logger.info('Not found!')
                    break
                else:
                    logger.info('{}'.format(search_result_next_page[0]))
                    try:
                        browser.get(search_result_next_page[0])
                    except (NoSuchElementException, TimeoutException, InvalidArgumentException):
                        logger.error("Can't open page, abandoning news source")
                        break
            except (TimeoutException, InvalidArgumentException):
                logger.error("Can't open page, abandoning news source")
                break
            logger.info("Begin to process page {0} ({1})".format(page_number, browser.current_url))
            articles_page = ProcessPage(config['keyword'], browser, news_name, news_url, language=config['language'][:2])
            articles_news = articles_news.append(articles_page)
            page_number += 1

        # save dataframe to csv
        logger.info('Saving articles from {}'.format( news_name))
        logger.info('{}'.format(articles_news.describe()))
        logger.info('*********************************************************')
        output_name = 'articles_{keyword}_{news_name}.csv'.format(
            keyword=config['keyword'], news_name=news_name)
        output_dir_news = os.path.join(output_dir, output_name)
        articles_news.to_csv(output_dir_news, sep='|', index=False)

    logger.info("\nFINISHED PROCESSING *****************************")

    # ## save dataframe to hdf5
    # output_dir_all = str(output_dir) + "/articles_" + keyword + "_all.h5"
    # logger.info("Saving all articles to {0}".format(output_dir_all))
    # articles_all.to_hdf(output_dir_all, key='df', mode='w')


if __name__ == '__main__':
    plac.call(main)

import configparser
import re
import logging
import os

import pandas as pd
from pandas.errors import EmptyDataError


INPSECTED_ARTICLES_OUTPUT_DIR = 'articles_processed'
LOCATIONS_KEYWORDS = 'keywords'  # location of keywords (victims, infrastructures)
LOG_DIR = 'logs'


def get_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config['main']


def get_keywords(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config['keywords']


def get_scraped_article_output_dir(config):
    return 'Articles_{keyword}_{country}'.format(
        keyword=config['keyword'], country=config['country'])


def get_articles_summary_output_filename(config):
    return 'articles_summary_{keyword}_{country}.csv'.format(
        keyword=config['keyword'], country=config['country'])


def get_inspected_articles_output_filename(config):
    return 'articles_all_topical_{keyword}_{country}.csv'.format(
        keyword=config['keyword'], country=config['country'])


def get_pattern_entity(loc_string, target):
    pattern_entity = '({loc_string}(.*){target}|{target}(.*){loc_string})'
    pattern_entity = pattern_entity.format(loc_string=re.escape(loc_string), target=re.escape(target))
    return re.compile(str(pattern_entity), re.IGNORECASE)


def read_keyword_csv(filename):
    try:
        return pd.read_csv(os.path.join(LOCATIONS_KEYWORDS,  filename),
                           header=None, encoding='latin-1')[0].tolist()
    except EmptyDataError:
        return []


def set_log_level(is_debug_mode=False, log_filename=None):
    logging.basicConfig()
    log_level = 'DEBUG' if is_debug_mode else 'INFO'
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    if log_filename is not None:
        if not os.path.isdir(LOG_DIR):
            os.mkdir(LOG_DIR)
        file_handler = logging.FileHandler(os.path.join(LOG_DIR, log_filename))
        formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level.upper())
        root_logger.addHandler(file_handler)

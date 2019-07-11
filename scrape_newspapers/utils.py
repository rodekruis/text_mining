import configparser


INPSECTED_ARTICLES_OUTPUT_DIR = 'articles_processed'


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
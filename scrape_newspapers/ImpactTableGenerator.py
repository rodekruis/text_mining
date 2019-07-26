import os
import importlib
import logging
import ast

import pandas as pd
from pandas import ExcelWriter
import spacy

utils = importlib.import_module('utils')
Article = importlib.import_module('Article')

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# location of gazetteers (http://geonames.nga.mil/gns/html/namefiles.html)
LOCATIONS_FOLDER = 'locations'

# location of keywords (victims, infrastructures)
LOCATIONS_KEYWORDS = 'keywords'

# output directory
OUTPUT_DIRECTORY = 'impact_data'


class ImpactTableGenerator:

    def __init__(self,
                 config_file,
                 input_filename=None,
                 output_filename_base=None):

        # create parameters
        self.__dict__.update(utils.get_config(config_file))

        # Load list of locations
        self.locations_df = self._load_locations()

        # load spacy model
        logger.info("Loading model {}".format(self.model))
        self.nlp = spacy.load(self.model)

        # get df of articles
        self.articles_df = self._load_articles(input_filename)

        # get keywords
        self.keywords = ImpactTableGenerator._get_keywords(config_file)
        logger.info(self.keywords.keys())

        # prepare output
        if output_filename_base is None:
            output_filename_base = 'impact_data_{keyword}_{country}'.format(
                keyword=self.keyword, country=self.country)
        self.output_filename_base = output_filename_base

        if not os.path.exists(OUTPUT_DIRECTORY):
            os.makedirs(OUTPUT_DIRECTORY)
        self.writer = ExcelWriter(os.path.join(OUTPUT_DIRECTORY,
                                          self.output_filename_base+'.xlsx'))
        self.df_impact = ImpactTableGenerator._make_df_impact()

    def loop_over_articles(self):
        for id_row in range(len(self.articles_df)):
            logger.info("Analyzing article {}/{}...".format(id_row+1, len(self.articles_df)))
            article = Article.Article(self, id_row)


    @staticmethod
    def _make_df_impact():
        levels = [[], [], []]
        codes = [[], [], []]
        names = ['location',
                 'date',
                 'article_num']
        columns = ['damage_livelihood',
                   'damage_general',
                   'people_affected',
                   'people_dead',
                   'houses_affected',
                   'livelihood_affected',
                   'infrastructures_affected',
                   'infrastructures_mentioned',
                   'sentence(s)',
                   'article_title']
        return pd.DataFrame(index=pd.MultiIndex(levels=levels, codes=codes, names=names),
                            columns=columns)

    def _load_articles(self, input_filename):
        # load DataFrame with articles
        input_directory = utils.INPSECTED_ARTICLES_OUTPUT_DIR
        if input_filename is None:
            input_filename = utils.get_inspected_articles_output_filename(
                {'keyword': self.keyword, 'country': self.country})
        df = pd.read_csv(os.path.join(input_directory, input_filename),
                         sep='|').drop_duplicates(['title', 'text'], keep=False)
        df['publish_date'] = df['publish_date'].apply(pd.to_datetime)
        logger.info('got {} articles:'.format(len(df)))
        logger.info('{} -- {}'.format(df['publish_date'].min().strftime('%Y-%m-%d'),
                                      df['publish_date'].min().strftime('%Y-%m-%d')))
        return df

    @staticmethod
    def _get_keywords(config_file):
        keywords_config = utils.get_keywords(config_file)

        keyword_list = ['donation',
                        'type_livelihood',
                        'type_people_multiple',
                        'type_people_death',
                        'type_house',
                        'local_currency_names_short',
                        'currency_short',
                        'local_currency_code',
                        'local_currency_names_long',
                        'currency_long',
                        'titles'
                        ]

        keywords = {keyword: ast.literal_eval(keywords_config[keyword])
                    for keyword in keyword_list}

        keywords['type_people'] = pd.read_csv(os.path.join(LOCATIONS_KEYWORDS,
                                              keywords_config['filename_type_people']),
                                              header=None, encoding='latin-1')[0].tolist()
        keywords['type_infrastructure'] = pd.read_csv(os.path.join(LOCATIONS_KEYWORDS,
                                                      keywords_config['filename_type_infrastructures']),
                                                      header=None, encoding='latin-1')[0].tolist()
        keywords['currency_short'] = keywords['local_currency_names_short'] + keywords['currency_short']
        keywords['currency_long'] = keywords['local_currency_names_long'] + keywords['currency_long']
        return keywords

    def _load_locations(self):
        """
        build a dictionary of locations {name: coordinates}
        from a gazetteer in tab-separated csv format (http://geonames.nga.mil/gns/html/namefiles.html)
        """
        input_file = os.path.join(LOCATIONS_FOLDER, self.country, self.country_short+'.txt')
        columns = ['FULL_NAME_RO', 'FULL_NAME_ND_RO', 'LAT', 'LONG']
        locations_df = pd.read_csv(input_file, sep='\t', encoding='utf-8', usecols=columns)
        # this definitely needs to be refactored to another location,
        # but anyway if the country is mali take out niger (the river)
        # or maybe we should not be reading in any of the hydrographic locations?
        if self.country_short == 'ml':
            locations_df = locations_df[locations_df['FULL_NAME_RO'] != "Niger"]
        return locations_df



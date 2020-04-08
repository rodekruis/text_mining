import os
import logging
import ast

import pandas as pd
from pandas import ExcelWriter
import spacy

from impact_table_generator import Article
from utils import utils
import geojson
from nltk.corpus import words


logger = logging.getLogger(__name__)

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
                 output_filename_base=None,
                 output_directory=None):

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

        # prepare output
        if output_filename_base is None:
            output_filename_base = 'impact_data_{keyword}_{country}'.format(
                keyword=self.keyword, country=self.country)
        self.output_filename_base = output_filename_base
        if output_directory is None:
            self.output_directory = OUTPUT_DIRECTORY
        else:
            self.output_directory = output_directory

        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)
        self.writer = ExcelWriter(os.path.join(self.output_directory,
                                  self.output_filename_base+'.xlsx'))
        self.df_impact = ImpactTableGenerator._make_df_impact()

    def loop_over_articles(self):
        n_articles = len(self.articles_df)
        for id_row in range(n_articles):
            logger.info("Analyzing article {}/{}...".format(id_row+1, n_articles))
            article = Article.Article(self.articles_df.iloc[id_row],
                                      self.language,
                                      self.keywords,
                                      self.nlp,
                                      self.locations_df
                                      )
            article.analyze(self.language, self.keywords, self.df_impact)

            logger.info("...finished article {}/{}, updating file\n".format(id_row+1, n_articles))

            if not self.df_impact.empty:
                self.df_impact.to_csv(os.path.join(self.output_directory, self.output_filename_base+'.csv'),
                                 mode='w', encoding='utf-8', sep='|')
                self.df_impact.to_excel(self.writer, sheet_name='Sheet1')
                self.writer.save()

        logger.info('found {} entries'.format(len(self.df_impact)))
        self.df_impact.dropna(how='all', inplace=True)
        logger.info('{}'.format(self.df_impact.describe()))
        logger.info('{}'.format(self.df_impact.head()))
        self.df_impact.to_csv(os.path.join(self.output_directory, self.output_filename_base+'.csv'),
                         mode='w', encoding='utf-8', sep='|')
        self.df_impact.to_excel(self.writer, sheet_name='Sheet1')
        self.writer.save()

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
                        'list_verb_death',
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

        keywords['type_people'] = utils.read_keyword_csv(keywords_config['filename_type_people'])
        keywords['type_infrastructure'] = utils.read_keyword_csv(keywords_config['filename_type_infrastructures'])
        keywords['currency_short'] = keywords['local_currency_names_short'] + keywords['currency_short']
        keywords['currency_long'] = keywords['local_currency_names_long'] + keywords['currency_long']
        return keywords

    def _load_locations(self):
        """
        build a dictionary of locations {name: coordinates}
        from a gazetteer in tab-separated csv format (http://geonames.nga.mil/gns/html/namefiles.html)
        """

        # --- OSM attempt
        with open(r"locations/Uganda/TestUgandaDistricts.geojson", encoding='utf-8') as gf:
            gj = geojson.load(gf)

        gj_df = pd.DataFrame(columns=['Name', 'Settlement', 'ADM1', 'ADM1_Name'])
        for i in gj.features:
            try:
                gj_df = pd.concat(
                    [gj_df, pd.DataFrame({'Name': [i.properties['name']], 'Settlement': [i.properties['place']], 'ADM1':[i.properties['ADM1_PCODE']], 'ADM1_Name':[i.properties['ADM1_EN']]})],
                    ignore_index=True)
            except KeyError:
                print(i.properties)

        gj_df = gj_df[~gj_df['Name'].isna()]
        gj_df = gj_df[~gj_df['ADM1'].isna()]

        # There are some 'weird' entries around row 3777, only taking first word per entry compensates this
        gj_df['Name'] = gj_df['Name'].apply(lambda x: x.split(' ', 1)[0])
        gj_df.drop_duplicates(subset='Name', keep='first', inplace=True)
        gj_df.reset_index(inplace=True, drop=True)

        # Words among town names have been found using following code, is however very time consuming
        # test = gj_df['Name'].apply(lambda x: x.lower() in words.words())

        words_among_town_names = ['East', 'West', 'Upper', 'Lower', 'Point', 'Township', 'Central', 'Village', 'Block',
                                  'Junior', 'Club', 'Air', 'Tank', 'Police', 'Hospital', 'New', 'Te', 'Railway', 'Media']

        final = gj_df[~gj_df['Name'].apply(lambda x: x in words_among_town_names)]
        return final



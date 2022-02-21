import os
import logging
import ast
import geopandas as gpd
import pandas as pd
from pandas import ExcelWriter
import spacy

from . import Article
from utils import utils


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

        # check for space-separated locations and add as custom entities
        locations_double_name = self.locations_df[self.locations_df['FULL_NAME_RO'].str.contains(" ")]
        if not locations_double_name.empty:
            entity_ruler = self.nlp.add_pipe("entity_ruler", before="ner")
            for location in locations_double_name['FULL_NAME_RO'].unique():
                entity_ruler.add_patterns([{"label": "GPE", "pattern": location}])
        self.nlp.add_pipe("merge_entities")

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
                                      self.locations_df)
            article.analyze(self.language, self.keywords, self.df_impact )

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
        if not self.df_impact.empty:
            self.df_impact.to_excel(self.writer, sheet_name='Sheet1')
            self.writer.save()
        else:
            logger.info('no impact data found')

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
                   'article_title',
                   'url'] #add URL to output in final table
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
        df['publish_date'] = pd.to_datetime(df['publish_date'])
        df['text'] = df['text'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
        logger.info('got {} articles:'.format(len(df)))
        logger.info('{} -- {}'.format(df['publish_date'].min().strftime('%Y-%m-%d'),
                                      df['publish_date'].max().strftime('%Y-%m-%d')))
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
        # check if there are locations from OSM (txt)
        locations_df = pd.DataFrame()
        input_file = os.path.join(LOCATIONS_FOLDER, self.country, self.country_short+'_administrative_a.txt')
        if os.path.exists(input_file):
            columns = ['FULL_NAME_RO', 'FULL_NAME_ND_RO', 'LAT', 'LONG', 'ADM1']
            locations_df = pd.read_csv(input_file, sep='\t', encoding='utf-8', usecols=columns)
            input_file = os.path.join(LOCATIONS_FOLDER, self.country, self.country_short + '_localities_l.txt')
            locations_df = locations_df.append(pd.read_csv(input_file, sep='\t', encoding='utf-8', usecols=columns), ignore_index=True)
            input_file = os.path.join(LOCATIONS_FOLDER, self.country, self.country_short + '_populatedplaces_p.txt')
            locations_df = locations_df.append(pd.read_csv(input_file, sep='\t', encoding='utf-8', usecols=columns), ignore_index=True)
            locations_df = locations_df[~locations_df['FULL_NAME_ND_RO'].str.contains(self.country)]
            locations_df["ADM1"] = pd.to_numeric(locations_df["ADM1"], errors='coerce')
        # check if there are locations from HDX (xlsx)
        input_file = os.path.join(LOCATIONS_FOLDER, self.country, self.country_short + '_adminboundaries_tabulardata.xlsx')
        if os.path.exists(input_file):
            try:
                hdx_df = pd.read_excel(input_file, sheet_name="Admin3")
                levels = [1, 2, 3]
            except ValueError:
                hdx_df = pd.read_excel(input_file, sheet_name="Admin2")
                levels = [1, 2]
            locations_df = pd.DataFrame()
            for lvl in levels:
                cols = [x for x in hdx_df.columns if f"admin{lvl}Name" in x]
                col_adm_name = cols[0]
                if locations_df.empty:
                    locations_df["FULL_NAME_RO"] = pd.Series(hdx_df[col_adm_name])
                    locations_df = locations_df.drop_duplicates(subset=["FULL_NAME_RO"])
                    locations_df["ADM1"] = lvl
                else:
                    locations_df_ = pd.DataFrame()
                    locations_df_["FULL_NAME_RO"] = pd.Series(hdx_df[col_adm_name])
                    locations_df_ = locations_df_.drop_duplicates(subset=["FULL_NAME_RO"])
                    locations_df_["ADM1"] = lvl
                    locations_df = locations_df.append(locations_df_, ignore_index=True)
        # check if there are locations from geoBoundaries (geojson)
        input_file = os.path.join(LOCATIONS_FOLDER, self.country,
                                  self.country_short + '_adminboundaries_vectordata.geojson')
        if os.path.exists(input_file):
            hdx_df = gpd.read_file(input_file)
            locations_df = pd.DataFrame()
            for lvl in [1, 2, 3]:
                hdx_df_lvl = hdx_df[hdx_df["Level"] == f"ADM{lvl}"]
                if locations_df.empty:
                    locations_df["FULL_NAME_RO"] = pd.Series(hdx_df_lvl["shapeName"])
                    locations_df = locations_df.drop_duplicates(subset=["FULL_NAME_RO"])
                    locations_df["ADM1"] = lvl
                else:
                    locations_df_ = pd.DataFrame()
                    locations_df_["FULL_NAME_RO"] = pd.Series(hdx_df_lvl["shapeName"])
                    locations_df_ = locations_df_.drop_duplicates(subset=["FULL_NAME_RO"])
                    locations_df_["ADM1"] = lvl
                    locations_df = locations_df.append(locations_df_, ignore_index=True)
        if locations_df.empty:
            raise(ValueError)
        return locations_df



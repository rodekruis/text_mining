import os
import importlib
import logging

import pandas as pd
import spacy

utils = importlib.import_module('utils')


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class ArticleGenerator:

    def __init__(self,
                 config_file,
                 locations_folder,
                 input_filename=None,
                 output_filename_base=None):

        # create parameters
        self.__dict__.update(utils.get_config(config_file))

        # set output filename base
        if output_filename_base is None:
            output_filename_base = 'impact_data_{keyword}_{country}'.format(
                keyword=self.keyword, country=self.country)
        self.output_filename_base = output_filename_base

        # Load list of locations
        self.locations_df = self._load_locations(locations_folder)

        # load spacy model
        logger.info("Loading model {}".format(self.model))
        self.nlp = spacy.load(self.model)

        # load DataFrame with articles
        input_directory = utils.INPSECTED_ARTICLES_OUTPUT_DIR
        if input_filename is None:
            input_filename = utils.get_inspected_articles_output_filename({'keyword': self.keyword,
                                                                           'country': self.country})
        self.articles_df = pd.read_csv(os.path.join(input_directory, input_filename),
                                       sep='|').drop_duplicates(['title', 'text'], keep=False)

        # some function to get keywords
        # maybe make a keywords class? or just a dict for now
        keywords = utils.get_keywords(config_file)

    def _load_locations(self, locations_folder):
        """
        build a dictionary of locations {name: coordinates}
        from a gazetteer in tab-separated csv format (http://geonames.nga.mil/gns/html/namefiles.html)
        """
        input_file = os.path.join(locations_folder, self.country, self.country_short+'.txt')
        columns = ['FULL_NAME_RO', 'FULL_NAME_ND_RO', 'LAT', 'LONG']
        locations_df = pd.read_csv(input_file, sep='\t', encoding='utf-8', usecols=columns)
        # this definitely needs to be refactored to another location,
        # but anyway if the country is mali take out niger (the river)
        # or maybe we should not be reading in any of the hydrographic locations?
        if self.country_short == 'ml':
            locations_df = locations_df[locations_df['FULL_NAME_RO'] != "Niger"]
        return locations_df



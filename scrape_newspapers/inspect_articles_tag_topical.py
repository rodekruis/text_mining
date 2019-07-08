#!/usr/bin/env python
# coding: utf8
from __future__ import unicode_literals, print_function

import plac
import os
import importlib

import pandas as pd

utils = importlib.import_module('utils')

pd.set_option('display.max_columns', 5)
pd.set_option('max_colwidth', 18)
pd.set_option('expand_frame_repr', True)

MAX_ARTICLES_PER_NEWSPAPER = 5


@plac.annotations(
    config_file="Configuration file",
)
def main(config_file):
    """
    Inspect articles and decide if relevant
    add corresponding boolean (topical) to dataframe
    """

    config = utils.get_config(config_file)
    articles_folder = utils.get_scraped_article_output_dir(config)

    files_in_articles_folder = os.listdir(articles_folder)
    files_in_articles_folder = [f for f in files_in_articles_folder if '.csv' in f]
    df_articles_topical_list = []

    # Get number of articles so that you know what you're in for
    num_articles = 0
    for file in files_in_articles_folder:
        num_articles += len(pd.read_csv(os.path.join(articles_folder, file),
                                        sep='|')[:MAX_ARTICLES_PER_NEWSPAPER])
    print('Analyzing {} articles'.format(num_articles))

    cnt_article = 0
    for file in files_in_articles_folder:
        df_articles = pd.read_csv(articles_folder+'/'+file,
                                  sep='|')[:MAX_ARTICLES_PER_NEWSPAPER]
        print("Analysing newspaper: {0}".format(file))
        var_topical_bool = []

        for index, article in df_articles.iterrows():
            print("\nArticle #{number}: {title}".format(
                number=cnt_article+1, title=article['title']))
            var_topical = input("Is it topical? t (True), f (False), i (Inspect text)  ")
            if var_topical == 'i':
                print(article['text'])
                var_topical = input("Is it topical? t (True), f (False)  ")
            var_topical_bool.append(var_topical=='t')
            cnt_article += 1

        df_articles = df_articles.assign(topical = var_topical_bool)
        print(df_articles.head())
        df_articles_topical_list.append(df_articles)

    output_directory = utils.INPSECTED_ARTICLES_OUTPUT_DIR
    print("Saving all articles to {0}".format(output_directory))
    # create output dir if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    output_filename = utils.get_inspected_articles_output_filename(config)
    df_articles_topical = pd.concat(df_articles_topical_list, axis=0)
    df_articles_topical.to_csv(os.path.join(output_directory, output_filename), sep='|')


if __name__ == '__main__':
    plac.call(main)

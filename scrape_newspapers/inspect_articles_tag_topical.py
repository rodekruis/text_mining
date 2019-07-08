import os
import importlib

import plac
import pandas as pd

utils = importlib.import_module('utils')

pd.set_option('display.max_columns', 5)
pd.set_option('max_colwidth', 18)
pd.set_option('expand_frame_repr', True)


@plac.annotations(
    config_file="Configuration file",
    recreate_summary_file=("Recreate the summary file", "flag", "r")
)
def main(config_file,
         recreate_summary_file=False):
    """
    Inspect articles and decide if relevant
    add corresponding boolean (topical) to dataframe
    """
    config = utils.get_config(config_file)

    output_directory = utils.INPSECTED_ARTICLES_OUTPUT_DIR
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    articles_folder = utils.get_scraped_article_output_dir(config)
    files_in_articles_folder = os.listdir(articles_folder)
    files_in_articles_folder = [f for f in files_in_articles_folder if '.csv' in f]

    # If doesn't exist yet, make a summary of articles to keep track of those
    # which have been tagged
    articles_summary_filename = os.path.join(output_directory,
                                             utils.get_articles_summary_output_filename(config))
    if os.path.isfile(articles_summary_filename) and not recreate_summary_file:
        print('Reading in summary file {}'.format(articles_summary_filename))
        df_articles_summary = pd.read_csv(articles_summary_filename)
    else:
        print('Creating summary file {}'.format(articles_summary_filename))
        columns = ['newspaper', 'article_number', 'title', 'topical']
        df_articles_summary = pd.DataFrame(columns=columns)
        index_article = 0
        for file in files_in_articles_folder:
            df_articles = pd.read_csv(articles_folder+'/'+file, sep='|')
            for index, article in df_articles.iterrows():
                row_to_add = [file, index, article['title'], None]
                df_articles_summary.loc[index_article] = row_to_add
                index_article += 1
        df_articles_summary.to_csv(articles_summary_filename)

    articles_to_analyze = df_articles_summary.loc[pd.isna(df_articles_summary['topical'])]
    number_to_analyze = len(articles_to_analyze)
    print('Analyzing {} articles'.format(number_to_analyze))

    # Tag articles and save it in the summary
    cnt_article = 0
    for _, row in articles_to_analyze.iterrows():
        article = pd.read_csv(articles_folder+'/'+row['newspaper'], sep='|').iloc[row['article_number']]
        print("\nArticle #{number}/{total}: {title}".format(
            number=cnt_article+1, total=number_to_analyze, title=article['title']))
        var_topical = input("Is it topical? t (True), f (False), i (Inspect text), q (Quit)  ")
        if var_topical == 'q':
            break
        elif var_topical == 'i':
            print(article['text'])
            var_topical = input("Is it topical? t (True), f (False)  ")
        df_articles_summary.loc[row[0], 'topical'] = var_topical == 't'
        cnt_article += 1
        df_articles_summary.to_csv(articles_summary_filename)

    # Use the summary to create a csv with only relevant articles
    df_articles_topical_list = []
    relevant_articles = df_articles_summary[df_articles_summary['topical'] == True]
    print('Saving {} relevent articles'.format(len(relevant_articles)))
    for _, row in articles_to_analyze.iterrows():
        article = pd.read_csv(articles_folder+'/'+row['newspaper'], sep='|').iloc[row['article_number']]
        df_articles_topical_list.append(article)
    print("Saving all articles to {0}".format(output_directory))
    output_filename = utils.get_inspected_articles_output_filename(config)
    df_articles_topical = pd.concat(df_articles_topical_list, axis=0)
    df_articles_topical.to_csv(os.path.join(output_directory, output_filename), sep='|', header=True)


if __name__ == '__main__':
    plac.call(main)

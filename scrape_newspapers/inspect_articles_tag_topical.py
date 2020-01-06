import os
import logging

import plac
import pandas as pd
import ast

from utils import utils


logger = logging.getLogger(__name__)

pd.set_option('display.max_columns', 5)
pd.set_option('max_colwidth', 18)
pd.set_option('expand_frame_repr', True)


@plac.annotations(
    config_file="Configuration file",
    recreate_summary_file=("Recreate the summary file", "flag", "r"),
    debug=("Set log level to debug", "flag", "d")
)
def main(config_file,
         recreate_summary_file=False,
         debug=False):
    """
    Inspect articles and decide if relevant
    add corresponding boolean (topical) to dataframe
    """
    #debug=False
    #config_file = 'config_files/mali.cfg'
    utils.set_log_level(debug)
    config = utils.get_config(config_file)
    keywords = utils.get_keywords(config_file)

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
        logging.info('Reading in summary file {}'.format(articles_summary_filename))
        df_articles_summary = pd.read_csv(articles_summary_filename)
    else:
        logging.info('Creating summary file {}'.format(articles_summary_filename))
        columns = ['newspaper', 'article_number', 'title', 'topical']
        df_articles_summary = pd.DataFrame(columns=columns)
        index_article = 0
        for file in files_in_articles_folder:
            df_articles = pd.read_csv(articles_folder+'/'+file, sep='|')
            for index, article in df_articles.iterrows():
                row_to_add = [file, index, article['title'], None]
                df_articles_summary.loc[index_article] = row_to_add
                index_article += 1
        
        # Automised article annotation
        # load keywords
        df_locations = utils.read_keyword_csv(keywords['filename_locations'])
        keys_topical = utils.read_keyword_csv(keywords['filename_article_topical']) + df_locations
        keys_not_topical = utils.read_keyword_csv(keywords['filename_article_nontopical'])
        keys_manual_check = ast.literal_eval(keywords['keys_manual_check'])

        #set counters and annotate article titles
        cnt_true = 0
        cnt_false = 0
        cnt_total = 0
        cnt_check = 0
        
        for row in df_articles_summary.itertuples():
            title_summary = df_articles_summary.at[row.Index, 'title']
            logger.debug('{}'.format(title_summary.lower()))
            logger.debug('{}'.format(keys_manual_check))
            logger.debug('{}'.format([word in title_summary.lower() for word in keys_manual_check]))
            logger.debug('{}'.format([word for word in keys_manual_check]))
            log_string = ' -{index}- | {flag} | {word_list} | {title_summary}'
            if any(word.lower() in title_summary.lower() for word in keys_topical):
                df_articles_summary.loc[row.Index, 'topical'] = True
                cnt_true += 1
                logger.info(log_string.format(index=row.Index, flag='TRUE', title_summary=title_summary,
                                              word_list=[word for word in keys_topical if
                                                         word.lower() in title_summary.lower()]))
            elif any(word.lower() in title_summary.lower() for word in keys_not_topical):
                df_articles_summary.loc[row.Index, 'topical'] = False
                cnt_false += 1
                logger.info(log_string.format(index=row.Index, flag='FALSE', title_summary=title_summary,
                                              word_list=[word for word in keys_not_topical if
                                                         word.lower() in title_summary.lower()]))
            elif any(word.lower() in title_summary.lower() for word in keys_manual_check): 
                df_articles_summary.loc[row.Index, 'topical'] = None
                cnt_check += 1
                logger.info(log_string.format(index=row.Index, flag='CHECK', title_summary=title_summary,
                                              word_list=[word for word in keys_manual_check if
                                                         word.lower() in title_summary.lower()]))
            cnt_total += 1

        #print result summary and write to csv
        cnt_rest = cnt_total-cnt_true-cnt_false
        processing_result = '\n Finished processing: \n {cnt_total} articles in total\n {cnt_true} True \n ' \
                            '{cnt_false} False \n {cnt_rest} to be checked manually ({check} newspaper names problem)'
        processing_result = processing_result.format(cnt_total=cnt_total, cnt_true=cnt_true, cnt_false=cnt_false,
                                                     cnt_rest=cnt_rest, check = cnt_check)
        logger.info(processing_result)
        df_articles_summary.to_csv(articles_summary_filename, index=False)
        
    articles_to_analyze = df_articles_summary.loc[pd.isna(df_articles_summary['topical'])]
    number_to_analyze = len(articles_to_analyze)
    logging.info('Analyzing {} articles'.format(number_to_analyze))

    # Tag articles and save it in the summary
    cnt_article = 0
    for row in articles_to_analyze.itertuples():
        newspaper = articles_to_analyze.at[row.Index, 'newspaper']
        article_number = articles_to_analyze.at[row.Index, 'article_number']
        article = pd.read_csv(articles_folder+'/'+newspaper, sep='|').iloc[article_number]
        logging.info("\nArticle #{number}/{total}: {title}".format(
            number=cnt_article+1, total=number_to_analyze, title=article['title']))
        var_topical = input("Is it topical? t (True), f (False), i (Inspect text), q (Quit)  ")
        if var_topical == 'q':
            break
        elif var_topical == 'i':
            logging.info(article['text'])
            var_topical = input("Is it topical? t (True), f (False)  ")
        df_articles_summary.loc[row.Index, 'topical'] = var_topical == 't'
        cnt_article += 1
        df_articles_summary.to_csv(articles_summary_filename, index=False)

    # Use the summary to create a csv with only relevant articles
    columns = ['Unnamed: 0', 'title', 'publish_date', 'text', 'url']
    df_articles_topical = pd.DataFrame(columns=columns)
    relevant_articles = df_articles_summary[df_articles_summary['topical'] == True]
    logging.info('Saving {} topical articles'.format(len(relevant_articles)))
    for index, row in relevant_articles.iterrows():
        article = pd.read_csv(articles_folder+'/'+row['newspaper'], sep='|').iloc[row['article_number']]
        df_articles_topical.loc[index] = article
    logging.info("Saving all articles to {0}".format(output_directory))
    output_filename = utils.get_inspected_articles_output_filename(config)
    df_articles_topical.to_csv(os.path.join(output_directory, output_filename), sep='|', header=True)


if __name__ == '__main__':
    plac.call(main)

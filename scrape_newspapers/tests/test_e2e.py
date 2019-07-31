import os
import pandas as pd

TEST_ARTICLES_FILE = 'tests/articles_test_inondation_Mali.csv'
OLD_RESULTS = 'impact_data_test_inondation_Mali_prev'
NEW_RESULTS = 'impact_data_test_inondation_Mali_new'


def test_e2e():
    cmd = 'python get_impact_data.py config_files/mali.cfg' \
          ' -i {test_articles_file}' \
          ' -o {new_results}' \
          ' -d tests'
    cmd = cmd.format(test_articles_file=TEST_ARTICLES_FILE,
                     new_results=NEW_RESULTS)
    os.system(cmd)
    df_prev = pd.read_csv(os.path.join('tests', OLD_RESULTS+'.csv'), delimiter='|')
    df_new = pd.read_csv(os.path.join('tests', NEW_RESULTS+'.csv'), delimiter='|')
    assert(df_prev.equals(df_new))

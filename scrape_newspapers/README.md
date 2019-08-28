# Scrape Newspapers

A set of scripts for scraping news articles and extracting impact data

## General

Python package requirements are in `reuirements.pip` in the top-level directory.

Everything described below should be run from the `scrape_newspapers` directory.

All scripts take as input a configuration file, a couple of working
examples can be found in the `config_files` directory.

### Configuration files

The configuration files have two sections, `main` and `keywords`.

#### main
`country`: The name of the country, used for finding and labelling files and searching
a newspaper database\
`country_short`: Used for finding the location file, which has the path
 `locations/{country}/{country_short}.txt`\
`keyword`: The keyword to search for in article titles\
`model`: The spaCy model to use\
`language`: The language of the articles (so far
can only be 'english' or 'french'

### keywords
The parameters with names that begin with 'filename' refer to names of
files in the `keywords` directory that contain long lists of keywords.

## Scrape articles

Using the country name specified in the configuration file, searches
all newspapers listed at [ABYZ News links](http://www.abyznewslinks.com/),
and queries for articles with the keyword in the title.

Usage:
```
scrape_articles.py [-h] config_file
```
Output: For each newspaper, a pandas DataFrame of articles, in csv, with
row format: `['title', 'publish_date', 'text', 'url']`. The default
save location is `Articles_{keyword}_{country}/articles_{keyword}_{newspaper}.csv`.

## Inspect and tag articles

Analyze the output of the scraped articles and decide if each article is relevant or not.
This works in 4 steps:

1) A summary csv file is created, or read in if it already exists. This file
contains the title, newspaper name and index of all articles that were scraped, 
as well as a column for marking the relevance as `True` / `False`. It is saved as
`articles_processed/articles_summary_{keyword}_{country}.csv`. 

2) Automisation of the annotation process. 
Based on the the summary dataframe, this script checks the title for words that 
indicate the relevance or not. The result (True/False/blank) is written to the 
column `topical`.
Possible outcomes:
    - Article is relevant --> `True`
    This is based on the keywords in `Article_topical_{country}.txt` and 
    `Locations_{country}.txt`. Article_topical_{country}.txt contains words that
    indicate relevance, e.g. the target country president's name, the name of the
    people ('maliens' for Mali, 'français' for France) and other words indicating 
    relevance of the article.
    Locations_{country}.txt contains a selection of (larger) cities and provinces
    in a country, e.g. from Wikipedia. A complete list of a country's locations
    is not used, since it may also include very small villages that are recognised
    in parts of words and therefore falsly treated as True by the script, e.g. 
    village 'Da' in Mali is recognised in the word 'indonDAtion'.   
    - Article is not relevant --> `False`
    This is based on the keywords in `Article_nontopical_{country}.txt`. Keyword 
    examples are: countries outside target country, 'you searched for', words
    related to the target word ('flood'), but in a different sense: e.g. flooding 
    a 'stadium' with people, or a 'market' is flooded with certain products.
     - Article requires manual inspection of the article text --> left `blank`
    This is based on the keywords in `keys_manual_check` in the Config file. 
    These are be words that have ambiguous meaning: e.g. river 'Niger' 
    in Mali (relevant), or country 'Niger' (not relevant for floods in Mali). 
    This merely functions as a counter for these ambiguous words.
IMPORTANT: Choosing the right keywords voor (non)topical articles is a iterative
exercise. The user had to to check a sample of the annotation results (in Excel), 
to see if they are correct and to find more words to add to the (non)topical lists. 
The scripts prints for every title: the title, index, True/False/Check, and the 
word responsible for the choice of True/False/Check.
NOTE: all keywords need to be written in lower case and with AND without accents.

3) For all articles that still require their relevancy to be assessed,
the user will be shown the title of the article and prompted to evaluate it
as relevant (`y`/`n`). There is also the option `i` to view the article text,
and `q` to quit and save the current results. Only titles will be shown of 
articles where the cell in column `topical` is left blank.

4) The text from all articles with relevance marked as `True` is saved to a new file,
`articles_processed/articles_all_topical_{keyword}_{country}.csv`. 

Usage:
```
python inspect_articles_tag_topical.py [-h] [-r] config_file

positional arguments:
  config_file           Configuration file

optional arguments:
  -h, --help            show this help message and exit
  -r, --recreate-summary-file
                        Recreate the summary file
```
TBI: automatize the process with a classification algorithm, too few data so far

## Get impact data

Analyze the relevant articles and extract impact data. As input, takes
the file containing all of the relevant article text. The analysis is
divided into several components, as follows:

#### get_impact_data.py
Takes arguments from the command line, reads in the configuration
file and creates an `ImpactTableGenerator` instance,
which it uses to loop over the articles.

#### ImpactTableGenerator.py 

The `ImpactTableGenerator` class contains all of the high-level
information shared between articles that is necessary for 
evaluating their relevance. It consists of:
 - a dataframe containing all of the article text
 - a list of country locations from the 
    [National Geospatial Intelligence Agency](http://geonames.nga.mil/gns/html/namefiles.html),
    read in from `locations/{country}/{country_short}.txt`
 - a dictionary of keywords from the configuration file
 - an output dataframe
 - the loaded spAcy model

From an `ImpactTableGenerator` instance, it is possible to call
`loop_over_articles`, which creates and calls `analyze()` on an
`Article` instance for each of the relevant articles.

#### Article.py

The `Article` class constructor cleans up the article text, performs preprocessing
on numbers and person titles, and then tokenizes the text with spAcy.
It also determines a most probable location for the article.
The `analyze()` method then loops through all the sentences of the article,
calling `Sentence.analyze()` on each one, and appending the returned
impact data to a list which is then used to add information to the impact dataframe.

#### Sentence.py

The `Sentence` constructor strips newline characters from the text,
and tries to determine a best location for the sentence. The `analyze()`
method then checks for two types of impact information. First,
an `Ents` instance is created and analyzed, and next the sentence
text is searched for infrastructures.

#### Ents.py

An `Ents` instance is meant to consist of any tokens that are
cardinal numbers or money. With some spaCy models, this can
be achieved by selecting the corresponding entities, however
when those are not available, all `NUM` tokens and / or digits within
a sentence are selected.

The entities are then looped through in the `analyze()` method,
checking whether each entity is money, otherwise trying to determine 
which object it refers to. Finally, a location is assigned to the entity.

#### Usage
```
get_impact_data.py [-h] [-i None] [-o None] [-d None] config_file

positional arguments:
  config_file           Configuration file

optional arguments:
  -h, --help            show this help message and exit
  -i, --input-filename
                        Optional input filename
                        (default: articles_all_topical_{keyword}_{country}.csv)
  -o, --output-filename-base
                        Optional output filename base
                        (default: impact_data_{keyword}_{country})
  -d, --output-directory
                        Optional output directory
                        (default: impact_data)
 ```
Output: .csv and .xlsx files with the following structure :
```
[index=['location', 'date', 'newspaper'], columns=['damage_livelihood', 'damage_general',
                                                    'people_affected', 'people_dead',
                                                    'houses_affected', 'livelihood_affected',
                                                    'infrastructures_affected',
                                                    'infrastructures_mentioned',
                                                    'sentence(s)', 'article_title']]
```

#### End-to-end test

The file `articles_processed/tests/articles_test_inondation_Mali.csv` 
contains some article examples that are used for an end-to-end test.
The test can be run by executing `pytest` in the `scrape_newspapers`
directory.

The expected output file is 
`tests/impact_data_test_inondation_Mali_prev.csv` and the output
produced by your current version of the script will be named
`impact_data_test_inondation_Mali_new.csv`. The test will simply
tell you if the two output files differ.

You may sometimes make changes that improve the output results,
in which case you can move the `new` file to the `prev` file
and commit it to git. Also, please add any funny edge cases to
the list of example articles. 

author: Jacopo Margutti, 2019

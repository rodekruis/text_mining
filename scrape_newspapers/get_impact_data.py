import re
import os
import ast
import importlib
import unicodedata
from itertools import groupby

import plac
import spacy
from spacy.matcher import Matcher
import pandas as pd
from pandas import ExcelWriter
from word2number import w2n
from text_to_num import text2num
import numpy as np

utils = importlib.import_module('utils')

# location of gazetteers (http://geonames.nga.mil/gns/html/namefiles.html)
locations_folder = 'locations'

# location of keywords (victims, infrastructures)
locations_keywords = 'keywords'

# output directory
output_directory = 'impact_data'

LANGUAGES_WITH_ENTS = ['english']

CRAZY_NUMBER_CUTOFF = 1E6
USD_CUTOFF = 1E7
LOCAL_CURRENCY_CUTOFF = 1E11

LONG_ARTICLE = 50  # considered a long article, perhaps signed by a name
LOCATION_NAME_WORD_CUTOFF = 10


def load_locations(input_folder, country_short):
    """
    build a dictionary of locations {name: coordinates}
    from a gazetteer in tab-separated csv format (http://geonames.nga.mil/gns/html/namefiles.html)
    """
    columns = ['FULL_NAME_RO', 'FULL_NAME_ND_RO', 'LAT', 'LONG', 'ADM1']
    locations_df = pd.read_csv(input_folder+'/'+country_short+'.txt', sep='\t',
                               encoding='utf-8', usecols=columns)
    # this definitely needs to be refactored to another location,
    # but anyway if the country is mali take out niger (the river)
    # or maybe we should not be reading in any of the hydrographic locations?
    if country_short == 'ml':
        locations_df = locations_df[locations_df['FULL_NAME_RO'] != "Niger"]
    return locations_df


def find_locations(doc, locations_df, nlp):
    """
    Find locations of interest in a given text
    """
    # find locations and append them to list
    matcher = Matcher(nlp.vocab)
    _ = [matcher.add('locations', None, [{'LOWER': location.lower(), 'POS': pos}])
         for location in locations_df['FULL_NAME_RO'] for pos in ['NOUN', 'PROPN']]
    matches = matcher(doc)
    # As (longer) articles are often signed, toss out last location if it's close to the end
    # since it is probably someone's name
    if len(doc) > LONG_ARTICLE:
        try:
            if matches[-1][1] > len(doc) - LOCATION_NAME_WORD_CUTOFF:
                matches = matches[:-1]
        except IndexError:
            pass
    locations_found = [doc[i:j].text for (_, i, j) in matches]
    return matches, locations_found


def normalize_caseless(text):
    return unicodedata.normalize("NFKD", text.casefold())


def preprocess_french_number_words(text):
    # Since the French model has no entities, need to deal with number words by hand
    # for now. Could eventually train our own cardinal entity, but in the medium
    # term this should probably be made a pipeline component, although the text
    # immutability may be an issue
    french_number_words = {'millier': 1E3, 'milliers': 1E3,
                           'million': 1E6, 'millions': 1E6,
                           'milliard': 1E9, 'milliards': 1E9}

    words = text.split(' ')
    for i, word in enumerate(words):
        if word in french_number_words.keys():
            prev_word = words[i-1]
            if re.match('^\\d+$', prev_word):
                number = int(prev_word)
                need_to_merge = True
            else:
                try:
                    number = text2num(str(prev_word))
                    need_to_merge = True
                except ValueError:
                    number = 2  # Multiply 1 million or whatever by 2
                    need_to_merge = False

            number *= french_number_words[word]
            if need_to_merge:
                search_text = '{}\\s+{}'.format(prev_word, word)
            else:
                search_text = word
            text = re.sub(search_text, str(int(number)), text)
    return text


def preprocess_numbers(text, currencies_short):
    """
    Pre-process text
    """
    # merge numbers divided by whitespace: 20, 000 --> 20000
    # Also works with repeated groups, without comma, and with appended currency
    # e.g. 5 861 052 772FCFA --> 5861052772FCFA (won't work with accents though)
    numbers_divided = re.findall('\d+(?:\,*\s\d+\w*)+', text)
    if numbers_divided is not None:
        for number_divided in numbers_divided:
            if re.search('(20[0-9]{2}|19[0-9]{2})', number_divided) is not None:
                continue
            else:
                number_merged = re.sub('\,*\s', '', number_divided)
                text = re.sub(number_divided, number_merged, text)

    # split money: US$20m --> US$ 20000000 or US$20 --> US$ 20
    numbers_changed = []
    for currency in currencies_short:
        currency_regex = re.sub('\$', '\\\$', currency)
        numbers_divided = re.findall(re.compile(currency_regex+'[0-9.]+\s', re.IGNORECASE), text)
        for number_divided in numbers_divided:
            try:
                number_final = currency + ' ' + re.search('[0-9.]+\s', number_divided)[0]
                text = re.sub(re.sub('\$', '\\\$', number_divided), number_final, text)
            except:
                pass
        numbers_divided = re.findall(re.compile(currency_regex+'[0-9.]+[a-z]', re.IGNORECASE), text)
        for number_divided in numbers_divided:
            try:
                number_split_curr = re.sub(currency_regex, currency_regex+' ', number_divided)
                number_isolated = re.search('[0-9.]+[a-z]', number_split_curr)[0]
                number_text = re.search('[0-9.]+', number_isolated)[0]
                appendix = re.search('[a-z]', number_isolated)[0].lower()
                # try to convert number and appendix into one number
                try:
                    number = float(number_text)
                    if appendix == 'b':
                        number *= 1E9
                    elif appendix == 'm':
                        number *= 1E6
                    elif appendix == 'k':
                        number *= 1E3
                    else:
                        print('money conversion failed (', text, ') !!!')
                except:
                    pass
                number_final = re.sub(appendix, '', str(int(number)))
                number_final = currency + ' ' + number_final
                text = re.sub(re.sub('\$', '\\\$', number_divided), number_final, text)
                numbers_changed.append(number_final)
            except:
                pass
    return text


def clean(text, language):
    if language == 'english':
        return ''.join([i if (ord(i) < 128) and (i != '\'') else '' for i in text])
    else:
        return ''.join([i if (i != '\'') else '' for i in text])


def preprocess_titles(text, titles, language):
    # Remove proper names of people because they can have names of towns

    target_text_edit = text
    name_replacement = {
        'english': 'someone',
        'french': "quelq'un"
    }[language]
    name_pattern_query_list = [
        r'\.\s[A-Za-z]+\s[A-Z][a-z]+',
        r'\s[A-Za-z]+\s[A-Z][a-z]+',
        r'\.\s[A-Za-z]+',
        r'\s[A-Za-z]+',
    ]

    # filter names with titles (Mr., Ms. ...)
    # titles are case insensitive
    for title in titles:
        for query in name_pattern_query_list:
            query_string = r'(?i:{title}){query}'.format(title=title, query=query)
            target_text_edit = re.sub(query_string, name_replacement, target_text_edit)

    # filter article signatures
    article_signature_query_list = [
        r'[A-Z]+\s[A-Z]+\,\s[A-Za-z]+',  # e.g. MONICA KAYOMBO, Ndola
        r'[A-Z]+\s[A-Z]+\n[A-Za-z]+',  # e.g. MONICA KAYOMBO \n Ndola
        r'[A-Z]+\s[A-Z]+\n\n[A-Za-z]+',  # e.g. MONICA KAYOMBO \n\n Ndola
    ]
    for query in article_signature_query_list:
        pattern_signatures = re.compile(query)
        target_text_edit = re.sub(pattern_signatures, '', target_text_edit)

    return target_text_edit


def process_number_money(text, sentence_text, sentence, currencies_short, currencies_long, local_currency_names_short,
                         local_currency_names_long, local_currency_code, language):
    """
    Get unique currency format
    """
    currency = ''
    for currency_short in currencies_short:
        if currency_short in text.lower():
            currency = currency_short
            text = re.sub(re.compile(currency_short+'[\.]{0,1}', re.IGNORECASE), '', text)

    for currency_long in currencies_long:
        regex_currency = re.compile(currency_long, re.IGNORECASE)
        if re.search(regex_currency, sentence_text) is not None:
            for idx, word in enumerate(sentence):
                if word.text in text:
                    if currency_long in sentence[idx+1].text or currency_long in sentence[idx+2].text:
                        currency = currency_long
                    if currency_long in sentence[idx-1].text or currency_long in sentence[idx-2].text:
                        currency = currency_long
    if currency != '':
        if currency in local_currency_names_short or currency in local_currency_names_long:
            currency = local_currency_code
        else:
            currency = 'USD'

    number = process_number_words(text, language)
    return number, currency


def process_number_words(text_raw, language):
    """
    Convert number words into numbers
    """
    #TODO: check text2num behaviour
    if language == 'english':
        parser = w2n.word_to_num
    elif language == 'french':
        parser = text2num

    # make lowercase, remove commas
    text = text_raw.lower()
    text = re.sub('\n|\,|\.', '', text)
    text = text.strip()

    # fix misspelling: '30millions' --> '30 millions'
    for (number, word) in re.findall('([0-9\.]+)([a-z]+)', text):
        text = re.sub(str(number+word), str(number+' '+word), text)

    # special case: 'between x and y' --> '(x+y)/2'
    for (x_text, y_text) in re.findall('between\s([0-9a-z\s\-]+)\sand\s([0-9a-z\s\-]+)', text):
        try:
            x = parser(x_text)
            y = parser(y_text)
            text = str((x+y)/2.)
            return text
        except ValueError:
            print('number conversion failed (special case *between*): ', text)
            return text

    # special case: 'x per cent'
    for perc in re.findall('([0-9a-z\-]+)\sper\scent', text):
        try:
            text = str(parser(perc)) + '%'
            return text
        except ValueError:
            print('number conversion failed (special case *per cent*): ', text)
            return text

    # word_to_num not working, need to convert string to number
    for (number, word) in re.findall('([0-9\.]+)\s([a-z]+)', text):
        number_old = number
        if 'billion' in word:
            number = str(float(number)*1000000000)
        elif 'million' in word:
            number = str(float(number)*1000000)
        elif 'thousand' in word:
            number = str(float(number)*1000)
        text = re.sub(str(number_old+' '+word), number, text)

    # try first if it can be directly converted
    if not re.match('^\d+$', text):  # Only try on strings containing non-digits
        try:
            text = str(parser(text))
        except ValueError:
            # remove words that cannot be converted to numbers: 'more than seven' --> 'seven'
            text_clean = ''
            for word in re.findall('[a-z0-9\-]+', text):
                try:
                    parser(word)
                    text_clean += word
                    if re.search(r'\d', word) is None:
                        text_clean += ' '
                except ValueError:
                    continue

            # try to convert what is left into one number
            try:
                text = str(parser(text_clean))
            except ValueError:
                # if we have a vague number word: assign a reasonable number
                if 'billions' in text:
                    text = '2000000000'
                elif 'millions' in text:
                    text = '2000000'
                elif 'hundreds of thousands' in text:
                    text = '200000'
                elif 'tens of thousands' in text:
                    text = '20000'
                elif 'thousands' in text:
                    text = '2000'
                elif 'hundreds' in text:
                    text = '200'
                elif 'dozens' in text:
                    text = '24'
                elif 'tens' in text:
                    text = '20'
                elif 'dozen' in text:
                    text = '12'
                else:
                    print('number conversion failed (', text, ') !!!')
                    text = re.sub('[^0-9\.]+', '', text)
    return text


def check_if_money(ent_text, sentence, currencies_short, currencies_long,
                   local_currency_names_short, local_currency_names_long, local_currency_code):
    """
    Check if numerical entity is monetary value
    """
    is_money = False
    currency_found = ''
    currencies_all = currencies_long+currencies_short
    
    for currency in currencies_all:
        if currency in ent_text.lower():
            is_money, currency_found = True, currency
    
    for currency in currencies_all:
        regex_currency = re.compile(currency, re.IGNORECASE)
        if re.search(regex_currency, sentence.text) is not None:
            for idx, word in enumerate(sentence):
                if word.text in ent_text:
                    try:
                        if currency == sentence[idx+1].text or currency == sentence[idx+2].text:
                            is_money, currency_found = True, currency
                        if currency == sentence[idx-1].text or currency == sentence[idx-2].text:
                            is_money, currency_found = True, currency
                    except:
                        pass
                    
    if currency_found != '':
        if currency_found in local_currency_names_short or \
                currency_found in local_currency_names_long:
            currency_found = local_currency_code
        else:
            currency_found = 'USD'

    return is_money, currency_found


def get_object(ent, sentence, language):
    """
    Get what a given number refers to
    """
    obj = ''

    if language in LANGUAGES_WITH_ENTS :
        # get all tokens of which entity is composed
        tokens_in_ent = []
        for idx, word in enumerate(ent):
            tokens_in_ent.append(word)
        # get last token in sentence
        for idx, word in enumerate(sentence):
            if word.text == tokens_in_ent[-1].text:
                # first attempt: look for head of type NOUN
                if word.head.pos_ == 'NOUN':
                    obj = word.head.text
                    break
                # second attempt: navigate the children list, look for an 'of'
                for possible_of in word.children:
                    if possible_of.text == 'of':
                        for possible_object in possible_of.children:
                            obj = 'of ' + possible_object.text
                            break

    else:
        # If no ents, need to navigate the tree by hand
        obj = ent.head.text

    return obj


def check_list_locations(locations, sentence, language):
    """
    Check if locations are in a list (e.g. "Kalabo, Chibombo and Lundazi")
    or if they are scattered around the sentence
    """

    and_word = {
        'french': 'et',
        'english': 'and'
    }[language]
    
    list_final = []

    if len(list(set(locations))) < 2:
        return list_final

    match_locations = []
    for location in locations:
        match = re.search(location, sentence)
        if match:
            match_locations.append((match.span()[0], match.span()[1]))
    
    if len(match_locations) < 2:
        return list_final

    in_between = []
    for i in range(0,len(match_locations)-1):
        in_between.append(sentence[match_locations[i][1]:match_locations[i+1][0]])

    merge = ''
    cnt_num_loc = 1
    list_loc = []

    for cnt in range(0, len(match_locations)-1):
        if len(in_between[cnt]) > 8:
            merge = ''
            cnt_num_loc = 1
            list_loc = []
            continue
        if ',' in in_between[cnt]:
            if cnt_num_loc == 1:
                merge += sentence[match_locations[cnt][0]:match_locations[cnt+1][1]]
            else:
                merge += sentence[match_locations[cnt][1]:match_locations[cnt+1][1]]
            cnt_num_loc += 1
            list_loc.append(locations[cnt])
            if ', {}'.format(and_word) in in_between[cnt]:
                list_loc.append(locations[cnt+1])
                list_final.append((merge, cnt_num_loc, list_loc))
                merge = ''
                cnt_num_loc = 1
                list_loc = []
        elif and_word in in_between[cnt]:
            if cnt_num_loc == 1:
                merge += sentence[match_locations[cnt][0]:match_locations[cnt+1][1]]
            else:
                merge += sentence[match_locations[cnt][1]:match_locations[cnt+1][1]]
            cnt_num_loc += 1
            list_loc.append(locations[cnt])
            list_loc.append(locations[cnt+1])
            list_final.append((merge, cnt_num_loc, list_loc))
            merge = ''
            cnt_num_loc = 1
            list_loc = []
    return list_final


def most_common(lst, locations_df):
    location_counts = [(i, len(list(c))) for i, c in groupby(sorted(lst))]
    # Find the places(s) with max counts
    counts = [count[1] for count in location_counts]
    idx_max = np.where(np.max(counts) == counts)[0]
    # Set location to first entry, this works if there is only one location, or as a fallback
    # if the multiple location handling doesn't work
    location = lst[idx_max[0]]
    # If there is more than one location, take the lowest level admin region.
    if len(idx_max) > 1:
        try:
            lst_max = [lst[idx] for idx in idx_max]
            location_info = locations_df[locations_df['FULL_NAME_RO'].isin(lst_max)]
            location = location_info.groupby('FULL_NAME_RO')['ADM1'].min().idxmin()
        except ValueError:  # in case location_info is empty due to string matching problem reasons
            pass
    return location


def sum_values(old_string, new_string, new_addendum, which_impact_label):

    final_number = ''
    final_addendum = ''

    if (which_impact_label == 'damage_livelihood') or (which_impact_label == 'damage_general'):
        for (number, currency) in re.findall('([0-9\.]+)[\s]+(.+)', old_string):
            if  new_addendum == currency:
                if int(number) == int(new_string):
                    # same number, probably a repetition... do not sum
                    final_number = str(int(number))
                else:
                    final_number = str(int(number) + int(new_string))
                final_addendum = new_addendum
            else:
                print('different currencies, dont know how to sum !!!!')

    elif (which_impact_label == 'houses_affected') or (which_impact_label == 'people_affected') or (which_impact_label == 'people_dead'):
        final_number = str(int(old_string) + int(new_string))

    else:
        #TODO: figure out why this isn't catching all duplicate sentences
        if (new_string.lower() not in old_string.lower() and
                old_string.lower() not in new_string.lower()):
              final_number = old_string + ', ' + new_string
              final_addendum = new_addendum
        else:
            final_number = old_string

    return str(final_number + ' ' + final_addendum).strip()


def save_in_dataframe(df_impact, location, date, article_num, label, number_or_text, addendum, sentence, title):
    """
    Save impact data in dataframe, sum entries if necessary
    """
    final_index = (location, date, article_num)
    # first, check if there's already an entry for that location, date and label
    # if so, sum new value to existing value
    if final_index in df_impact.index:
        if str(df_impact.loc[final_index, label]) != 'nan':
            new_value = sum_values(str(df_impact.loc[final_index, label]), number_or_text, addendum, label)
        else:
            new_value = number_or_text
        df_impact.loc[final_index, label] = new_value
        new_sentence = sum_values(df_impact.loc[final_index, 'sentence(s)'],
                                  sentence, '', 'sentence(s)')
        new_title = sum_values(df_impact.loc[final_index, 'article_title'], title, '', 'title')
        df_impact.loc[final_index, ['sentence(s)', 'article_title']] = [new_sentence, new_title]
        return
    # otherwise just save the new entry
    df_impact.loc[final_index, label] = str(number_or_text+' '+addendum).strip()
    df_impact.loc[final_index, ['sentence(s)', 'article_title']] = [sentence, title]


################################################################################

@plac.annotations(
    config_file="Configuration file",
    input_filename=("Optional input filename", "option", "i", str),
    output_filename_base=("Optional output filename base", "option", "o", str)
)
def main(config_file, input_filename=None, output_filename_base=None):

    config = utils.get_config(config_file)
    keywords = utils.get_keywords(config_file)

    # create output dir if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    if output_filename_base is None:
        output_filename_base = 'impact_data_{keyword}_{country}'.format(
            keyword=config['keyword'], country=config['country']
        )
    writer = ExcelWriter(os.path.join(output_directory, output_filename_base+'.xlsx'))

    # load location dictionary
    locations_df = load_locations(locations_folder + '/' + config['country'], config['country_short'])
    
    # load NLP model
    print("Loading model {}".format(config['model']))
    nlp = spacy.load(config['model'])

    # load DataFrame with articles
    input_directory = utils.INPSECTED_ARTICLES_OUTPUT_DIR
    if input_filename is None:
        input_filename = utils.get_inspected_articles_output_filename(config)
    df = pd.read_csv(os.path.join(input_directory, input_filename), sep='|')
    # select only relevant ones
    df = df.drop_duplicates(['title','text'], keep=False)

    # convert all dates into datetime
    df['publish_date'] = df['publish_date'].apply(pd.to_datetime)
    print('got ', len(df), 'articles:')
    print(df['publish_date'].min().strftime('%Y-%m-%d'), ' -- ', df['publish_date'].max().strftime('%Y-%m-%d'))
    
    # define keywords
    type_people = pd.read_csv(os.path.join(locations_keywords, keywords['filename_type_people']),
                              header=None, encoding='latin-1')[0].tolist()
    type_infrastructure = pd.read_csv(os.path.join(locations_keywords, keywords['filename_type_infrastructures']),
                                      header=None, encoding='latin-1')[0].tolist()
    donation = ast.literal_eval(keywords['donation'])
    type_livelihood = ast.literal_eval(keywords['type_livelihood'])
    type_people_multiple = ast.literal_eval(keywords['type_people_multiple'])
    type_people_death = ast.literal_eval(keywords['type_people_death'])
    list_verb_death = ast.literal_eval(keywords['list_verb_death'])
    type_house = ast.literal_eval(keywords['type_house'])
    local_currency_names_short = ast.literal_eval(keywords['local_currency_names_short'])
    currency_short = local_currency_names_short +\
                     ast.literal_eval(keywords['currency_short'])
    local_currency_code = keywords['local_currency_code']
    local_currency_names_long = ast.literal_eval(keywords['local_currency_names_long'])
    currency_long = local_currency_names_long +\
                    ast.literal_eval(keywords['currency_long'])
    titles = ast.literal_eval(keywords['titles'])

    # initialize output DatFrame
    df_impact = pd.DataFrame(index=pd.MultiIndex(levels=[[], [], []],
                                                 codes=[[], [], []],
                                                 names=[u'location',
                                                        u'date',
                                                        u'article_num']),
                             columns=['damage_livelihood', 'damage_general',
                                      'people_affected', 'people_dead',
                                      'houses_affected', 'livelihood_affected',
                                      'infrastructures_affected',
                                      'infrastructures_mentioned',
                                      'sentence(s)', 'article_title'])

    # loop over articles
    n_articles = len(df)
    for id_row in range(n_articles):
        print("Analyzing article {}/{}...".format(id_row+1, n_articles))
        article_text = df.iloc[id_row]['text']
        title = df.iloc[id_row]['title']
        doc_with_title = title + '.\n' + article_text

        article_num = df.iloc[id_row]['Unnamed: 0']
        publication_date = str(df.iloc[id_row]['publish_date'].date())

        article_text = preprocess_french_number_words(article_text)
        article_text = preprocess_numbers(article_text, currency_short)
        article_text = clean(article_text, config['language'])
        article_text = preprocess_titles(article_text, titles, config['language'])

        # TODO: perhaps use doc_with_title here if article text is below some word count,
        #  but need to be careful of duplicates
        doc = nlp(article_text)

        # set location (most) mentioned in the document
        # discard documents with no locations
        location_matches, locations_document = find_locations(doc, locations_df, nlp)

        # fix ambiguities: [Bongo West, Bongo] --> [Bongo-West, Bongo]
        loc2_old, loc1_old = '', ''
        for loc1 in locations_document:
            for loc2 in locations_document:
                if loc1 in loc2 and loc1 != loc2:
                    loc2_old = loc2
                    loc1_old = loc1
                    loc2 = re.sub(' ', '-', loc2_old)
                    doc_with_title = re.sub(loc2_old, loc2, doc_with_title)
        if loc2_old != '':
            idx = locations_document.index(loc2_old)
            locations_document[idx] = re.sub(' ', '-', locations_document[idx])
            idx = locations_document.index(loc1_old)
            locations_document[idx] = ' '+locations_document[idx]
        if len(locations_document) == 1:
            # easy case, document mentions one location only
            location_document = locations_document[0]
        elif len(locations_document) > 1:
            # multiple locations mentioned, take the most common
            location_document = most_common(locations_document, locations_df)
        elif len(locations_document) == 0:
            # no location mentioned, document not useful
            print('WARNING: no locations mentioned in document')
            continue

        # loop over sentences
        for sentence in doc.sents:

            # remove newlines
            sentence_text = re.sub('\n', ' ', sentence.text)
            sentence_text = re.sub('-', ' ', sentence_text)

            # get locations mentioned in the sentence
            location_final = ''
            location_lists = []
            # Use locations from the full doc
            locations_found = [doc[i].text for (_, i, _) in location_matches
                               if sentence.start <= i < sentence.end]
            # fix ambiguities: [Bongo West, Bongo] --> [Bongo-West, Bongo]
            loc2_old, loc1_old = '', ''
            for loc1 in locations_found:
                for loc2 in locations_found:
                    if loc1 in loc2 and loc1 != loc2:
                        loc2_old = loc2
                        loc1_old = loc1
                        loc2 = re.sub(' ', '-', loc2_old)
                        sentence_text = re.sub(loc2_old, loc2, sentence_text)
            if loc2_old != '':
                idx = locations_found.index(loc2_old)
                locations_found[idx] = re.sub(' ', '-', locations_found[idx])
                idx = locations_found.index(loc1_old)
                locations_found[idx] = ' '+locations_found[idx]

            # determine location, 3 cases:
            if len(locations_found) == 1:
                # easy case, assign all damages to the location
                location_final = locations_found[0]

            elif len(locations_found) > 1:
                # multiple locations mentioned!
                # will create a list of locations and later assign it to the closest target
                location_final = 'TBI'
                # first, get a list of locations in the order in which they appear in the sentence
                positions = []
                for loc in locations_found:
                    positions.append(sentence_text.find(loc))
                locations_found_order = [x for _,x in sorted(zip(positions,locations_found))]
                # check if some locations are mentioned within a list (e.g. Paris, London and Rome)
                location_lists = check_list_locations(locations_found_order, sentence_text,
                                                      config['language'])
                # add a list of locations, merging those that are within a list
                locations_found_merged = locations_found_order.copy()
                for loc in locations_found_order:
                    if any(loc in loc_list for loc_list, num, loc_sublist in location_lists):
                        locations_found_merged.remove(loc)
                for loc in locations_found_merged:
                    location_lists.append((loc, 1, [loc]))
                if len(location_lists) == 0:
                    for loc in locations_found:
                        location_lists.append((loc, 1, [loc]))

            elif len(locations_found) == 0:
                # no locations mentioned in the sentence, use the paragraph one
                location_final = location_document

            # loop over numerical entities,
            # check if it's impact data and if so, add to dataframe
            if config['language'] in LANGUAGES_WITH_ENTS:
                ents = filter(lambda w: (w.label_ == 'CARDINAL') | (w.label_ == 'MONEY'),
                              sentence.as_doc().ents)
            else:
                # Sometimes number tokens are classified as e.g. pronouns so also check for digits
                ents = [token for token in sentence if (token.pos_ == 'NUM' or token.is_digit)]

            for ent in ents:
                # get entity text and clean it
                ent_text = re.sub('\n', '', ent.text).strip()
                if ent_text == '':
                    continue
                number = '' # number associated to entity
                addendum = '' # extra info (currency or object)
                impact_label = '' # label specifying the nature of the impact data

                is_money, currency_found = check_if_money(ent_text, sentence, currency_short, currency_long,
                                                          local_currency_names_short,
                                                          local_currency_names_long,
                                                          local_currency_code)

                # check if it's monetary value
                if is_money:
                    number, addendum = process_number_money(ent_text, sentence_text, sentence, currency_short,
                                                            currency_long, local_currency_names_short,
                                                            local_currency_names_long, local_currency_code,
                                                            config['language'])
                    if addendum == '':
                        addendum = currency_found
                    try:
                        int(float(number))
                    except ValueError:
                        continue
                    if int(number) >= USD_CUTOFF and addendum == 'USD':
                        print('WARNING: too many dollars:')
                        print(sentence_text)
                        continue
                    if int(number) >= LOCAL_CURRENCY_CUTOFF and addendum == local_currency_code:
                        print('WARNING: too much local currency:')
                        print(sentence_text)
                        continue
                    # check if root is damage-like
                    token_root = next(iter([token for token in sentence if token.dep_=='ROOT']), None)
                    if any(type in token_root.text for type in donation):
                        # donation, discard
                        # print('donation, discarding')
                        continue
                    else:
                        if any(type == sentence_text.lower() for type in type_livelihood):
                            # print('    proposing assignement: ', ent_text, ' in damage_livelihood')
                            impact_label = 'damage_livelihood'
                        else:
                            # print('    proposing assignement: ', ent_text, ' in damage_general')
                            impact_label = 'damage_general'

                # if it's not monetary value, look for object
                else:
                    # get the object, i.e. what the number refers to
                    obj = get_object(ent, sentence, config['language'])
                    number = process_number_words(ent_text, config['language'])
                    if (obj != '') & (number != ''):
                        if any(type_obj in obj.lower() for type_obj in type_people_death):
                            impact_label = 'people_dead'
                        elif any(type_obj in obj.lower() for type_obj in type_people):
                            # if it's "family" or similar, multiply by 4
                            if any(type_obj in obj.lower() for type_obj in type_people_multiple):
                                number = str(int(round(float(number)*4)))
                            # determine if they are dead or not
                            is_dead = False
                            if config['language'] in LANGUAGES_WITH_ENTS:
                                number_and_object = [tok for tok in ent]
                            else:
                                number_and_object = [ent, ent.head]
                            for tok in sentence:
                                if tok.text == obj:
                                    number_and_object.append(tok)
                            # first, check if root verb or its children
                            # (e.g. 'seven people who died') are death-like
                            roots_ch = tok.children
                            for tok in number_and_object:
                                roots_and_children = list()
                                roots_and_children.append(tok.head.text.lower())
                                roots_and_children += [ch.text.lower() for ch in roots_ch]
                                if any(verb in roots_and_children for verb in list_verb_death):
                                    is_dead = True

                            if is_dead == True:
                                impact_label = 'people_dead'
                            else:
                                impact_label = 'people_affected'
                        elif any(type_obj in obj.lower() for type_obj in type_house):
                            impact_label = 'houses_affected'
                        elif any(type_obj in obj.lower() for type_obj in type_infrastructure):
                            impact_label = 'infrastructures_affected'
                            for type_obj in filter(lambda w: w in obj.lower(), type_infrastructure):
                                addendum += type_obj
                        elif any(type_obj in obj.lower() for type_obj in type_livelihood):
                            impact_label = 'livelihood_affected'
                            for type_obj in filter(lambda w: w in obj.lower(), type_livelihood):
                                addendum += type_obj
                        else:
                            # nothing interesting, discarding
                            continue
                    else:
                        # object not found, discarding
                        continue
                    try:
                        if int(number) >= CRAZY_NUMBER_CUTOFF:
                            print('WARNING: crazy number (not assigned)', number)
                            print(sentence_text)
                            continue
                    except:
                        pass
                # safety check
                if impact_label.strip() == '':
                    print('WARNING: impact_label NOT ASSIGNED !!!')
                    continue

                # assign location
                location_impact_data = location_final

                # if multiple locations or lists of locations are found
                # check which is the closest one to the impact data
                if location_final == 'TBI':
                    # compute distances between entity (i.e. impact data) and locations, choose the closest one
                    distances_locations_entities = []
                    ent_text = ent_text.strip()
                    ent_text = re.sub('\n', '', ent_text)
                    for idx, (loc, num, loc_sublist) in enumerate(location_lists):
                        pattern_entity = re.compile(str('('+re.escape(loc)+'(.*)'+re.escape(ent_text)+'|'+re.escape(ent_text)+'(.*)'+re.escape(loc)+')'), re.IGNORECASE)
                        distances_locations_entities += [(loc, len(chunk[0])-len(loc)-len(ent_text), num, loc_sublist) for chunk in re.finditer(pattern_entity, sentence_text)]
                    closest_entity = min(distances_locations_entities, key=lambda t: t[1])
                    # if closest location is a list, location_impact_data will be a list of strings
                    # otherwise just a string
                    if closest_entity[2] > 1:
                        location_impact_data = closest_entity[3] # get list of locations in the list
                    else:
                        location_impact_data = closest_entity[0]

                # save to dataframe
                if type(location_impact_data) is str:
                    location_impact_data = location_impact_data.strip()
                    # safety check
                    if location_impact_data == '':
                        print('WARNING: location_impact_data NOT FOUND !!!')
                        continue
                    # one location, just append impact data to that one
                    save_in_dataframe(df_impact, location_impact_data,
                                      publication_date, article_num, impact_label,
                                      number, addendum, sentence_text, title)
                if type(location_impact_data) is list:
                    # multiple locations, divide impact data equally among them
                    number_divided = ''
                    try:
                        number_divided = str(int(int(number)/len(location_impact_data)))
                    except ValueError:
                        print('division failed: ', number)
                        number_divided = number
                    for location in location_impact_data:
                        location = location.strip()
                        # safety check
                        if location == '':
                            print('WARNING: location_impact_data NOT FOUND !!!')
                            continue
                        save_in_dataframe(df_impact, location,
                                      publication_date, article_num, impact_label,
                                      number_divided, addendum, sentence_text, title)

            # *****************************************************************            
            # look for infrastructures (not in numerical entities)
            # if found, add to dataframe
            
            int_inf_in_sent = []
            for token in sentence:
                if token.text in [ent.text for ent in filter(lambda w: (w.label_ == 'CARDINAL') | (w.label_ == 'MONEY'), sentence.as_doc().ents)]:
                    continue
                for int_inf in type_infrastructure:
                    if (normalize_caseless(int_inf) in normalize_caseless(token.text)) and (len(normalize_caseless(token.text)) <= len(normalize_caseless(int_inf))+1):
                        int_inf_in_sent.append(token)

            for infrastructure in int_inf_in_sent:

                # assign location
                location_infrastructure = location_final
                inf_text = infrastructure.text.strip()
                inf_text = re.sub('\n', '', inf_text)

                # if multiple locations (or lists of locations) are found
                # check which is the closest one to the impact data
                if location_final == 'TBI':
                    # compute distances between infrastructure and locations, choose the closest one
                    distances_locations_entities = []
                    for idx, (loc, num, loc_sublist) in enumerate(location_lists):
                        pattern_entity = re.compile(str('('+re.escape(loc)+'(.*)'+re.escape(inf_text)+'|'+re.escape(inf_text)+'(.*)'+re.escape(loc)+')'), re.IGNORECASE)
                        distances_locations_entities += [(loc, len(chunk[0])-len(loc)-len(inf_text), num, loc_sublist) for chunk in re.finditer(pattern_entity, sentence_text)]
                    closest_entity = min(distances_locations_entities, key = lambda t: t[1])
                    # if closest location is a list, location_impact_data will be a list of strings
                    # otherwise just a string
                    if closest_entity[2] > 1:
                        location_infrastructure = closest_entity[3] # get list of locations in the list
                    else:
                        location_infrastructure = closest_entity[0]

                if type(location_infrastructure) is str:
                    location_infrastructure = location_infrastructure.strip()
                    # safety check
                    if location_infrastructure == '':
                        print('WARNING: location_infrastructure NOT FOUND !!!')
                        continue
                    # one location, just append infrastructure to that one
                    save_in_dataframe(df_impact, location_infrastructure,
                                      publication_date, article_num, 'infrastructures_mentioned',
                                      inf_text, '', sentence_text, title)
                if type(location_infrastructure) is list:
                    # multiple locations and one infrastructure mentioned, assign to all
                    for location in location_infrastructure:
                        location = location.strip()
                        # safety check
                        if location == '':
                            print('WARNING: location_infrastructure NOT FOUND !!!')
                            continue
                        save_in_dataframe(df_impact, location,
                                          publication_date, article_num, 'infrastructures_mentioned',
                                          inf_text, '', sentence_text, title)
            # ******************************************************************
        print("...finished article {}/{}, updating file\n".format(id_row+1, n_articles))
        df_impact.to_csv(os.path.join(output_directory, output_filename_base+'.csv'),
                         mode='w', encoding='utf-8', sep='|')
        df_impact.to_excel(writer, 'Sheet1')
        writer.save()

    print('found ', len(df_impact), ' entries')

    df_impact.dropna(how='all', inplace=True)

    print(df_impact.describe())
    print(df_impact.head())
    
    df_impact.to_csv(os.path.join(output_directory, output_filename_base+'.csv'),
                     mode='w', encoding='utf-8', sep='|')
    df_impact.to_excel(writer, 'Sheet1')
    writer.save()


if __name__ == '__main__':
    plac.call(main)

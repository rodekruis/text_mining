#!/usr/bin/env python
# coding: utf8\
from __future__ import unicode_literals, print_function

import plac
import spacy
import pandas as pd
import re
import unicodedata
from word2number import w2n
from pandas import ExcelWriter
import os
from fuzzywuzzy import process
from fuzzywuzzy import fuzz

# names of local currency
local_currency_code ='UGX'
local_currency_names_short = ['USh', 'UGX', 'UGS', 'sh']
local_currency_names_long = ['shilling']

# location of gazetteers (http://geonames.nga.mil/gns/html/namefiles.html)
locations_folder = 'locations'

# location of keywords (victims, infrastructures)
locations_keywords = 'keywords'

# output directory
output_directory = 'impact_data'

# input directory
input_directory = 'articles_processed'

def LoadLocations(input_folder, country_short):
    """
    build a dictionary of locations {name: coordinates}
    from a gazetteer in tab-separated csv format (http://geonames.nga.mil/gns/html/namefiles.html)
    """
    locations_df = pd.read_csv(input_folder+'/'+country_short+'.txt', sep='\t')
    # create a dictionary locations : coordinates
    locations_dict = dict(zip(locations_df.FULL_NAME_ND_RO, zip(locations_df.LAT, locations_df.LONG)))
    return locations_dict

def FindLocations(target_sentence, locations_dict):
    """
    Find locations of interest in a given text
    """
    
    locations_found = []
    text = target_sentence.text
    
    # skip non-string values
    if type(text) != str:
        return []
    else:
        # find locations and append them to list
        ratio_loc = process.extract(text, locations_dict.keys(), scorer = fuzz.token_set_ratio)
        locations_found = []
        for l,v in ratio_loc: 
            if v > 95:
                locations_found.append(l)
        return locations_found

def normalize_caseless(text):
    return unicodedata.normalize("NFKD", text.casefold())

def preprocess_text(text, currencies_short):
    """
    Pre-process text
    """

    # merge numbers divided by whitespace: 20, 000 --> 20000
    numbers_divided = re.findall('[0-9]+\,\s[0-9]+', text)
    if numbers_divided is not None:
        for number_divided in numbers_divided:
            if re.search('(20[0-9]{2}|19[0-9]{2})', number_divided) is not None:
                # print('probably a date, not merging: ', number_divided)
                continue
            else:
                number_merged = re.sub('\,\s', '', number_divided)
                text = re.sub(number_divided, number_merged, text)
                # print('merging numbers: ', number_divided, ' --> ', number_merged)
            
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

    # get onli ASCII characters, remove "\'"
    text = clean(text)
    
    target_text_edit = text
    # filter names with titles (Mr., Ms. ...)
    # important: some people have names of towns!
    titles = ['Mr', 'Mrs', 'Ms', 'Miss', 'Senator', 'President', 'Minister',
              'Councillor', 'Mayor', 'Governor', 'Secretary', 'Attorney',
              'Chancellor', 'Judge', 'Don', 'Father', 'Dr', 'Doctor', 'Prof',
              'Professor']
    for title in titles:
        target_text_edit = re.sub(title+'\.\s[A-Za-z]+\s[A-Z][a-z]+', 'someone', target_text_edit)
        target_text_edit = re.sub(title+'\s[A-Za-z]+\s[A-Z][a-z]+', 'someone', target_text_edit)
        target_text_edit = re.sub(title+'\.\s[A-Za-z]+', 'someone', target_text_edit)
        target_text_edit = re.sub(title+'\s[A-Za-z]+', 'someone', target_text_edit)

    # filter article signatures
    pattern_signatures_head = re.compile(r'[A-Z]+\s[A-Z]+\,\s[A-Za-z]+') # e.g. MONICA KAYOMBO, Ndola
    target_text_edit = re.sub(pattern_signatures_head, '', target_text_edit)
    pattern_signatures_foot = re.compile(r'[A-Z]+\s[A-Z]+\n[A-Za-z]+') # e.g. MONICA KAYOMBO \n Ndola
    target_text_edit = re.sub(pattern_signatures_foot, '', target_text_edit)
    pattern_signatures_foot = re.compile(r'[A-Z]+\s[A-Z]+\n\n[A-Za-z]+') # e.g. MONICA KAYOMBO \n\n Ndola
    target_text_edit = re.sub(pattern_signatures_foot, '', target_text_edit)

    return target_text_edit

def process_number_money(text, sentence_text, sentence, currencies_short, currencies_long):
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
                    if (currency_long in sentence[idx+1].text or currency_long in sentence[idx+2].text):
                        currency = currency_long
                    if (currency_long in sentence[idx-1].text or currency_long in sentence[idx-2].text):
                        currency = currency_long
    if currency != '':
        if (currency in local_currency_names_short or currency in local_currency_names_long):
            currency = local_currency_code
        else:
            currency = 'USD'

    number = process_number_words(text)
    return (number, currency)

def process_number_words(text_raw):
    """
    Convert number words into numbers
    """

    # make lowercase, remove commas
    text = text_raw.lower()
    text = re.sub('\n', '', text)
    text = re.sub(',', '', text)
    text = text.strip()

    # fix misspelling: '30millions' --> '30 millions'
    for (number, word) in re.findall('([0-9\.]+)([a-z]+)', text):
        text = re.sub(str(number+word), str(number+' '+word), text)

    # special case: 'between x and y' --> '(x+y)/2'
    for (x_text, y_text) in re.findall('between\s([0-9a-z\s\-]+)\sand\s([0-9a-z\s\-]+)', text):
        try:
            x = w2n.word_to_num(x_text)
            y = w2n.word_to_num(y_text)
            text = str((x+y)/2.)
            return text
        except ValueError:
            print('number conversion failed (special case *between*): ', text)
            return text

    # special case: 'x per cent'
    for perc in re.findall('([0-9a-z\-]+)\sper\scent', text):
        try:
            text = str(w2n.word_to_num(perc)) + '%'
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
    try:
        text = str(w2n.word_to_num(text))
    except ValueError:
        # remove words that cannot be converted to numbers: 'more than seven' --> 'seven'
        text_clean = ''
        for word in re.findall('[a-z0-9\-]+', text):
            try:
                w2n.word_to_num(word)
                text_clean += word
                if re.search(r'\d', word) is None:
                    text_clean += ' '
            except ValueError:
                continue

        # try to convert what is left into one number
        try:
            text = str(w2n.word_to_num(text_clean))
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

def is_money(ent_text, sentence, currencies_short, currencies_long):
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
                        if (currency == sentence[idx+1].text or currency == sentence[idx+2].text):
                            is_money, currency_found = True, currency
                        if (currency == sentence[idx-1].text or currency == sentence[idx-2].text):
                            is_money, currency_found = True, currency
                    except:
                        pass
                    
    if currency_found != '':
        if (currency_found in local_currency_names_short or \
            currency_found in local_currency_names_long):
            currency_found = local_currency_code
        else:
            currency_found = 'USD'

    return (is_money, currency_found)

def get_object(ent, sentence, doc_text):
    """
    Get what a given number refers to
    """
    object = ''

    # get all tokens of which entity is composed
    tokens_in_ent = []
    for idx, word in enumerate(ent):
        tokens_in_ent.append(word)

    # get last token in sentence
    for idx, word in enumerate(sentence):
        if word.text == tokens_in_ent[-1].text:
            # first attempt: look for head of type NOUN
            if word.head.pos_ == 'NOUN':
                object = word.head.text
                break
            # second attempt: navigate the children list, look for an 'of'
            for possible_of in word.children:
                if possible_of.text == 'of':
                    for possible_object in possible_of.children:
                        object = 'of ' + possible_object.text
                        break

    return object

def check_list_locations(locations, sentence):
    """
    Check if locations are in a list (e.g. "Kalabo, Chibombo and Lundazi")
    or if they are scattered around the sentence
    """
    
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
            if ', and' in in_between[cnt]:
                list_loc.append(locations[cnt+1])
                list_final.append((merge, cnt_num_loc, list_loc))
                merge = ''
                cnt_num_loc = 1
                list_loc = []
        elif 'and' in in_between[cnt]:
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

def most_common(lst):
    return max(set(lst), key=lst.count)

def clean(text):
    return ''.join([i if (ord(i) < 128) and (i!='\'') else '' for i in text])

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
        if (new_string.lower() not in old_string.lower() and old_string.lower() not in new_string.lower()):
               if which_impact_label not in ['sentence(s)', 'article_title']:
                   final_number = old_string + ', ' + new_string
                   final_addendum = new_addendum
        else:
            final_number = old_string

    return str(final_number + ' ' + final_addendum).strip()

def save_in_dataframe(df_impact, location, date, label, number_or_text, addendum, sentence, title): 
    """
    Save impact data in dataframe, sum entries if necessary
    """

    final_index = (location, date)      

    # first, check if there's already an entry for that location, date and label
    # if so, sum new value to existing value
    if final_index in df_impact.index:
        if str(df_impact.loc[final_index, label]) != 'nan':
            new_value = sum_values(str(df_impact.loc[final_index, label]), number_or_text, addendum, label)
            df_impact.loc[final_index, label] = new_value
            new_sentence = sum_values(df_impact.loc[final_index, 'sentence(s)'], sentence, '', 'sentence(s)')
            new_title = sum_values(df_impact.loc[final_index, 'article_title'], title, '', 'title')
            df_impact.loc[final_index, ['sentence(s)', 'article_title']] = [new_sentence, new_title]
    # otherwise just save the new entry
    else:
        df_impact.loc[final_index, label] = str(number_or_text+' '+addendum).strip()
        df_impact.loc[final_index, ['sentence(s)', 'article_title']] = [sentence, title]


################################################################################

@plac.annotations(
    model=("Model to load (needs parser and NER)", "positional", None, str))
def main(model='en_core_web_sm'):
    
    # define country of interest
    country = 'Uganda'
    country_short = 'ug'
    
    # load location dictionary
    locations_dict = LoadLocations(locations_folder+'/'+country, country_short)
    
    # load NLP model
    nlp = spacy.load(model)
    print("Loaded model '%s'" % model)

    # load DataFrame with articles
    df = pd.read_csv(input_directory+'/articles_all_topical.csv', sep='|')
    # select only relevant ones
    df = df[df['topical']==True]
    df = df.drop_duplicates(['title','text'], keep=False)

    # convert all dates into datetime
    df['publish_date'] = df['publish_date'].apply(pd.to_datetime)
    print('got ', len(df), 'articles:')
    print(df['publish_date'].min().strftime('%Y-%m-%d'), ' -- ', df['publish_date'].max().strftime('%Y-%m-%d'))
    
    # define keywords
    type_people = pd.read_csv(locations_keywords+'/Victims.txt', header=None)[0].tolist()  
    type_infrastructure = pd.read_csv(locations_keywords+'/Infrastructures.txt', header=None)[0].tolist()
    donation = ['donate', 'give', 'contribut', 'present', 'gift', 'grant',
                'hand', 'waive']
    type_livelihood = ['crop', 'field', 'cattle', 'farm', 'wheat', 'livestock',
                       'acre', 'plantation', 'cow', 'sheep', 'pig', 'goat']
    type_people_multiple = ['household', 'family', 'families']
    type_people_death = ['casualties', 'victims', 'fatalities', 'dead',
                         'lives ', 'lives,', 'lives.', 'lives:', 'lives;',
                         'lives!', 'lives?', 'deaths', 'bodies']
    list_verb_death = ['die', 'dead', 'pass', 'perish', 'drown', 'expire',
                       'killed', 'fall'] 
    type_house = ['house', 'home', 'building', 'hut', 'bungalow', 'cottage',
                  'ranch', 'barn', 'tower']
    currency_short = local_currency_names_short + ['USD', 'US$', '$']
    currency_long = local_currency_names_long + ['dollar']

    # initialize output DatFrame
    df_impact = pd.DataFrame(index=pd.MultiIndex(levels=[[],[]],
                                                 codes=[[],[]],
                                                 names=[u'location',
                                                        u'date']),
                             columns=['damage_livelihood', 'damage_general',
                                      'people_affected', 'people_dead',
                                      'houses_affected', 'livelihood_affected',
                                      'infrastructures_affected',
                                      'infrastructures_mentioned',
                                      'sentence(s)', 'article_title'])

    # loop over articles
    for id_row in range(0, len(df)):

        TEXT = df.iloc[id_row]['text']
        title = df.iloc[id_row]['title']
        doc_with_title = title + '.\n' + TEXT
        
        publication_date = str(df.iloc[id_row]['publish_date'].date())

        doc_with_title = preprocess_text(doc_with_title, currency_short)
        doc = nlp(doc_with_title)

        # set location (most) mentioned in the document
        # discard documents with no locations
        location_document = ''
        locations_document = FindLocations(doc, locations_dict)
        # fix ambiguities: [Bongo West, Bongo] --> [Bongo-West, Bongo]
        loc2_old, loc1_old = '', ''
        for loc1 in locations_document:
            for loc2 in locations_document:
                if (loc1 in loc2 and loc1 != loc2):
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
            location_document = most_common(locations_document)
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
            locations_found = list(set(FindLocations(sentence, locations_dict)))
            # fix ambiguities: [Bongo West, Bongo] --> [Bongo-West, Bongo]
            loc2_old, loc1_old = '', ''
            for loc1 in locations_found:
                for loc2 in locations_found:
                    if (loc1 in loc2 and loc1 != loc2):
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
                locations_found_order = []
                positions = []
                for loc in locations_found:
                    positions.append(sentence_text.find(loc))
                locations_found_order = [x for _,x in sorted(zip(positions,locations_found))]
                # check if some locations are mentioned within a list (e.g. Paris, London and Rome)
                location_lists = check_list_locations(locations_found_order, sentence_text)
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

            # *****************************************************************
            # loop over numerical entities,
            # check if it's impact data and if so, add to dataframe
            
            for ent in filter(lambda w: (w.label_ == 'CARDINAL') | (w.label_ == 'MONEY'), sentence.as_doc().ents):
                
                # get entity text and clean it
                ent_text = re.sub('\n', '', ent.text).strip()
                if ent_text == '':
                    continue
                number = '' # number associated to entity
                addendum = '' # extra info (currency or object)
                impact_label = '' # label specifying the nature of the impact data

                money_bool, currency_found = is_money(ent_text, sentence, currency_short, currency_long)

                # check if it's monetary value
                if money_bool:
                    number, addendum = process_number_money(ent_text, sentence_text, sentence, currency_short, currency_long)
                    if addendum == '':
                        addendum = currency_found
                    try:
                        int(float(number))
                    except ValueError:
                        continue
                    if int(number)>=1E7 and addendum == 'USD':
                        print('WARNING: too many dollars:')
                        print(sentence_text)
                        continue
                    if int(number)>=1E11 and addendum == local_currency_code:
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
                        if any(type in sentence_text.lower() for type in type_livelihood):
                            # print('    proposing assignement: ', ent_text, ' in damage_livelihood')
                            impact_label = 'damage_livelihood'
                        else:
                            # print('    proposing assignement: ', ent_text, ' in damage_general')
                            impact_label = 'damage_general'

                # if it's not monetary value, look for object
                else:
                    # get the object, i.e. what the number refers to
                    object  = get_object(ent, sentence, TEXT)
                    number = process_number_words(ent_text)

                    if (object != '') & (number != ''):

                        if any(type_obj in object.lower() for type_obj in type_people_death):
                            impact_label = 'people_dead'
                        elif any(type_obj in object.lower() for type_obj in type_people):
                            # if it's "family" or similar, multiply by 4
                            if any(type_obj in object.lower() for type_obj in type_people_multiple):
                                number = str(int(round(float(number)*4)))
                            # determine if they are dead or not
                            is_dead = False
                            number_and_object = [tok for tok in ent]
                            for tok in sentence:
                                if tok.text == object:
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
                        elif any(type_obj in object.lower() for type_obj in type_house):
                            impact_label = 'houses_affected'
                        elif any(type_obj in object.lower() for type_obj in type_infrastructure):
                            impact_label = 'infrastructures_affected'
                            for type_obj in filter(lambda w: w in object.lower(), type_infrastructure):
                                addendum += type_obj
                        elif any(type_obj in object.lower() for type_obj in type_livelihood):
                            impact_label = 'livelihood_affected'
                            for type_obj in filter(lambda w: w in object.lower(), type_livelihood):
                                addendum += type_obj
                        else:
                            # nothing interesting, discarding
                            continue
                    else:
                        # object not found, discarding
                        continue
                    try:
                        # cut-off at 1M
                        if int(number) >= 1E6:
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
                    closest_entity = min(distances_locations_entities, key = lambda t: t[1])
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
                                      publication_date, impact_label,
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
                                      publication_date, impact_label,
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
                                      publication_date, 'infrastructures_mentioned',
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
                                      publication_date, 'infrastructures_mentioned',
                                      inf_text, '', sentence_text, title)
            # ******************************************************************
            
    print('found ', len(df_impact), ' entries')

    df_impact.dropna(how='all', inplace=True)

    print(df_impact.describe())
    print(df_impact.head())
    
    # create output dir if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    df_impact.to_csv(output_directory+'/impact_data.csv', mode='w', encoding='utf-8', sep='|')
    writer = ExcelWriter(output_directory+'/impact_data.xlsx')
    df_impact.to_excel(writer, 'Sheet1')
    writer.save()

if __name__ == '__main__':
    plac.call(main)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  1 10:31:11 2019

@author: jacopo
"""

from __future__ import unicode_literals, print_function

import plac
import spacy
from spacy import displacy
from spacy.symbols import nsubj, VERB
import pandas as pd
import re
import unicodedata
from word2number import w2n
import json
import math
import pandas as pd
import os

titles = ['Mr', 'Mrs', 'Ms', 'Miss', 'Senator', 'President', 'Minister', 'Councillor', 'Mayor', 'Governor', 'Secretary', 'Attorney', 'Chancellor', 'Judge', 'Don', 'Father', 'Dr', 'Doctor', 'Prof', 'Professor']

def FindLocations(target_text, locations):
    """Find locations of interest in a given text,
    after applying some preprocessing
    """

    target_text_edit = target_text
    # filter names with titles (Mr., Ms. ...)
    # important: some people have names of towns!
    for title in titles:
        target_text_edit = re.sub(title+'\.\s[A-Za-z]+\s[A-Z][a-z]+', '', target_text_edit)
        target_text_edit = re.sub(title+'\s[A-Za-z]+\s[A-Z][a-z]+', '', target_text_edit)
        target_text_edit = re.sub(title+'\.\s[A-Za-z]+', '', target_text_edit)
        target_text_edit = re.sub(title+'\s[A-Za-z]+', '', target_text_edit)

    # filter article signatures (ZambiaDailyMail)
    pattern_signatures_head = re.compile(r'[A-Z]+\s[A-Z]+\,\s[A-Za-z]+') # e.g. MONICA KAYOMBO, Ndola
    target_text_edit = re.sub(pattern_signatures_head, '', target_text_edit)
    pattern_signatures_foot = re.compile(r'[A-Z]+\s[A-Z]+\n\n[A-Za-z]+') # e.g. MONICA KAYOMBO \n\n Ndola
    target_text_edit = re.sub(pattern_signatures_foot, '', target_text_edit)

    # find locations
    locations_found = []
    locations_found_re = [re.search(re.compile(ward), target_text_edit) for ward in locations]
    locations_found = [word.group(0) for word in locations_found_re if word is not None]
    return locations_found

def normalize_caseless(text):
    return unicodedata.normalize("NFKD", text.casefold())

def preprocess_text(text):
    """Pre-process text
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

    # get onli ASCII characters, remove "\'"
    text = clean(text)

    return text

def process_number_money(text, sentence, currencies_short, currencies_long):

    currency = ''
    for currency_short in currencies_short:
        if currency_short in text.lower():
            currency = currency_short
            text = re.sub(re.compile(currency_short+'[\.]{0,1}', re.IGNORECASE), '', text)

    for currency_long in currencies_long:
        regex_currency = re.compile(currency_long, re.IGNORECASE)
        if re.search(regex_currency, sentence.text) is not None:
            for idx, word in enumerate(sentence):
                if word.text in text:
                    if (currency_long in sentence[idx+1].text or currency_long in sentence[idx+2].text):
                        currency = currency_long
                    if (currency_long in sentence[idx-1].text or currency_long in sentence[idx-2].text):
                        currency = currency_long
    if currency != '':
        if 'sh' in currency:
            currency = '‎KES'
        else:
            currency = 'USD'

    number = process_number_words(text)
    return (number, currency)

def process_number_words(text):
    """convert number words into numbers
    """

    # make lowercase, remove commas
    text = text.lower()
    text = re.sub('\n', '', text)
    text = re.sub(',', '', text)
    text = text.strip()
    # print('start process_number_words on ', text)

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

    # fucking word_to_num not working, need to convert string to number
    for (number, word) in re.findall('([0-9\.]+)\s([a-z]+)', text):
        number_old = number
        if 'billion' in word:
            number = str(int(float(number))*1000000000)
        if 'million' in word:
            number = str(int(float(number))*1000000)
        if 'thousand' in word:
            number = str(int(number)*1000)
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
    return text

def is_money(ent_text, sentence, currencies_short, currencies_long):
    """check if numerical entity is monetary value
    """
    if any(currency_short in ent_text.lower() for currency_short in currencies_short):
        return True

    for currency_long in currencies_long:
        regex_currency = re.compile(currency_long, re.IGNORECASE)
        if re.search(regex_currency, sentence.text) is not None:
            for idx, word in enumerate(sentence):
                if word.text in ent_text:
                    if (currency_long in sentence[idx+1].text or currency_long in sentence[idx+2].text):
                        return True
                        break
                    if (currency_long in sentence[idx-1].text or currency_long in sentence[idx-2].text):
                        return True
                        break

    return False

def get_object(ent, sentence, doc_text):
    """get what a given number refers to
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
    """check if locations are in a list (e.g. "Kalabo, Chibombo and Lundazi")
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

def sum_values(old_string, new_number, new_addendum, which_impact_label):

    final_number = ''
    final_addendum = ''

    print(which_impact_label)

    if (which_impact_label == 'damage_livelihood') or (which_impact_label == 'damage_general'):
        for (number, currency) in re.findall('([0-9\.]+)[\s]+(.+)', old_string):
            print(number, ' (', currency, ')')
            if  new_addendum in currency:
                final_number = str(int(number) + int(new_number))
                final_addendum = new_addendum
            else:
                print('different currencies, dont know how to sum !!!!')

    elif (which_impact_label == 'houses_affected') or (which_impact_label == 'people_affected') or (which_impact_label == 'people_dead'):
        final_number = str(int(old_string) + int(new_number))

    else:
        final_number = old_string + ', ' + new_number
        final_addendum = new_addendum

    print('substituting: ',  old_string, ' + ', new_number, ' ', new_addendum, ' --> ', final_number + ' ' + final_addendum)
    return str(final_number + ' ' + final_addendum)


################################################################################

@plac.annotations(
    model=("Model to load (needs parser and NER)", "positional", None, str))
def main(model='en_core_web_sm'):
    nlp = spacy.load('en_core_web_sm')
    print("Loaded model '%s'" % model)

    donation = ['donate', 'give', 'contribut', 'present', 'gift',
                'grant', 'hand', 'waive']
    type_livelihood = ['crop', 'field', 'cattle', 'farm', 'wheat', 'livestock',
                       'acre', 'plantation', 'cow', 'sheep', 'pig', 'goat']
    
    type_people = pd.read_csv('../Input/Victims.txt', header=None)[0].tolist()
    
    type_infrastructure = pd.read_csv('../Input/Infrastructures.txt', header=None)[0].tolist()
    
    type_people_multiple = ['household', 'family', 'families']
    type_people_death = ['casualties', 'victims', 'fatalities', 'dead',
                         'lives ', 'lives,', 'lives.', 'lives:', 'lives;',
                         'lives!', 'lives?', 'deaths', 'bodies']
    list_verb_death = ['die', 'pass', 'perish', 'drown', 'expire', 'killed', 'fall']   
    type_house = ['house', 'home']

    currency_short = ['ksh', 'sh', 'usd', '$']
    currency_long = ['shilling', 'dollar']

    # Import excel file with provinces and districts of Zambia as a DataFrame
    Zambia_provinces = pd.read_excel('../Input/Zambia Provincies en Districten.xlsx')
    Zambia_distr = pd.read_excel('../Input/Zambia Provincies en Districten.xlsx', 'All districts')
    # From this DataFrame, create list of provinces and districts in Zambia
    locations = Zambia_provinces['Total districts by Province'].tolist() + Zambia_distr['Districts'].tolist()
    # add 'Zambia' to locations, used if nothing else is found
    locations.append('Zambia')
    locations.append('North Western')

    # dataframe of impact data (output)
    df_impact = pd.DataFrame(columns=['location', 'date', 'damage_livelihood',
                                      'damage_general', 'people_affected',
                                      'people_dead', 'houses_affected',
                                      'livelihood_affected',
                                      'infrastructures_affected',
                                      'infrastructures_mentioned'])
    # directory of paragraphs
    directory = '../Output/Paragraph selection/'
    
    for filename in os.listdir(directory):
        paragraphs = pd.read_excel(os.path.join(directory, filename))
    
        for id_row in range(0, len(paragraphs)):
    
            paragraph = paragraphs.iloc[id_row]
    
            TEXT = paragraph['Paragraph text']
            publication_date = paragraph['Dates']
            TEXT = preprocess_text(TEXT)
            doc = nlp(TEXT)
            
    #        print('\n\nstarting paragraph *******************************************************************')
    #        print(TEXT)
    
            # set location (most) mentioned in the document
            # discard documents with no locations
            location_document = ''
            locations_document_all = FindLocations(TEXT, locations)
            locations_document_unique = list(set(locations_document_all))
            for loc in locations_document_unique:
                if any((loc in locs and loc != locs) for locs in locations_document_unique):
                    locations_document_unique.remove(loc)
            if len(locations_document_unique) == 1:
                # easy case, document mentions one location only
                location_document = locations_document_unique[0]
            elif len(locations_document_unique) > 1:
                # multiple locations mentioned, take the most common
                location_document = most_common(locations_document_all)
            else:
                # no location mentioned, just use Zambia
                location_document = 'Zambia'
    
            # loop over sentences
            for sentence in doc.sents:
                
                # remove newlines
                sentence_text = re.sub('\n', ' ', sentence.text)
    
                # get locations mentioned in the sentence
                location_final = ''
                location_lists = []
                locations_found = list(set(FindLocations(sentence_text, locations)))
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
                    # check if some locations are mentioned within a list
                    location_lists = check_list_locations(locations_found_order, sentence_text)
                    # add a list of locations, merging those that are within a list
                    locations_found_merged = locations_found_order.copy()
                    for loc in locations_found_order:
                        if any(loc in loc_list for loc_list, num, loc_sublist in location_lists):
                            locations_found_merged.remove(loc)
                    for loc in locations_found_merged:
                        location_lists.append((loc, 1, [loc]))
                else:
                    # no locations mentioned in the sentence, use the paragraph one
                    location_final = location_document
    
                # print(location_final, location_lists)
    
#                print('\nstarting sentence ******************************************')
#                print(sentence_text)
#                for token in sentence:
#                    print(token.text, token.dep_, token.ent_type_, token.pos_, token.head.text, token.head.pos_, [child for child in token.children])
    
                # ******************************************************************
                # loop over numerical entities,
                # check if it's impact data and if so, add to dataframe
                for ent in filter(lambda w: (w.label_ == 'CARDINAL') | (w.label_ == 'MONEY'), sentence.as_doc().ents):
                    ent_text = ent.text
                    number = '' # number associated to entity
                    addendum = '' # extra info (currency or object)
                    impact_label = '' # label specifying the nature of the impact data
    
                    # check if it's monetary value
                    if is_money(ent_text, sentence, currency_short, currency_long):
                        # print('--> money money money')
                        number, addendum = process_number_money(ent_text, sentence, currency_short, currency_long)
                        try:
                            int(float(number))
                        except ValueError:
                            continue
                        if int(number)>=1000000 and addendum == 'USD':
                            print('too many dollars:')
                            print(sentence_text)
                            print(location_final)
                        if int(number)>=100000000 and addendum == 'KES':
                            print('too many shillings:')
                            print(sentence_text)
                            print(location_final)
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
    
                    # otherwise look for object
                    else:
#                        print('--> other stuff')
                        # get what the number refers to
                        object  = get_object(ent, sentence, TEXT)
                        number = process_number_words(ent_text)
                        if object != '':
#                            print('    object: ', object)
                            if any(type_obj in object.lower() for type_obj in type_people_death):
                                # print('    proposing assignement: ', ent_text, ' in people_dead')
                                impact_label = 'people_dead'
                            if any(type_obj in object.lower() for type_obj in type_people):
                                if any(type_obj in object.lower() for type_obj in type_people_multiple):
                                    number = str(int(round(float(number)*4.4)))
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
                                    # print('    proposing assignement: ', ent_text, ' in people_dead')
                                    impact_label = 'people_dead'
                                else:
                                    # print('    proposing assignement: ', ent_text, ' in affected_people')
                                    impact_label = 'people_affected'
                            elif any(type_obj in object.lower() for type_obj in type_house):
                                # print('    proposing assignement: ', number, ' in affected_houses')
                                impact_label = 'houses_affected'
                            elif any(type_obj in object.lower() for type_obj in type_infrastructure):
                                # print('    proposing assignement: ', number, ' in affected_infrastructures')
                                impact_label = 'infrastructures_affected'
                                for type_obj in filter(lambda w: w in object.lower(), type_infrastructure):
                                    addendum += type_obj
                            elif any(type_obj in object.lower() for type_obj in type_livelihood):
                                # print('    proposing assignement: ', ent_text, ' in affected_livelihood')
                                impact_label = 'livelihood_affected'
                                for type_obj in filter(lambda w: w in object.lower(), type_livelihood):
                                    addendum += type_obj
                            else:
#                                print('    nothing interesting, discarding')
                                continue
                        else:
#                            print('    object not found, discarding')
                            continue
    
                    # safety check
                    if impact_label == '':
                        print('WARNING: impact_label NOT ASSIGNED !!!')
    
                    # assign location
                    location_impact_data = location_final
    
                    # if multiple locations (or lists of locations) are found
                    # check which is the closest one to the impact data
                    if location_final == 'TBI':
                        # compute distances between entity and locations, choose the closest one
                        distances_locations_entities = []
                        ent_text = ent_text.strip()
                        ent_text = re.sub('\n', '', ent_text)
                        for idx, (loc, num, loc_sublist) in enumerate(location_lists):
                            pattern_entity = re.compile(str('('+re.escape(loc)+'(.*)'+re.escape(ent_text)+'|'+re.escape(ent_text)+'(.*)'+re.escape(loc)+')'))
                            distances_locations_entities += [(loc, len(chunk[0])-len(loc)-len(ent_text), num, loc_sublist) for chunk in re.finditer(pattern_entity, sentence_text)]
                        closest_entity = min(distances_locations_entities, key = lambda t: t[1])
                        # print('entity: ', ent_text, ent.label_, ', location: ', [locations_found], ', closest: ', closest_location[0])
                        # if closest location is a list, location_impact_data will be a list of strings
                        # otherwise just a string
                        if closest_entity[2] > 1:
                            location_impact_data = closest_entity[3] # get list of locations in the list
                        else:
                            location_impact_data = closest_entity[0]
    
                    # save to dataframe
                    if type(location_impact_data) is str:
                        # one location, just append impact data to that one
                        df_impact.loc[len(df_impact), ['location', 'date', impact_label]] = [location_impact_data, publication_date, str(number+' '+addendum)] 
                    if type(location_impact_data) is list:
                        # multiple locations, divide impact data equally among them
                        number_divided = ''
                        try:
                            number_divided = str(int(int(number)/len(location_impact_data)))
                        except ValueError:
                            print('division failed: ', number)
                            number_divided = number
                        for location in location_impact_data:
                            df_impact.loc[len(df_impact), ['location', 'date', impact_label]] = [location, publication_date, str(number_divided+' '+addendum)]
    
#                    print(cnt, ' <-- ')
                # ******************************************************************
    
                # ******************************************************************
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
                            pattern_entity = re.compile(str('('+re.escape(loc)+'(.*)'+re.escape(inf_text)+'|'+re.escape(inf_text)+'(.*)'+re.escape(loc)+')'))
                            distances_locations_entities += [(loc, len(chunk[0])-len(loc)-len(inf_text), num, loc_sublist) for chunk in re.finditer(pattern_entity, sentence_text)]
                        closest_entity = min(distances_locations_entities, key = lambda t: t[1])
                        # if closest location is a list, location_impact_data will be a list of strings
                        # otherwise just a string
                        if closest_entity[2] > 1:
                            location_infrastructure = closest_entity[3] # get list of locations in the list
                        else:
                            location_infrastructure = closest_entity[0]
    
#                    save to dataframe
                    if type(location_infrastructure) is str:
                        # one location, just append impact data to that one
                        df_impact.loc[len(df_impact), ['location', 'date', 'infrastructures_mentioned']] = [location_infrastructure, publication_date, inf_text] 
                    if type(location_infrastructure) is list:
                        # multiple locations, assign infrastructure to all
                        for location in location_infrastructure:
                            df_impact.loc[len(df_impact), ['location', 'date', 'infrastructures_mentioned']] = [location, publication_date, inf_text]
                            
                # ******************************************************************

    print('******************************************************************')
    print('impact data extracion finished successfully')
    print('found', len(df_impact), 'sentences with impact data or infrastructures')

    df_impact.dropna(how='all', inplace=True)
#    print(df_impact.describe())
    print('entries with exact locations: ', len(df_impact[df_impact['location']!='Zambia']))
#    print(df_impact.head(500))

    df_impact.to_hdf('../Output/impact_data/impact_data_ZVAC.h5', key='df', mode='w')
    df_impact.to_csv('../Output/impact_data/impact_data_ZVAC.csv', mode='w', encoding='utf-8', sep='|')

if __name__ == '__main__':
    plac.call(main)
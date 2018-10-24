import nltk
from nltk.tokenize import word_tokenize, sent_tokenize, PunktSentenceTokenizer
from nltk.tag import pos_tag
from nltk.chunk.regexp import *
import pandas as pd
import re
import os
import pprint
import dateparser
import string
from nltk.corpus import wordnet
import pandas as pd
import datefinder
nltk.download('punkt')
nltk.download('wordnet')
import datetime as dt
import numpy as np
import time
import glob

# print(nltk.__file__)
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 250)
pd.set_option('display.max_colwidth', 75)
pd.options.display.float_format = '{:,.2f}'.format
np.set_printoptions(precision=2)


def find_occurrences_of_list_elements_in_string(search_list, s, ignore_case=True):
    """Suppose we have a list of strings, 'search_list'. We want to see where the items of 'search_list' occur in
    some text string s. For each occurrence, we want to know all occurrences of these items. This method performs this
    search, and returns the results."""
    #
    # INPUT:
    # - s:              str, text in which we want to search
    # - search_list:    list of str, elements which we want to find in the text/str.
    # - ignore_case:    bool, if True, we ignore upper/lower case in our search
    #
    # OUTPUT:
    # - found_items:    list of occurrences of words

    found_items = []

    if ignore_case:
        s = s.lower()

    # For each item in search_list
    for item in search_list:
        # Finds all occurrences of 'item' in 's', and returns a list of the corresponding indices where these
        # occurrences start. E.g. if item = 'Lusaka' and indices_item = [20, 40], it means 'Lusaka' occurs twice in s,
        # starting at the 20th and 40th character of s.
        if ignore_case:
            indices_item = [m.start() for m in re.finditer(item.lower(), s)]
        else:
            indices_item = [m.start() for m in re.finditer(item, s)]

        # Add each of the found occurrences to found_items
        for idx in indices_item:
            found_items.append(item)

    return found_items


def find_all_dates_in_string(s):
    """Finds all occurrences of dates in a given text string."""
    # This method tried to find all occurrences of date elements in a given string.
    # As a first step, we use the 'datefinder' module, which has a function 'find_dates' that
    # returns a list of locations where it guesses a date is referenced in a given input string. We use this function to
    # get an initial list of potential date references in the text (Step 1).
    #
    # However, this function is quite crude: many of its suggestions are not actually dates. Hence, we refine the list
    # of guesses by applying some additional selection rules to the output of 'find_dates' (Step 2).
    #
    # INPUT:
    # - s       str of text in which we want to find date elements
    #
    # OUTPUT:
    # result     pd.Series with index = start idx of date element, value = str that was identified as date element

    #######################################################################################################
    # STEP 1 Use datefinder.find_dates to get a list of "guesses" of where date references might occur
    #######################################################################################################
    # Returns 'list of sublist'. Each sublist represents one found date, and has the following elements:
    # - dt.datetime():      datetime that is estimated to be foound
    # - [list of str]:      list of str items, which together are marked as a single date reference by the function
    # - 2-tuple of int:     indicating the first and last index location where the date strings were found

    indices_dates = []
    matches = datefinder.find_dates(s, source=True, index=True)

    for match in matches:
        indices_dates.append(match)

    # Create pandas DataFrame 'df_dates', in which we will store the results. df_dates has the following columns:
    # - Date:               dt.datetime, actual date that is identified
    # - Token elements:   str, concatenation of all text elements that together tokened the datefinder to
    #                       identify a date element
    # - Index range:        2-tuple, (index_of_first_token_element, index_of_last_token_element)
    df_dates = pd.DataFrame(indices_dates, columns=['Date', "Token elements", "Index range"])

    #######################################################################################################
    # STEP 2 Filter the results from datefinder.find_dates using some additional selection rules.
    ######################################################################################################
    drop_idxs = []

    # First, we define some lists of elements that we expect (or do not expect) to be in a date.
    # For example, we expect ['01', '02', ..., '12'] might be in the date element as month references.

    years_long = [str(year) for year in np.arange(1990, dt.datetime.now().year + 1)]
    years_short_with_leading_0 = [str(year_short) for year_short in np.arange(1990, 2000)] + ['01', '02', '03', '04',
                                                                                              '05', '06', '07',
                                                                                              '08', '09', '10', '11',
                                                                                              '12']
    months_short_no_leading_0 = [str(month) for month in np.arange(1, 12)]

    days = [str(day) for day in np.arange(1, 32)]

    # All number items that we reasonably expect to occur in the "token elements". E.g. we never expect '44' or
    # '99123' to occur. Thus, we only include the observation if it is a "feasible" number.
    valid_numbers = years_long + years_short_with_leading_0 + months_short_no_leading_0 + days
    # days/months without leading 0 not necessary, because it's already part of years without leading 0

    for idx, row in df_dates.iterrows():
        s_curr = row["Token elements"]

        tokens_curr = word_tokenize(s_curr)
        # For example, s_curr could be "2007 08", then tokens_curr = ["2007", "08"].

        # The datefinder.find_dates() function includes some signal words (e.g. 't', 'of', 'on') in its results.
        # We exclude these words from the tokens, because they are not directly relevant.
        tokens_curr = [s for s in tokens_curr if not s.lower() == 't']
        tokens_curr = [s for s in tokens_curr if not s.lower() == 'of']
        tokens_curr = [s for s in tokens_curr if not s.lower() == 'and']
        tokens_curr = [s for s in tokens_curr if not s.lower() == 'to']
        tokens_curr = [s for s in tokens_curr if not s.lower() == 'time']
        tokens_curr = [s for s in tokens_curr if not s.lower() == 'on']

        # For each of the token elements, we check whether it is a numerical, and if yes, whether this number
        # is in the valid number set. (we include the comma "," as a symbol, to account for numbers like 2,000,000
        # which are also recognized by datefinder as dates).
        for token in tokens_curr:

            if re.match('^[\d\,]{1,}$', token) and not token in valid_numbers:
                drop_idxs.append(idx)

        # If there is NO year in the string, we exclude the observation as well. (i.e., we assume that
        # all date references in a text must have a year in them. This means that e.g. "21 September" is not recognized
        # as a valid date.)
        if not any(year in s_curr for year in years_long + years_short_with_leading_0):
            drop_idxs.append(idx)

        # If ALL token elements are digits and there are at least two tokens, then there should at least be "/" or "-"
        # in the elements as well. We assume digit combinations WITHOUT such punctuation marks cannot be dates.
        if all(token.isdigit() for token in tokens_curr) \
                and not ('/' in s_curr or '-' in s_curr) \
                and len(tokens_curr) > 1:
            drop_idxs.append(idx)

        # If there is only one token, AND it is a digit BUT it is NOT a long year(2007, 2008, etc.) then we assume it is
        # not a date.
        if len(tokens_curr) == 1 and tokens_curr[0].isdigit() and not tokens_curr[0] in years_long:
            drop_idxs.append(idx)

    # Now, actually apply the selection filters (i.e. drop date if it doesn't satisfy the filter).
    drop_idxs = list(set(drop_idxs))
    df_dates.drop(drop_idxs, inplace=True)
    df_dates['Start index'] = -1

    # Now, for each found date, we gather the corresponding "neighborhood" of text in the document and we assign it to df_dates
    for idx, row in df_dates.iterrows():
        df_dates.loc[idx, "Start index"] = row['Index range'][0]

    result = pd.Series(index=df_dates["Start index"], data=df_dates["Token elements"].values)

    return result


def write_to_excel_with_invalid_char_catch(df, path):
    """Writes pd.DataFrame to Excel file, including a try-catch loop to deal with invalid character issues"""
    #
    # Sometimes, when directly trying df.to_excel(path), we get an error because df contains invalid characters
    # (specifically, characters that are not unicode). In this method, we use a try-catch loop to deal with this error.
    #
    # INPUT:
    # - df:     pd.DataFrame, which we want to write to Excel
    # - path:   str, indicating to which path we want to write the file (relative to this Python script's current dir.)
    #           path should include .xlsx as suffix.

    try:
        df.to_excel(path)
    except:
        df= df.applymap(lambda x: x.encode('unicode_escape').
                                         decode('utf-8') if isinstance(x, str) else x)
        df.to_excel(path)


########################################################################################################################
### Structure
########################################################################################################################
# This code takes a text document (a PDF document that is scraped and stored as .txt) as its input. It then identifies
# the paragraphs in this document. For each paragraph, it identifies geographic location references (as given in an
# Excel-file), disaster references (as given in a disaster.txt file) and date references.
#
# It does this in the following steps:
# - Step 1:  import document, and apply some cleaning steps
# - Step 2:  import lists of potential locations, disasters
# - Step 3:  determine the page on which each paragraph starts
# - Step 4:  for each paragraph, find the locations, disasters and dates.
# - Step 5:  filter the paragraphs in which at least 2 of the 3 elements (location, disaster, date) occur and store
#            results


########################################################################################################################
### Step 1: import document, and apply some cleaning steps
########################################################################################################################
#Import text file and convert it to proper nltk environment

#f = open('C:/Users/s110768/Documents/Pipple/KlantenPipple - Rode Kruis/201806 Data Challenge #1/03. Work/Input/Text_Reports/2009 In-depth Action Plan.pdf.txt', 'r')
# Loop over not just 1 txt file, but folder containing txt files
txt_files = 'C:/Users/s110768/Documents/Pipple/KlantenPipple - Rode Kruis/201806 Data Challenge #1/03. Work/Input/Text_Reports' #map containing txt files
read_files = glob.glob(os.path.join(os.getcwd(), txt_files, "*.txt")) #list with all the txt files
data_files = [] #empty list

#Now define a loop where every txt file is fully read
for file_path in read_files:
    with open(file_path, encoding='utf8') as f_input:
        data_files.append(f_input.read())

#Create a list with names of the different txt files, is to save the Excel files later on
names = []
for y in range(0,len(read_files)):
    z = read_files[y]
    names.append(z[106:])

#For every entirly read file, loop over entire code to grasp all the relevant information
for i in range(len(data_files)):
    x = data_files[i]
    # Table of contents and tables contain a LOT of dots ('......'). If two or more dots occur after each other, we conclude
    # that it is not a dot that marks the end of a sentence. Therefore, we consider these dots useless and remove them.
    raw = re.sub('\.{2,}', '', x)

    # Sometimes, multiple enters (linebreaks) occur after each other, but there are also some spaces in between.
    # We remove these spaces.
    raw = re.sub('\n +', '\n', raw)



    # A "normal" enter (i.e. start of new sentence WITHIN a paragraph) is marked by "\n\n". Otherwise (e.g. end of paragraph),
    # we have three or more times "\n".
    raw = re.sub('\n\n', '\n', raw)
    raw = re.sub('[\n]{3,}', '\n\n', raw)
    # As a result, we know that, where there used to be "\n\n" (normal enter for end of line WITHIN paragraph), there is now
    # an "\n", and # where there was "\n\n\n" (or more), there is now an "\n\n". This will help us later to identify the
    # paragraph breaks.



    # We remove some common whitespace characters and replace them by simple spaces.
    raw = re.sub('[ \t\r\v]+', ' ', raw)



    ########################################################################################################################
    ### Step 2: import lists of potential locations, disasters, victims
    ########################################################################################################################
    # Import excel file with provinces and districts of Zambia as a DataFrame
    Zambia_provinces = pd.read_excel('C:/Users/s110768/Documents/Pipple/KlantenPipple - Rode Kruis/201806 Data Challenge #1/03. Work/Input/Zambia Provincies en Districten.xlsx')
    Zambia_distr = pd.read_excel('C:/Users/s110768/Documents/Pipple/KlantenPipple - Rode Kruis/201806 Data Challenge #1/03. Work/Input/Zambia Provincies en Districten.xlsx', 'All districts')

    # From this DataFrame, create list of districts in Zambia
    locations = Zambia_distr['Districts'].tolist()

    disaster_words = pd.read_csv('C:/Users/s110768/Documents/Pipple/KlantenPipple - Rode Kruis/201806 Data Challenge #1/03. Work/Input/Disaster.txt', header=None)[0].tolist()

    victims_words = pd.read_csv('C:/Users/s110768/Documents/Pipple/KlantenPipple - Rode Kruis/201806 Data Challenge #1/03. Work/Input/Victims.txt', header=None)[0].tolist()


    ########################################################################################################################
    # Step 2: determine the paragraphs of the document
    ########################################################################################################################
    paragraph_split_identifier = '\n\n'
    paragraphs = pd.DataFrame(data=re.split(paragraph_split_identifier, raw), columns=['Paragraph text'])

    # Store the starting and ending character idx of where the paragraph starts/ends.
    paragraphs['Start index'] = [0] + [m.start() for m in re.finditer(paragraph_split_identifier, raw)]

    ########################################################################################################################
    # Step 3: determine the page on which each paragraph starts
    ########################################################################################################################
    # In the documents that we investigated, we found that the unicode character '\xoc' (up arrow) indicates the transition
    # from main body to footer (and possibly also from header to main body, or from footer to header).
    print("Warning: page number calculation only works if the document has NO headers, only footers.")

    # First, identify the index of all page breaks (characterized by an 'up arrow' sign, which has unicode \xoc)
    page_break_idxs = []
    for match in re.finditer('\x0c', raw):
        page_break_idxs.append(match.start())

    # Create a separate page_starts and page_ends based on the page_breaks
    page_start_idxs = [0] + page_break_idxs
    page_end_idxs = page_break_idxs + [len(raw)]

    # Initialize as not found
    paragraphs['Page nr'] = -1

    # Iteratively go through all pages, and assign the paragraphs accordingly
    for page_nr, (page_start, page_end) in enumerate(zip(page_start_idxs, page_end_idxs)):
        # True for rows in the current page, else False
        page_mask = (paragraphs['Start index'] >= page_start) & (paragraphs['Start index'] < page_end)

        paragraphs.loc[page_mask, 'Page nr'] = page_nr + 1  # +1 because python starts counting at 0

    # For some reason, if the paragraph is at the top of the page, it underestimates th epage number by 1.
    for idx, row in paragraphs.iterrows():
        if '\f' in row['Paragraph text']:
            paragraphs.loc[idx, 'Page nr'] += 1



    ########################################################################################################################
    # Step 4: for each paragraph, find the locations, disasters, dates and victims.
    ########################################################################################################################
    # Now, for each paragraph, we search for the locations, disasters and dates that occur in the paragraph text.
    # We add the results as a new column to the 'paragraphs' DataFrame.

    for idx, row in paragraphs.iterrows():


        start = time.time()
        # Find all location occurrences
        locations_paragraph = find_occurrences_of_list_elements_in_string(search_list=locations, s=row['Paragraph text'])
        paragraphs.loc[idx, 'Locations'] = ', '.join(locations_paragraph)

        # Find all disaster occurrences
        disasters_paragraph = find_occurrences_of_list_elements_in_string(search_list=disaster_words,
                                                                          s=row['Paragraph text'])
        paragraphs.loc[idx, 'Disasters'] = ', '.join(disasters_paragraph)

        # Find all date occurrences
        dates_paragraph = find_all_dates_in_string(s=row['Paragraph text'])
        paragraphs.loc[idx, 'Dates'] = ', '.join(dates_paragraph)

        # Find all victims
        victims_paragraph = find_occurrences_of_list_elements_in_string(search_list=victims_words, s=row['Paragraph text'])
        paragraphs.loc[idx, 'Victims'] = ', '.join(victims_paragraph)

    #write_to_excel_with_invalid_char_catch(paragraphs, 'C:/Users/s110768/Documents/Pipple/KlantenPipple - Rode Kruis/201806 Data Challenge #1/03. Work/Output/paragraphs_all.xlsx')
    paragraphs.to_excel('C:/Users/s110768/Documents/Pipple/KlantenPipple - Rode Kruis/201806 Data Challenge #1/03. Work/Output/All paragraphs/paragraphs_all_of_{}.xlsx'.format(names[i]))

    #################################################################################################################################
    # Step 5: filter the paragraphs in which at least 3 of the 4 elements (location, disaster, date, victims) occur and store results
    #################################################################################################################################
    for idx, row in paragraphs.iterrows():

        bool1 = len(row['Locations']) > 0
        bool2 = len(row['Disasters']) > 0
        bool3 = len(row['Dates']) > 0
        bool4 = len(row['Victims']) > 0

        if bool1 + bool2 + bool3 + bool4 < 3:
            paragraphs.drop(idx, inplace=True)

    print(paragraphs.head(25))
    paragraphs.to_excel(
        'C:/Users/s110768/Documents/Pipple/KlantenPipple - Rode Kruis/201806 Data Challenge #1/03. Work/Output/Paragraph selection/paragraphs_selection_of_{}.xlsx'.format(names[i]))
    #write_to_excel_with_invalid_char_catch(paragraphs, 'C:/Users/s110768/Documents/Pipple/KlantenPipple - Rode Kruis/201806 Data Challenge #1/03. Work/Output/paragraphs_selection.xlsx')
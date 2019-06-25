# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 13:10:34 2019

@author: LuisaB
"""

import os

from docx.api import Document

#Code for reading in the table from here: https://stackoverflow.com/questions/27861732/parsing-of-table-from-docx-file
    
#Function for turning table into dictionary

def tab_to_dic(table_number):
    keys = None
    list_rows_or_cols = []
    for i, row in enumerate(table_number.rows):
        text = (cell.text for cell in row.cells)
        
        # Establish the mapping based on the first row
        # headers; these will become the keys of the dictionary
        if i == 0:
            keys = tuple(text)
            continue
    
        # Construct a dictionary for this row, mapping keys to values for this row
        row_data = dict(zip(keys, text))
        #Convert dic values and keys to lowercase
        row_data = dict((k.lower(), v.lower()) for k, v in row_data.items())
        if "types of hazard" in row_data or "capacities" in row_data:
            print(row_data)
            list_rows_or_cols.append(row_data)
    if "types of disaster" in row_data or "type of\ndisaster" in row_data:
        keys = None
        for i, row in enumerate(table_number.columns):
            text = (cell.text for cell in row.cells)
        
            # Establish the mapping based on the first row
            # headers; these will become the keys of our dictionary
            if i == 0:
                keys = tuple(text)
                continue
        
            # Construct a dictionary for this row, mapping keys to values for this row
            new_data = dict(zip(keys, text))
            new_data = dict((k.lower(), v.lower()) for k, v in new_data.items())
            print(new_data)
            list_rows_or_cols.append(new_data)
    return list_rows_or_cols


#Loop over all the files.
directory = os.chdir(#path to folder with files)
documents = os.listdir(os.getcwd())
table_dir = #path to new directory

for i in documents:
    path = os.getcwd() + '\\' + i
    print(path)
    
    document = Document(path)
    tables = document.tables
    
    tab_as_dic = []
    if tables is not None:
        tab_as_dic = [tab_to_dic(t) for t in tables]
    print(tab_as_dic)
    
    new_filename = table_dir + '\\' + i + '.txt'
    os.makedirs(os.path.dirname(new_filename), exist_ok=True)
    with open(new_filename, "w", encoding='utf-8') as f:
        for table in tab_as_dic:
            for row in table:
                f.write("{}\n".format(row))
            f.write("\n")



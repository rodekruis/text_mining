# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pandas as pd


input_path = 'C:/Users/ErlijnLinskens/Pipple/KlantenPipple - Documents/Rode Kruis/Overige werkzaamheden/20180514 Impact Based Finance Text Mining/Spelling Mistake Fixer/Received files/'
filename = "EocDesinventar_master_new.xls"
filepath = input_path+filename

# read input data
impact = pd.read_excel(filepath)


# change column names, such that no '.' are used. 
old_cols = impact.columns.values
cols = [x.replace('.','_') for x in old_cols]
impact.columns = cols


# clean Houses_Destroyed 
impact.loc[336,'Houses_Destroyed'] = 1440 #both values 1440 and 69 present in this cell
impact['Houses_Destroyed'] = pd.to_numeric(impact['Houses_Destroyed'])


output_path = 'C:/Users/ErlijnLinskens/Pipple/KlantenPipple - Documents/Rode Kruis/Overige werkzaamheden/20180514 Impact Based Finance Text Mining/Spelling Mistake Fixer/Data/'
output_name = 'impact_data.pickle'
impact.to_pickle(output_path+output_name)

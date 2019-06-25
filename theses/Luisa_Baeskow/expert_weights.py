# -*- coding: utf-8 -*-
"""
Created on Sat Jun  1 22:37:37 2019

@author: LuisaB
"""


import pandas as pd

expert_count = pd.read_excel(#path to excel file)

expert_count_copy = expert_count

#Renaming the column
expert_count_copy = expert_count_copy.rename(columns={ expert_count_copy.columns[0]: "expert count" })




#Changing the numbers into weights

expert_count_copy.loc[expert_count_copy['expert count'] == 5, 'expert count scaled'] = 1

expert_count_copy.loc[expert_count_copy['expert count'] == 4, 'expert count scaled'] = 0.8

expert_count_copy.loc[expert_count_copy['expert count'] == 3, 'expert count scaled'] = 0.6

expert_count_copy.loc[expert_count_copy['expert count'] == 2, 'expert count scaled'] = 0.4

expert_count_copy.loc[expert_count_copy['expert count'] == 1, 'expert count scaled'] = 0.2

expert_count_copy.loc[expert_count_copy['expert count'] == 0, 'expert count scaled'] = 0

#Turning the rows into columns
expert_count_copy = expert_count_copy.transpose()

#Droping the orginal numbers
expert_count_copy = expert_count_copy.drop("expert count", axis=0)

#Reading in the csv file with all wordcounts
all_wordcounts = pd.read_csv(#path to file)

#Dropping dublicate columns
all_wordcounts = all_wordcounts.drop("damage_y", axis=1)
all_wordcounts = all_wordcounts.drop("wind_y", axis=1)

#Renaming
all_wordcounts.rename(columns={'damage_x':'damage'}, inplace=True)
all_wordcounts.rename(columns={'wind_x':'wind'}, inplace=True)
expert_count_copy.rename(columns={'damage_x':'damage'}, inplace=True)
expert_count_copy.rename(columns={'wind_x':'wind'}, inplace=True)

#Multiplying the values

all_wordcounts_new = all_wordcounts   
 
for column_name in expert_count_copy.columns:
    all_wordcounts_new[column_name] = all_wordcounts_new[column_name]*expert_count_copy[column_name][0]
    
#Save new counts as csv
all_wordcounts_new.to_csv(#path including new file name)
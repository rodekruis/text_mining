# -*- coding: utf-8 -*-
"""
Created on Tue May 14 14:56:01 2019

@author: ErlijnLinskens
"""

import pandas as pd
import numpy as np
import re
from fuzzywuzzy import process
from fuzzywuzzy import fuzz

path = 'C:/Users/ErlijnLinskens/Pipple/KlantenPipple - Documents/Rode Kruis/Overige werkzaamheden/20180514 Impact Based Finance Text Mining/Spelling Mistake Fixer/'
path_data = path + 'Data/'
input_name = 'impact_data.pickle'

impact_data = pd.read_pickle(path_data+input_name)


# official county/subcounty/ward data
path_received = path + 'Received/'
borders_list_nm = 'kenya_borders_list.csv'
borders = pd.read_csv(path_received+borders_list_nm,sep=';')
county_list = borders['County'].dropna()
subcounty_list = borders['Subcounty'].dropna()
ward_list = borders['Ward'].dropna()

data = impact_data[['Location', 'Comments']]
data['county_match'] = None
data['subcounty_match'] = None
data['ward_match'] = None


#%% part 1: approximate location matching
    

for i in range(len(data.Location)):
    loc = data.Location[i]
    comm = data.Comments[i]
    strsearch = " ".join([loc,str(np.where(pd.isna(comm),'',comm))]) #if nan then remove
    print(strsearch)
    ratio_ward = process.extract(strsearch,ward_list, scorer=fuzz.token_set_ratio)
    ratio_subcounty = process.extract(strsearch,subcounty_list, scorer=fuzz.token_set_ratio)
    ratio_county = process.extract(strsearch,county_list, scorer = fuzz.token_set_ratio)
    new_county = []
    new_sub = []
    new_ward = []
    for l,v,x in ratio_county: 
        if v > 95:
            new_county.append(l) 
            print('County:' + l)
    for l,v,x in ratio_subcounty: 
        if v > 95:
            new_sub.append(l)
            print('Subcounty' + l)
    for l,v,x in ratio_ward: 
        if v > 95:
            new_ward.append(l)
            print('Ward' + l)
            
    if len(new_county) > 0:
        data.loc[i,'county_match'] = new_county
    if len(new_sub) > 0:
        data.loc[i,'subcounty_match'] = new_sub
    if len(new_ward) > 0:
        data.loc[i,'ward_match'] = new_ward
        
    
print(ratio_ward)
print(ratio_subcounty)
print(ratio_county)

#%% part two:fill and expand county data

# check county data
counties_used = list(set(impact_data.County))
counties_used.remove('None')
not_in_list = [c in county_list for c in counties_used]
print('Number of counties used not in list: '+ str(sum(not_in_list)))

impact_data['county_match'] = data['county_match']
impact_data['subcounty_match'] = data['subcounty_match']
impact_data['ward_match'] = data['ward_match']

numeric_values = ['Deaths', 'Injured',
       'Missing', 'Houses_Destroyed', 'Evacuated', 'Houses_Damaged',
       'Directly_affected', 'Indirectly_Affected', 'Relocated',
       'Losses__Local', 'Education_centers', 'Damages_in_crops_Ha_',
       'Lost_Cattle', 'Lost_Goats', 'Lost_Livestock']

# fill all numeric values which are NAN to 0:
impact_data[numeric_values]=impact_data[numeric_values].fillna(0)

'''
The next part will check for matches in the data. If matches occur, the matches will be added 
to a dataframe 'new_rows' as separate rows with the source impact data divided by number of matches.
This new dataframe will be added to the impact data. The loop will not cover that part,
as the indices will fall out of the range provided at the beginning of the loop. 

The source data should be removed in the end, as they are transformed. This should happen at the end,
because otherwise the indices do not longer correspond within the loop. 

'''

data_ext = impact_data.copy()
data_ext['county_match2'] = np.where(data_ext.county_match.isna() == False,data_ext.county_match,'')
data_ext['length'] = data_ext.county_match2.apply(lambda x: len(x))

to_remove = [] #list of indices which should be removed after matched rows are added
for i in range(np.size(data_ext,0)):
    county = data_ext.loc[i,'County']
    match = data_ext.loc[i,'county_match']
    if type(match) == list:
        if county != 'None':
            match.append(county)
        matching_counties = list(set(match)) #removes duplicates
        # if only one matching county, then adjust row inplace
        if len(matching_counties) == 1:
            data_ext.loc[i,'County'] = matching_counties[0]
        else:
            row = data_ext.loc[i]
            for cn in matching_counties:
                row.County = cn
                row[numeric_values] = data_ext.loc[i,numeric_values] / len(matching_counties)
                data_ext.loc[np.size(data_ext,0)] = row
            to_remove.append(i)
            

#%% output
path_output = path + 'Output/'
output_name = 'matched.pickle'

pd.to_pickle(data,path_output+output_name)

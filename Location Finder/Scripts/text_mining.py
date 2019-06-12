# -*- coding: utf-8 -*-
"""
Created on Tue May 14 14:56:01 2019

@author: ErlijnLinskens & JacopoMargutti
"""

import pandas as pd
import numpy as np
import re
from fuzzywuzzy import process
from fuzzywuzzy import fuzz
import os
import math

path = re.sub('Scripts', '', os.getcwd()) + '/'
path_data = path + 'Data/'
path_output = path + 'Output/'
input_name = 'impact_data.pickle'

impact_data = pd.read_pickle(path_data+input_name)

# drop existing matches
impact_data.drop(columns=['County_comments', 'Subcounty_comments', 'Wards_comments'],
                 inplace=True)

# official county/subcounty/ward data
path_received = path + 'Received/'
#borders_list_nm = 'kenya_borders_list.csv'
#borders = pd.read_csv(path_received+borders_list_nm,sep=';')
#county_list = borders['County'].dropna()
#subcounty_list = borders['Subcounty'].dropna()
#ward_list = borders['Ward'].dropna()

admin_names = pd.read_csv(path_data+'Pcode_template_KEN.csv', delimiter=';', encoding='utf-8')
county_list = admin_names['name_level1'].dropna().drop_duplicates()
subcounty_list = admin_names['name_level2'].dropna().drop_duplicates()
ward_list = admin_names['name_level3'].dropna().drop_duplicates()

data = impact_data[['Location', 'Comments']]

#%% part 1: approximate location matching

for field in ['Location', 'Comments']:
    
    data[field+'_county_match'] = None
    data[field+'_subcounty_match'] = None
    data[field+'_ward_match'] = None
    
    for i in range(len(data[field])):
        
        strsearch = data[field][i]
        
        # skip nan values
        try:
            str_to_float = float(strsearch)
            if math.isnan(str_to_float):
                continue
        except:
            pass
        
        ratio_ward = process.extract(strsearch, ward_list, scorer=fuzz.token_set_ratio)
        ratio_subcounty = process.extract(strsearch, subcounty_list, scorer=fuzz.token_set_ratio)
        ratio_county = process.extract(strsearch, county_list, scorer = fuzz.token_set_ratio)
        new_county = []
        new_sub = []
        new_ward = []
        for l,v,x in ratio_county: 
            if v > 95:
                new_county.append(l) 
                print('County: ' + l)
        for l,v,x in ratio_subcounty: 
            if v > 95:
                new_sub.append(l)
                print('Subcounty: ' + l)
        for l,v,x in ratio_ward: 
            if v > 95:
                new_ward.append(l)
                print('Ward: ' + l)
                
        if len(new_county) > 0:
            data.loc[i,field+'_county_match'] = new_county
        if len(new_sub) > 0:
            data.loc[i,field+'_subcounty_match'] = new_sub
        if len(new_ward) > 0:
            data.loc[i,field+'_ward_match'] = new_ward
        
print(ratio_ward)
print(ratio_subcounty)
print(ratio_county)

#%% part two:fill and expand county data

# check county data
counties_used = list(set(impact_data.County))
counties_used.remove('None')
not_in_list = [c in county_list for c in counties_used]
print('Number of counties used not in list: '+ str(sum(not_in_list)))

# check if hierarchy is correct, otherwise discard
data_filtered = data.copy()
data_county = impact_data[['County']]
data_county['County'] = data_county['County'].apply(lambda x: np.nan if x=='None' else x)

for field in ['Location', 'Comments']:
    
    data_filtered[field+'_county_filtered'] = None
    data_filtered[field+'_subcounty_filtered'] = None
    data_filtered[field+'_ward_filtered'] = None
    
    for i in range(len(data_filtered)):
        
        row = data_filtered.iloc[i]
        row_county = data_county.iloc[i]
        
        # first, fix county
        county_final = []
        if not pd.isna(row_county['County']):
            county_final = [row_county['County']]
        else:
            if not np.all(pd.isna(row[field+'_county_match'])):
                county_final = row[field+'_county_match']
        
        # second, fix subcounty
        subcounty_final = []
        
        if not np.all(pd.isna(row[field+'_subcounty_match'])):
                
            # filter subcounties that belong to county_final, if county_fanal is present
            if not np.all(pd.isna(county_final)):
                
                # get list of valid subcounties
                valid_subcounties = list(set(admin_names[admin_names['name_level1'].isin(county_final)]['name_level2'].values.tolist()))    
            
                for subcounty in row[field+'_subcounty_match']:
                    if subcounty in valid_subcounties:
                        subcounty_final.append(subcounty) 
        
        # third, fix ward
        ward_final = []
        
        if not np.all(pd.isna(row[field+'_ward_match'])):
            
            # filter wards that belong to subcounty_final, if subcounty_final is present
            if not np.all(pd.isna(subcounty_final)):
     
                # get list of valid wards
                valid_wards = list(set(admin_names[(admin_names['name_level2'].isin(subcounty_final))]['name_level3'].values.tolist()))  
                 
                for ward in row[field+'_ward_match']:
                    if ward in valid_wards:
                        ward_final.append(ward)
                            
            # if not, filter wards that belong to county_final, if county_fanal is present       
            elif not np.all(pd.isna(county_final)):
                
                # get list of valid wards
                valid_wards = list(set(admin_names[admin_names['name_level1'].isin(county_final)]['name_level3'].values.tolist()))    
            
                for ward in row[field+'_ward_match']:
                    if ward in valid_wards:
                        ward_final.append(ward)
            
        # copy back to original dataframe
        if len(county_final) > 0:
            data_filtered.loc[i,field+'_county_filtered'] = county_final
        if len(subcounty_final) > 0:
            data_filtered.loc[i,field+'_subcounty_filtered'] = subcounty_final
        if len(ward_final) > 0:
            data_filtered.loc[i,field+'_ward_filtered'] = ward_final

# add matches to original dataframe
for field in ['Location', 'Comments']:
    for type_field in ['match', 'filtered']:
        impact_data[field+'_county_'+type_field] = data_filtered[field+'_county_'+type_field].apply(lambda x: ",".join(list(set(x))) if np.all(pd.notnull(x)) else x)
        impact_data[field+'_subcounty_'+type_field] = data_filtered[field+'_subcounty_'+type_field].apply(lambda x: ",".join(list(set(x))) if np.all(pd.notnull(x)) else x)
        impact_data[field+'_ward_'+type_field] = data_filtered[field+'_ward_'+type_field].apply(lambda x: ",".join(list(set(x))) if np.all(pd.notnull(x)) else x)

numeric_values = ['Deaths', 'Injured',
       'Missing', 'Houses_Destroyed', 'Evacuated', 'Houses_Damaged',
       'Directly_affected', 'Indirectly_Affected', 'Relocated',
       'Losses__Local', 'Education_centers', 'Damages_in_crops_Ha_',
       'Lost_Cattle', 'Lost_Goats', 'Lost_Livestock']

# fill all numeric values which are NAN to 0:
impact_data[numeric_values]=impact_data[numeric_values].fillna(0)

# save impact data in xls
impact_data.to_excel(path_output+'EcoDesinventar_master_natched.xls')

'''
The next part will check for matches in the data. If matches occur, the matches will be added 
to a dataframe 'new_rows' as separate rows with the source impact data divided by number of matches.
This new dataframe will be added to the impact data. The loop will not cover that part,
as the indices will fall out of the range provided at the beginning of the loop. 

The source data should be removed in the end, as they are transformed. This should happen at the end,
because otherwise the indices do not longer correspond within the loop. 

'''

#data_ext = impact_data.copy()
#data_ext['county_match2'] = np.where(data_ext.county_match.isna() == False,data_ext.county_match,'')
#data_ext['length'] = data_ext.county_match2.apply(lambda x: len(x))
#
#to_remove = [] #list of indices which should be removed after matched rows are added
#for i in range(np.size(data_ext,0)):
#    county = data_ext.loc[i,'County']
#    match = data_ext.loc[i,'county_match']
#    if type(match) == list:
#        if county != 'None':
#            match.append(county)
#        matching_counties = list(set(match)) #removes duplicates
#        # if only one matching county, then adjust row inplace
#        if len(matching_counties) == 1:
#            data_ext.loc[i,'County'] = matching_counties[0]
#        else:
#            row = data_ext.loc[i]
#            for cn in matching_counties:
#                row.County = cn
#                row[numeric_values] = data_ext.loc[i,numeric_values] / len(matching_counties)
#                data_ext.loc[np.size(data_ext,0)] = row
#            to_remove.append(i)
#            
#
##%% output
#output_name = 'matched.pickle'
#
#pd.to_pickle(data,path_output+output_name)

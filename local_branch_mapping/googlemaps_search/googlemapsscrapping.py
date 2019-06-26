# -*- coding: utf-8 -*-
"""
Created on Wed May 22 11:49:32 2019

@author: AnnaP
"""

import numpy as np
import pandas as pd
import math
import geopy
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time
import googlemaps

import os
path="D:/AnnaP/Documents/Red cross - text mining/google maps scrapping"
os.chdir(path)

gmaps = googlemaps.Client(key='AIzaSyANzA_Tm91rRCo9O-dTTE3OLQS9tswA_ic')

# read all the data that is used for determining the language and translations

# file with coordinates of extreme points of each country
extreme_points = pd.read_csv('extreme_points.csv', header = 0)
extreme_points['country'] = [country.lstrip() for country in extreme_points['country']]

# file with 2 most used languages for each country
languages = pd.read_csv('languages.csv', header = 0)
translations = pd.read_csv('translations.csv', header = 0)

# list of the most popular languages in internet and translation of red cross
# and red crescent to these languages
# we only search in these languages
popular_languages = translations['language'].tolist()

#dictionary with codes for each country
codes = pd.read_csv('codes.csv', header = 0)
codes['Code'] = codes['Code'].str.lower()

# file needed to identify in which countries we search for red crescent
religions = pd.read_csv('religions.csv')
muslim_countries = religions[religions['type']=='red_crescent']['country'].tolist()
muslim_countries = [country.lstrip() for country in muslim_countries]


## in geoloc_dict we save points for which the country is already identified 
## we do that to deacrease the number of requests to geopy and computation time
geoloc_dict = pd.DataFrame(columns = ['latitude', 'longitude', 'country'])
SPENT = 0.00   ## here we will save the costs


def long_step(latitude):
    ## computes step in longitude so that the step in longitude and latitude is the same in meters
    return round(STEP/math.cos(math.radians(latitude)),  2)

def which_country(latitude, longitude):
    ## finds a country given latitude and longitude
    global geoloc_dict
    geolocator = Nominatim(user_agent="my_app")
    place = geolocator.reverse((str(latitude)+', '+str(longitude)), timeout = 300).raw ## returns a nearby address for a point
    country = 'Unknown'
    if not 'error' in place:
        if 'country_code' in place['address']:
            country_code = place['address']['country_code'] 
            country = codes[codes['Code']==country_code]['Name'].values[0]  # uses codes distionary to find full country name
    geoloc_dict = geoloc_dict.append({'latitude':latitude, 'longitude': longitude, 'country':country}, ignore_index = True)
    time.sleep(1) # geopy does not really like when you do more than 1 request per second
    return country

def list_of_countries(latitude, longitude):
    ## finds list of countries in a circle around given place  
    set_of_countries = set()
    # we look at four corners of the square with our point in the middle and side = STEP,
    # check to which country they belong and return these countries
    for x in [-0.5*STEP, 0.5*STEP]:
        corner_latitude = latitude+x
        for y in [-long_step(corner_latitude)/2, long_step(corner_latitude)/2]:
            corner_longitude = round(longitude+y, 2)
            country = 'Unknown'
            # if the point is already in geoloc_dict we read it from there
            if not geoloc_dict[(geoloc_dict['latitude']==corner_latitude)&(geoloc_dict['longitude']==corner_longitude)].empty:
                country = geoloc_dict[(geoloc_dict['latitude']==corner_latitude)&(geoloc_dict['longitude']==corner_longitude)]['country'].values[0]
            else:   # if not, call which_country function
                country = which_country(corner_latitude, corner_longitude)
            if country != 'Unknown':
                set_of_countries.add(country) # adding the country of the corner to the set
    list_of_countries = list(set_of_countries)
    return list_of_countries

        
def search_languages(country):
    ## given a country determines the languages we will use for search
    local_languages = []
    ## check what languages are spoken in the country and which of the are popular in internet
    if country in languages['country'].tolist():
        local_languages = languages[languages['country']==country][['first_language', 'second_language']].values[0].tolist()
        local_languages = list(set(local_languages)&set(popular_languages))
    if len(local_languages) == 0: # if no popular languages were found, the default language is English
        local_languages = ['English'] 
    return local_languages

def search_words(countries):
    ## from list of countries returns a list of search words 
    words = set()
    for country in countries:
        # first we check if we are looking for red cross or red crescent
        if country in muslim_countries:
            org_type = 'red_crescent'
        else:
            org_type = 'red_cross'
        # and then translate it to the search languages
        for language in search_languages(country):
            translation = translations.loc[translations['language']==language, org_type].values[0]
            if str(translation) != 'nan':
                words.add(translations.loc[translations['language']==language, org_type].values[0])
    return list(words)


def search_for(latitude, longitude, search_word):
    ## searches for a red cross around given location using given language
    ## cheap search, only one result, returns place_id
    location_bias = 'circle:'+str(radius)+'@'+str(latitude)+','+str(longitude)
    search_result = gmaps.find_place(search_word, input_type = 'textquery', location_bias = location_bias, fields = ['place_id'])
    if len(search_result['candidates'])>0: ## means that we found nothing
        return search_result['candidates'][0]['place_id']
    else:
        return False

def text_search(latitude, longitude, search_word):
    ## searches for a red cross around given location using given language
    ## expensive search, up to 60 results, returns information about places
    global SPENT
    result_columns = ['search_lat', 'search_long', 'search_words', 'place_id', 'place_name', 'place_address', 'place_lat', 'place_long', 'distance']
    final_results = pd.DataFrame(columns = result_columns)
    location = str(latitude)+','+str(longitude)
    #relevant_fields = ['place_id', 'formatted_address', 'geometry/location', 'name', 'perm_closed']
    CONTINUE = True
    page = 0
    next_page_token = False
    while CONTINUE:
        page = page + 1
        #print(page)
        if not next_page_token: ## if there is no next_page_token, we perform normal search
            this_page = gmaps.places(search_word, location = location, radius = radius)
        else:
            # if there is we look at the next page
            time.sleep(5) # there is a short delay before the token works, so we wait
            this_page = gmaps.places(search_word, location = location, radius = radius, page_token = next_page_token)
        SPENT = SPENT + 0.4
        # transform search result to a nice data frame
        df_this_page = pd.DataFrame.from_records(this_page['results'])
        df_this_page['latitude'] = [x['location']['lat'] for x in df_this_page['geometry']]
        df_this_page['longitude'] = [x['location']['lng'] for x in df_this_page['geometry']]
        df_this_page['distance'] = (df_this_page['latitude'] - latitude)**2+(df_this_page['longitude'] - longitude)**2
        # add them to the final results
        if page == 1:
            all_pages = df_this_page
        else:
            all_pages = all_pages.append(df_this_page)
        # now we define if we need to do request for the next page or not
        if (df_this_page.shape[0]<20) | (page == 3) | (max(df_this_page['distance'])>(2*STEP)**2) | (not 'next_page_token' in this_page.keys()):
            CONTINUE = False
        else:
            next_page_token = this_page['next_page_token']
    
    final_results['place_id'] = all_pages['place_id']
    final_results['place_name'] = all_pages['name']
    final_results['place_address'] = all_pages['formatted_address']
    final_results['place_lat'] = all_pages['latitude']
    final_results['place_long'] = all_pages['longitude']
    final_results['distance'] = all_pages['distance']
    final_results[['search_lat', 'search_long', 'search_words']] = [latitude, longitude, search_word]
    return final_results
    


'''
INPUT PARAMETERS
Please write longitudes and latitudes in correct order, because it is not cheked anywhere
Also we can not handle crossing -180/180 longitude
'''
long_start, long_end = 3, 8
lat_start, lat_end = 50, 54
STEP = 0.5 # step of the grid. Choose from 1, 0.5 or 0.25 depending on the size of the region
radius = 111000*0.75*STEP

search_country = 'Guatemala' # set False if you do not care about the country
if search_country:
    lat_start = extreme_points.loc[extreme_points['country']==search_country, 'southernmost'].values[0]
    lat_end = extreme_points.loc[extreme_points['country']==search_country, 'nothernmost'].values[0]
    long_start = extreme_points.loc[extreme_points['country']==search_country, 'westernmost'].values[0]
    long_end = extreme_points.loc[extreme_points['country']==search_country, 'easternmost'].values[0]
    #print('Search area: [%f, %f] x [%f, %f]' % long_start % long_end % lat_srt % lat_end)ta
    

'''
First we go through the grid and search around each point for one place 
in all languages suitable for this area.
'''

latitude_range = np.arange(lat_start, lat_end, STEP)
first_search_results = pd.DataFrame(columns = ['latitude', 'longitude', 'search_words', 'place_id'])

# iterate over grid points and search for a red cross around the point
for latitude in latitude_range:
    longitude = long_start
    longitude_range = np.arange(long_start, long_end, longitude + long_step(latitude))
    while longitude < long_end:
        longitude = round(longitude + long_step(latitude), 2)
        #print(latitude, longitude)
        # find countries intersecting with the circle
        countries_here = list_of_countries(latitude, longitude)
        #print(countries_here)
        if search_country:
            if not search_country in countries_here:    
                continue                                
            countries_here = [search_country]        
        for search_word in search_words(countries_here):
            #print(search_word)
            ## search aroung this place using current search word from the list
            place_id = search_for(latitude, longitude, search_word) 
            # if something was found we save it
            if place_id:        
                new_search_results = pd.DataFrame([[latitude, longitude, search_word, place_id]], columns = ['latitude', 'longitude', 'search_words', 'place_id'])
                first_search_results = first_search_results.append(new_search_results)
        time.sleep(0.5)
   
    
'''
Now we need to check whether the place found is really close to the point we searched around
To check it for all places seems to costly (0.017 per request), so we only check places
that appeared at least twice in the results. For them we find their real coordinates and 
write them to checked_places data frame.
'''

# count for how many circles we found the same place      
first_search_results['count'] = first_search_results.groupby(['place_id'])['place_id'].transform('count')
found_places = first_search_results[['place_id', 'count']].drop_duplicates()
checked_places = pd.DataFrame(columns = ['place_id','lat_real', 'long_real']) # here we will save extended information
# iterates over found places that appears more than once and finds their actual location
for place_id in found_places[found_places['count']>1]['place_id']:
    place_location = gmaps.place(place_id, fields = ['geometry'])['result']['geometry']['location']
    SPENT = SPENT + 0.017
    checked_places = checked_places.append({'place_id': place_id, 'lat_real':place_location['lat'], 'long_real':place_location['lng']}, ignore_index = True)


'''
And then we get rid of the coordinates where the distance to the found location is more than 0.75*STEP
'''

cleaned_first_srch_results = first_search_results
cleaned_first_srch_results = cleaned_first_srch_results.merge(checked_places, how = 'left', on = 'place_id')
cleaned_first_srch_results.loc[cleaned_first_srch_results['lat_real'].isnull(),'lat_real'] = cleaned_first_srch_results['latitude']
cleaned_first_srch_results.loc[cleaned_first_srch_results['long_real'].isnull(),'long_real'] = cleaned_first_srch_results['longitude']
cleaned_first_srch_results['distance'] = (cleaned_first_srch_results['latitude']-cleaned_first_srch_results['lat_real'])**2+(cleaned_first_srch_results['longitude']-cleaned_first_srch_results['long_real'])**2
cleaned_first_srch_results = cleaned_first_srch_results.drop(cleaned_first_srch_results[cleaned_first_srch_results['distance']>(0.75*STEP)**2].index)


'''
cleaned_first_srch_results contains coordinates and languages for which we are going 
to perform expensive Text Search (0.04 per request).
The job is done by text_search function.
'''

result_columns = ['search_lat', 'search_long', 'search_words', 'place_id', 'place_name', 'place_address', 'place_lat', 'place_long', 'distance']
total_search_results = pd.DataFrame(columns = result_columns)
# we iterate over all grid points and search words for which at least one result was found
# and perform text_search for them  
for index, row  in cleaned_first_srch_results.iterrows():
    new_total_search_results = text_search(row['latitude'], row['longitude'], row['search_words'])
    total_search_results = total_search_results.append(new_total_search_results)
    #if SPENT > 50:
    #    print('More than 50 eur spent')
    #    break

'''
Nice! We have the list of places. 
Let's get rid of search information and remove duplicates.
'''
results = total_search_results
results['count'] = results.groupby(['place_id'])['place_id'].transform('count') #count how many times we found each place
places = results[['place_id', 'place_name', 'place_address', 'place_lat', 'place_long', 'count']]
places = places.drop_duplicates() 
if search_country: # if we use search country, drop the locations outside of it
    places['country'] = [x.split(', ')[-1] for x in places['place_address']] 
    places = places[places['country']==search_country]    

'''
For now we know the name and address of each place.
If we want to have also phone number, website and opening hours, we need to run another request
'''

places_extended = places
places_extended = places_extended.drop('count', axis = 1)
places_extended['phone_number'] = ''
places_extended['website'] = ''
places_extended['url'] = ''
places_extended['country'] = ''
places_extended['adm_lvl_1'] = ''
places_extended['adm_lvl_2'] = ''
places_extended['types'] = ''  # types contain the types of the place returned by google maps

# iterate over found places and request additional information about each place
for place_id in places_extended['place_id']:
    
    place_details = gmaps.place(place_id)['result'] # request to google maps, returns a lot of information
    SPENT = SPENT + 0.017
    
    # save the information in places_extended
    if 'international_phone_number' in place_details:
        places_extended.loc[places_extended['place_id']==place_id, 'phone_number'] = place_details['international_phone_number']
    if 'website' in place_details:
        places_extended.loc[places_extended['place_id']==place_id, 'website'] = place_details['website']
    if 'url' in place_details:
        places_extended.loc[places_extended['place_id']==place_id, 'url'] = place_details['url']
    if 'types' in place_details:
        places_extended.loc[places_extended['place_id']==place_id, 'types'] = ", ".join(place_details['types'])
    
    address = pd.DataFrame.from_records(place_details['address_components'])
    address.loc[[len(x)==0 for x in address['types']], 'types'] = ['Unknown']
    address['types'] = [x[0] for x in address['types']]    
    if 'country' in address['types'].values:
        places_extended.loc[places_extended['place_id']==place_id, 'country'] = address.loc[address['types']=='country', 'long_name'].values[0]
    if 'administrative_area_level_1' in address['types'].values:
        places_extended.loc[places_extended['place_id']==place_id, 'adm_lvl_1'] = address.loc[address['types']=='administrative_area_level_1', 'long_name'].values[0]
    if 'administrative_area_level_2' in address['types'].values:
        places_extended.loc[places_extended['place_id']==place_id, 'adm_lvl_2'] = address.loc[address['types']=='administrative_area_level_2', 'long_name'].values[0]
    
if search_country:        
    places_extended = places_extended[places_extended['country']==search_country]

places_extended.to_csv('search_results_'+search_country+'.csv')

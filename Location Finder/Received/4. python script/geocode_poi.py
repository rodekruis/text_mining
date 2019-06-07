#-------------------------------------------------------------------------------
# Name:        geocode_poi
# Purpose:     gets coordinates of POIs then writes then to existing csv file
#              change lines 25 & 43 everytime you have a new file

# Author:      benard mitto
#
# Created:     26/11/2018
# Copyright:   (c) bmitto; jduong
#-------------------------------------------------------------------------------
import time
start = time.time()

from geopy.geocoders import GoogleV3
import pandas as pd

# pull the api key from google. read google's T&C's on use of api's
with open('data/google_api.txt', 'r') as key:
    api_key = key.read()

# initiate the geoloator with your API key - purchased one from google.
geolocator = GoogleV3(api_key = api_key)

# read the csv file containing poi's
data = pd.read_csv('data/ke_borders.csv')

# iterate through the rows, passing place names to google's geolocator
for index, row in data.iterrows():
    try:
            print ("Geocoding.. %s" %(row['name']))

            latlng = geolocator.geocode (row['name'] + ', ' + row['country'])
            data.set_value(index, ['lat_y', 'long_x'], [latlng.latitude, latlng.longitude])
    except:
        print ("Could not find coordinates for: " + row['name'])
        data.set_value(index, ['lat_y', 'long_x'], [0, 0])

# write the output to same csv file

data.to_csv('data/ke_borders.csv', index=False)

# time the code execution

print ("It took {:.2f} seconds".format(time.time() - start))
##
###-------------------------------------------------------------------------------
### Name:        geocode_poi
### Purpose:     gets coordinates of POIs then writes then to existing csv file
###              change lines 25 & 43
##
### Author:      benard mitto
###
### Created:     26/11/2018
### Copyright:   (c) bmitto; jduong
###-------------------------------------------------------------------------------
##import time
##start = time.time()
##
##from geopy.geocoders import GoogleV3
##import pandas as pd
##
### pull the api key from google. read google's T&C's on use of api's
##with open('data/google_api.txt', 'r') as key:
##    api_key = key.read()
##
### initiate the geoloator with your API key - purchased one from google.
##geolocator = GoogleV3(api_key = api_key)
##
### read the csv file containing poi's
##data = pd.read_csv('data/ke_borders.csv')
##
### iterate through the rows, passing place names to google's geolocator
##for index, row in data.iterrows():
##    try:
##        # check if nonzero coordinates already exists
##        if ( (row.long_x==0 and row.lat_y==0) or (row.long_x.isnull() and row.lat_y.isnull()) ):
##
##            print ("Geocoding.. %s" %(row['name']))
##
##            latlng = geolocator.geocode (row['name'] + ', ' + row['country'])
##            data.set_value(index, ['lat_y', 'long_x'], [latlng.latitude, latlng.longitude])
##    except:
##        print ("Could not find coordinates for: " + row['name'])
##        data.set_value(index, ['lat_y', 'long_x'], [0, 0])
##
### write the output to same csv file
##
##data.to_csv('data/ke_borders.csv', index=False)
##
### time the code execution
##
##print ("It took {:.2f} seconds".format(time.time() - start))
from itertools import groupby
import numpy as np
import re

class Location:
    def __init__(self, loc_string, loc_list, index_start, index_end):

        self.string = loc_string
        self.list = loc_list
        self.index_start = index_start
        self.index_end = index_end

        self.dep_distance = None
        self.distance = None

def most_common(locations, locations_df):

    # Create list of found location strings
    lst = [location.string for location in locations]

    # Sort the list and count duplicates, then remove them
    lst = sorted(lst)
    location_counts = [(i, len(list(c))) for i, c in groupby(lst)]
    lst = sorted(list(set(lst)))
    # Find the places(s) with max counts
    counts = [count[1] for count in location_counts]
    idx_max = np.where(np.max(counts) == counts)[0]
    # Set location to first entry, this works if there is only one location, or as a fallback
    # if the multiple location handling doesn't work
    location = lst[idx_max[0]]
    # If there is more than one location, take the lowest level admin region.
    if len(idx_max) > 1:
        try:
            lst_max = [lst[idx] for idx in idx_max]
            location_info = locations_df[locations_df['FULL_NAME_RO'].isin(lst_max)]
            location = location_info.groupby('FULL_NAME_RO')['ADM1'].min().idxmin()
        except ValueError:  # in case location_info is empty due to string matching problem reasons
            pass

    # find corresponding location object
    for obj in locations:
        if obj.string == location:
            location = obj

    return [location]

def clean_locations(locations, text_to_replace):
    # fix ambiguities: [Bongo West, Bongo] --> [Bongo-West, Bongo]
    loc2_old, loc1_old = '', ''
    for loc1 in locations:
        for idx, loc2 in enumerate(locations):
            if loc1.string in loc2.string and loc1.string != loc2.string:
                # replace ' ' by '-'
                loc2_old = loc2.string
                loc2.string = re.sub(' ', '-', loc2_old)

                # save changes in sentence and location object
                text_to_replace = re.sub(loc2_old, loc2.string, text_to_replace)
                locations[idx].string = re.sub(' ', '-', locations[idx].string)

    return locations, text_to_replace

def merge_locations(location_obj1, location_obj2, sentence):
    # merge strings
    loc_string_start = location_obj1.index_start - sentence.start
    loc_string_end = location_obj2.index_end - sentence.start
    loc_string = sentence[loc_string_start:loc_string_end].text

    # merge lists
    loc_list = location_obj1.list + location_obj2.list

    # get indeces
    index_start = location_obj1.index_start
    index_end = location_obj2.index_end

    location = Location(loc_string, loc_list, index_start, index_end)

    return location

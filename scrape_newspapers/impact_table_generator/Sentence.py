import re
import unicodedata
import logging

from . import Ents
from . import Location
from utils import utils


logger = logging.getLogger(__name__)


class Sentence:
    def __init__(self, sentence, locations, language, location_article):
        self.sentence = sentence

        # remove newlines
        self.sentence_text = re.sub('\n', '', self.sentence.text)
        self.sentence_text = re.sub('\r', '', self.sentence_text)
        self.sentence_text = re.sub('-', ' ', self.sentence_text)

        # Find all locations in  sentence
        self.locations_found = [location for location in locations if sentence.start <= location.index_end < sentence.end]

        # Clean location strings
        self.locations_found, self.sentence_text = Location.clean_locations(self.locations_found, self.sentence_text)

        # Get list of final location dicts
        self._get_sentence_location(self.locations_found, self.sentence, language, location_article)

    def analyze(self, keywords, language):
        final_info_list = []
        # loop over numerical entities,
        # check if it's impact data and if so, add to dataframe
        ents = Ents.Ents(self.sentence, self.sentence_text, language)
        final_info_list += ents.analyze(keywords, self.locations_final, language)
        final_info_list += self._analyze_infrastructures(keywords)

        return final_info_list

    def _analyze_infrastructures(self, keywords):
        # look for infrastructures (not in numerical entities)
        # if found, add to dataframe
        int_inf_in_sent = []
        for token in self.sentence:
            if token.text in [ent.text for ent in filter(lambda w: (w.label_ == 'CARDINAL') | (w.label_ == 'MONEY'), self.sentence.as_doc().ents)]:
                continue
            for int_inf in keywords['type_infrastructure']:
                if (_normalize_caseless(int_inf) in _normalize_caseless(token.text)) \
                        and (len(_normalize_caseless(token.text)) <= len(_normalize_caseless(int_inf))+1):
                    int_inf_in_sent.append(token)

        info_list = []
        for infrastructure in int_inf_in_sent:
            inf_text = infrastructure.text.strip()
            inf_text = re.sub('\n', '', inf_text)

            # if multiple locations (or lists of locations) are found
            # check which is the closest one to the impact data
            if len(self.locations_final) > 1:
                # compute distances between infrastructure and locations, choose the closest one
                distances_locations_entities = []
                for location_obj in self.locations_final:
                    pattern_entity = utils.get_pattern_entity(location_obj.string, inf_text)
                    distances_locations_entities += [(location_obj.list,
                                                      len(chunk[0])-len(location_obj.string)-len(inf_text))
                                                     for chunk in re.finditer(pattern_entity, self.sentence_text)]
                closest_entity = min(distances_locations_entities, key = lambda t: t[1])[0]
            else:   # final location is a single (list of) location(s)
                closest_entity = self.locations_final[0].list

            for location in closest_entity:
                location = location.strip()
                # safety check
                if location == '':
                    logger.warning('location_infrastructure NOT FOUND !!!')
                    continue
                info_list.append([location, 'infrastructures_mentioned', inf_text, ''])
        return info_list

    @staticmethod
    def _check_list_locations(locations, sentence, language):
        """
        Check if locations are in a list (e.g. "Kalabo, Chibombo and Lundazi")
        or if they are scattered around the sentence.
        Create corresponding location dictionary
        """
        and_word = {
            'french': 'et',
            'english': 'and'
        }[language]
        list_final = []

        # check number of unique locations
        unique_locations = set([location.string for location in locations])
        if len(list(unique_locations)) < 2:
            return list_final

        # get sentence indeces of locations
        match_locations = []
        for location in locations:
            location_start = location.index_start - sentence.start
            location_end = location.index_end - sentence.start
            match_locations.append((location_start, location_end))

        # get list of indeces in between matches
        in_between = []
        for i in range(len(locations)-1):
            in_between.append(sentence[match_locations[i][1]:match_locations[i+1][0]].text)

        # loop over spans in between different locations
        cnt_num_loc = 1
        for cnt in range(len(match_locations)-1):
            # if span is more than 6 characters -> no list of locations (', and ' = 6 signs)
            #TODO: Think about generalization to different languages (alternatives for 6 characters?)
            if len(in_between[cnt]) > 6:
                cnt_num_loc = 1
                continue

            # if span contains a comma, start merging locations together
            if ',' in in_between[cnt]:
                if cnt_num_loc == 1:
                    temp_obj = Location.merge_locations(locations[cnt],locations[cnt+1], sentence)
                else:
                    temp_obj = Location.merge_locations(temp_obj, locations[cnt+1], sentence)
                cnt_num_loc += 1
                # if there is also and/et, save merged locations and continue to next span
                if ', {}'.format(and_word) in in_between[cnt]:
                    list_final.append(temp_obj)
                    # reset
                    cnt_num_loc = 1
                    # and/et in span
            elif and_word in in_between[cnt]:
                # merge and save merged spans
                if cnt_num_loc == 1:
                    temp_obj = Location.merge_locations(locations[cnt], locations[cnt + 1], sentence)
                else:
                    temp_obj = Location.merge_locations(temp_obj, locations[cnt+1], sentence)
                cnt_num_loc += 1
                list_final.append(temp_obj)
                # reset
                cnt_num_loc = 1
        return list_final

    def _get_sentence_location(self, locations_found, sentence, language, location_article):
        """
        For each location found in sentence, creates a location dictionary with:
        loc_string: Original location string in sentence, e.g. 'Segou' or 'Bamako, Sikasso et Koulikoro'
        loc_list: List containing separate locations, e.g. ['Segou'] or ['Bamako', 'Sikasso', 'Koulikoro']
        """
        # determine location, 3 cases:
        if len(locations_found) == 1:
            # easy case, assign all damages to the location
            self.locations_final = locations_found
        elif len(locations_found) > 1:
            # multiple locations mentioned!
            # will create a list of locations and later assign it to the closest target
            # first, get a list of locations in the order in which they appear in the sentence
            positions = []
            for loc in locations_found:
                positions.append(loc.index_start)
            locations_found_order = [x for _,x in sorted(zip(positions,locations_found), key = lambda t:t[0])]
            # check if some locations are mentioned within a list (e.g. Paris, London and Rome)
            location_lists = Sentence._check_list_locations(locations_found_order, sentence, language)
            # add a list of locations, merging those that are within a list
            locations_found_merged = locations_found_order.copy()
            for loc in locations_found_order:
                if any(loc.string in location_obj.string for location_obj in location_lists):
                    locations_found_merged.remove(loc)
            for loc in locations_found_merged:
                location_lists.append(loc)
            if len(location_lists) == 0:
                for loc in locations_found:
                    location_lists.append(loc)
            self.locations_final = location_lists
        else:
            # no locations mentioned in the sentence, use the paragraph one
            self.locations_final = location_article


def _normalize_caseless(text):
    return unicodedata.normalize("NFKD", text.casefold())

import re
import importlib
import unicodedata

Ents = importlib.import_module('Ents')
utils = importlib.import_module('utils')


class Sentence:
    def __init__(self, sentence, doc, location_matches, language, location_article):
        self.sentence = sentence

        # remove newlines
        self.sentence_text = re.sub('\n', '', self.sentence.text)
        self.sentence_text = re.sub('\r', '', self.sentence_text)
        self.sentence_text = re.sub('-', ' ', self.sentence_text)

        # Use locations from the full doc
        self.locations_found = [doc[i:j].text for (_, i, j) in location_matches
                                if sentence.start <= i < sentence.end]
        self.locations_found, self.sentence_text = clean_locations(self.locations_found, self.sentence_text)

        self._get_sentence_location(self.locations_found, self.sentence_text, language, location_article)

    def analyze(self, keywords, language):
        final_info_list = []
        # loop over numerical entities,
        # check if it's impact data and if so, add to dataframe
        ents = Ents.Ents(self.sentence, self.sentence_text, language)
        final_info_list += ents.analyze(keywords, self.location_final, language)
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
            if len(self.location_final) > 1:
                # compute distances between infrastructure and locations, choose the closest one
                distances_locations_entities = []
                for location_dict in self.location_final:
                    pattern_entity = utils.get_pattern_entity(location_dict['loc_string'], inf_text)
                    distances_locations_entities += [(location_dict['loc_list'],
                                                      len(chunk[0])-len(location_dict['loc_string'])-len(inf_text))
                                                     for chunk in re.finditer(pattern_entity, self.sentence_text)]
                closest_entity = min(distances_locations_entities, key = lambda t: t[1])[0]
            else:   # final location is a single (list of) location(s)
                closest_entity = self.location_final[0]['loc_list']

            for location in closest_entity:
                location = location.strip()
                # safety check
                if location == '':
                    print('WARNING: location_infrastructure NOT FOUND !!!')
                    continue
                info_list.append([location, 'infrastructures_mentioned', inf_text, ''])
        return info_list

    @staticmethod
    def _check_list_locations(locations, sentence, language):
        """
        Check if locations are in a list (e.g. "Kalabo, Chibombo and Lundazi")
        or if they are scattered around the sentence
        """
        and_word = {
            'french': 'et',
            'english': 'and'
        }[language]
        list_final = []
        if len(list(set(locations))) < 2:
            return list_final
        match_locations = []
        for location in locations:
            match = re.search(location, sentence)
            if match:
                match_locations.append((match.span()[0], match.span()[1]))
        if len(match_locations) < 2:
            return list_final
        in_between = []
        for i in range(0,len(match_locations)-1):
            in_between.append(sentence[match_locations[i][1]:match_locations[i+1][0]])
        merge = ''
        cnt_num_loc = 1
        loc_list = []
        for cnt in range(0, len(match_locations)-1):
            if len(in_between[cnt]) > 8:
                merge = ''
                cnt_num_loc = 1
                loc_list = []
                continue
            if ',' in in_between[cnt]:
                if cnt_num_loc == 1:
                    merge += sentence[match_locations[cnt][0]:match_locations[cnt+1][1]]
                else:
                    merge += sentence[match_locations[cnt][1]:match_locations[cnt+1][1]]
                cnt_num_loc += 1
                loc_list.append(locations[cnt])
                if ', {}'.format(and_word) in in_between[cnt]:
                    loc_list.append(locations[cnt+1])
                    list_final.append({'loc_string':merge, 'loc_list':loc_list}  )
                    merge = ''
                    cnt_num_loc = 1
                    loc_list = []
            elif and_word in in_between[cnt]:
                if cnt_num_loc == 1:
                    merge += sentence[match_locations[cnt][0]:match_locations[cnt+1][1]]
                else:
                    merge += sentence[match_locations[cnt][1]:match_locations[cnt+1][1]]
                cnt_num_loc += 1
                loc_list.append(locations[cnt])
                loc_list.append(locations[cnt+1])
                list_final.append({'loc_string': merge, 'loc_list': loc_list})
                merge = ''
                cnt_num_loc = 1
                loc_list = []
        return list_final

    def _get_sentence_location(self, locations_found, sentence_text, language, location_article):
        # determine location, 3 cases:
        if len(locations_found) == 1:
            # easy case, assign all damages to the location
            self.location_final = [{'loc_string':locations_found[0], 'loc_list':locations_found}]
        elif len(locations_found) > 1:
            # multiple locations mentioned!
            # will create a list of locations and later assign it to the closest target
            location_final = 'TBI'
            # first, get a list of locations in the order in which they appear in the sentence
            positions = []
            for loc in locations_found:
                positions.append(sentence_text.find(loc))
            locations_found_order = [x for _,x in sorted(zip(positions,locations_found))]
            # check if some locations are mentioned within a list (e.g. Paris, London and Rome)
            location_lists = Sentence. _check_list_locations(locations_found_order, sentence_text, language)
            # add a list of locations, merging those that are within a list
            locations_found_merged = locations_found_order.copy()
            for loc in locations_found_order:
                if any(loc in location_dict['loc_list'] for location_dict in location_lists):
                    locations_found_merged.remove(loc)
            for loc in locations_found_merged:
                location_lists.append({'loc_string':loc, 'loc_list':[loc]})
            if len(location_lists) == 0:
                for loc in locations_found:
                    location_lists.append({'loc_string':loc, 'loc_list':[loc]})
            self.location_final = location_lists
        else:
            # no locations mentioned in the sentence, use the paragraph one
            self.location_final = [{'loc_string':location_article, 'loc_list': [location_article]}]

def clean_locations(locations, text_to_replace):
    # fix ambiguities: [Bongo West, Bongo] --> [Bongo-West, Bongo]
    loc2_old, loc1_old = '', ''
    for loc1 in locations:
        for loc2 in locations:
            if loc1 in loc2 and loc1 != loc2:
                loc2_old = loc2
                loc1_old = loc1
                loc2 = re.sub(' ', '-', loc2_old)
                text_to_replace = re.sub(loc2_old, loc2, text_to_replace)
    if loc2_old != '':
        idx = locations.index(loc2_old)
        locations[idx] = re.sub(' ', '-', locations[idx])
        idx = locations.index(loc1_old)
        locations[idx] = ' '+locations[idx]
    return locations, text_to_replace


def _normalize_caseless(text):
    return unicodedata.normalize("NFKD", text.casefold())

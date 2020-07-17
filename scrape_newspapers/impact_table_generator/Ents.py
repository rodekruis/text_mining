import re
import logging

from word2number import w2n
from text_to_num import text2num
import networkx as nx

from utils import utils


logger = logging.getLogger(__name__)

LANGUAGES_WITH_ENTS = ['english']

CRAZY_NUMBER_CUTOFF = 1E6
USD_CUTOFF = 1E7
LOCAL_CURRENCY_CUTOFF = 1E11


class Ents:

    def __init__(self, sentence, sentence_text, language):
        self.sentence = sentence
        self.sentence_text = sentence_text
        self.offset_token_index = 0
        if language in LANGUAGES_WITH_ENTS:
            self.ents = filter(lambda w: (w.label_ == 'CARDINAL') | (w.label_ == 'MONEY'),
                               self.sentence.as_doc().ents)
            self.offset_token_index = self.sentence[0].i
        else:
            # Sometimes number tokens are classified as e.g. pronouns so also check for digits
            self.ents = [token for token in self.sentence if (token.pos_ == 'NUM' or token.is_digit)]

    def analyze(self, keywords, locations_final, language):
        final_info_list = []
        for ent in self.ents:
            # get entity text and clean it
            ent_text = re.sub('\n', '', ent.text).strip()
            # check if empty entity text
            if ent_text == '':
                continue
            # check if number is a year
            try:
                if int(ent_text) in range(2001,2041):
                    continue
            except ValueError:
                pass

            is_money, currency_found = self._check_if_money(ent_text,
                                                            keywords['currency_short'], keywords['currency_long'],
                                                            keywords['local_currency_names_short'],
                                                            keywords['local_currency_names_long'],
                                                            keywords['local_currency_code'])

            # check if it's monetary value
            if is_money:
                results = self._deal_with_money(ent_text, keywords, currency_found, language)
            else:
                # if it's not monetary value, look for object
                results = self._deal_with_object(ent, ent_text, language, keywords)
            if results is None:
                continue
            number, addendum, impact_label = results

            # safety check
            if impact_label.strip() == '':
                logger.warning('Impact_label NOT ASSIGNED !!!')
                continue

            # check if relevant location is unknown (single list of multiple locations counts as 1 relevant location found)
            if len(locations_final) > 1:
                # get dependency tree
                self._get_dependency_graph(self.sentence)
                closest_entity = self._deal_with_multiple_locations(locations_final, ent, ent_text, language)
            else:  #final location is a single (list of) location(s)
                closest_entity = locations_final[0].list

            # from closest_entity list, get location corresponding to numerical entity
            try:
                # if closest_entity contains multiple locations, divide numerical entity by number of locations and
                # distribute equally over different locations
                # if closest_entity contains single location, numerical entity is divided by 1 and assigned to location
                number_divided = str(int(int(number)/len(closest_entity)))
            except ValueError:
                logger.error('division failed: {}'.format(number))
                number_divided = number
            for location in closest_entity:
                location = location.strip()
                # safety check
                if location == '':
                    logger.warning('location_impact_data NOT FOUND !!!')
                    continue
                final_info_list.append([location, impact_label, number_divided, addendum])
        return final_info_list

    def _get_dependency_graph(self, sentence):
        edges = []

        for token in sentence:
            for child in token.children:
                edges.append(('{0}'.format(token.i), '{0}'.format(child.i)))
        try:
            self.dependency_graph = nx.Graph(edges)
        except nx.NetworkXError:
            self.dependency_graph = None
            logger.warning('Could not generate dependency tree')
            return

    def _deal_with_multiple_locations(self, locations, ent, ent_text, language):
        # convert from type entity to type token, if entity present
        if language in LANGUAGES_WITH_ENTS:
            ent = ent[0]
        # extract entity location, correct for offset if needed
        ent_loc = ent.i + self.offset_token_index
        # check if dependency tree exists
        if self.dependency_graph is not None:
            for location_obj in locations:
                # get dependency distances
                dep_distances = []
                for loc_index in range(location_obj.index_start,location_obj.index_end):
                    if str(loc_index) in self.dependency_graph:
                        dep_distances.append(nx.shortest_path_length(self.dependency_graph, source=str(ent_loc), target=str(loc_index)))
                # Quick fix for parsing quality of Spacy (sometimes dependency distances cannot be found due to bad parsing)
                if len(dep_distances) != 0:
                    dep_distance = min(dep_distances)
                    location_obj.dep_distance = dep_distance

                # get regular distance
                if ent_loc < location_obj.index_start:
                    distance = location_obj.index_start - ent_loc
                elif ent_loc >= location_obj.index_end:
                    distance = ent_loc - location_obj.index_end

                location_obj.distance = distance

            # find min dependency distance
            min_dep_distance = min([location_obj.dep_distance for location_obj in locations if type(location_obj.dep_distance)==int])
            min_dep_distances = [location_obj for location_obj in locations if location_obj.dep_distance == min_dep_distance]

            # if multiple locations corresponds with minimum dependency distance
            if len(min_dep_distances) > 1:
                # check regular distance
                min_distance = min([location_obj.distance for location_obj in min_dep_distances])
                min_distances = [location_obj for location_obj in min_dep_distances if location_obj.distance == min_distance]
                # Take first item of min_distances as closest_entity
                # Will fail in case two locations have same dep_distance and same 'regular' distance
                #TODO: Deal with case of equal dependency and regular distances
                closest_entity = min_distances[0].list
            else:
                #select location with minimum dependency distance
                closest_entity = min_dep_distances[0].list
        else:
            # check only regular distance if dependency tree is unavailable
            distances = []
            for location_obj in locations:
                if ent_loc < location_obj.index_start:
                    distance = location_obj.index_start - ent_loc
                elif ent_loc >= location_obj.index_end:
                    distance = ent_loc - location_obj.index_end

                distances.append((location_obj.list, distance))
            # assuming no equal distances
            #TODO: Deal with case of equal distances
            closest_entity = min(distances, key=lambda t: t[1])[0]

        return closest_entity

    def _deal_with_object(self, ent, ent_text, language, keywords):
        # get the object, i.e. what the number refers to
        obj = self._get_object(ent, language)
        number = Ents._process_number_words(ent_text, language)
        number = str(number).strip('%')   #remove %, it was giving an error
        addendum = '' # extra info (currency or object)
        impact_label = '' # label specifying the nature of the impact data
        if (obj != '') & (number != ''):
            if any(type_obj in obj.lower() for type_obj in keywords['type_people_death']):
                impact_label = 'people_dead'
            elif any(type_obj in obj.lower() for type_obj in keywords['type_people']):
                # if it's "family" or similar, multiply by 4
                if any(type_obj in obj.lower() for type_obj in keywords['type_people_multiple']):
                    number = str(int(round(float(number)*4)))
                # determine if they are dead or not
                is_dead = False
                if language in LANGUAGES_WITH_ENTS:
                    number_and_object = [tok for tok in ent]
                else:
                    number_and_object = [ent, ent.head]
                for tok in self.sentence:
                    if tok.text == obj:
                        number_and_object.append(tok)
                # first, check if root verb or its children
                # (e.g. 'seven people who died') are death-like
                for tok in number_and_object:
                    roots_and_children = list()
                    roots_and_children.append(tok.head.text.lower())
                    roots_and_children += [ch.text.lower() for ch in tok.children]
                    if any(verb in roots_and_children for verb in keywords['list_verb_death']):
                        is_dead = True

                if is_dead:
                    impact_label = 'people_dead'
                else:
                    impact_label = 'people_affected'
            elif any(type_obj in obj.lower() for type_obj in keywords['type_house']):
                impact_label = 'houses_affected'
            elif any(type_obj in obj.lower() for type_obj in keywords['type_infrastructure']):
                impact_label = 'infrastructures_affected'
                for type_obj in filter(lambda w: w in obj.lower(), keywords['type_infrastructure']):
                    addendum += type_obj
            elif any(type_obj in obj.lower() for type_obj in keywords['type_livelihood']):
                impact_label = 'livelihood_affected'
                for type_obj in filter(lambda w: w in obj.lower(), keywords['type_livelihood']):
                    addendum += type_obj
            else:
                # nothing interesting, discarding
                return None
        else:
            # object not found, discarding
            return None
        try:
            if int(number) >= CRAZY_NUMBER_CUTOFF:
                logger.warning('crazy number (not assigned) {} {}'.format(number, self.sentence_text))
                return None
        except:
            pass
        return number, addendum, impact_label

    def _deal_with_money(self, ent_text, keywords, currency_found, language):
        number, addendum = self._process_number_money(ent_text,
                                                      keywords['currency_short'], keywords['currency_long'],
                                                      keywords['local_currency_names_short'],
                                                      keywords['local_currency_names_long'],
                                                      keywords['local_currency_code'], language)
        if addendum == '':
            addendum = currency_found
        try:
            int(float(number))
        except ValueError:
            return None
        if int(number) >= USD_CUTOFF and addendum == 'USD':
            logger.warning('too many dollars: {}'.format(self.sentence_text))
            return None
        if int(number) >= LOCAL_CURRENCY_CUTOFF and addendum == keywords['local_currency_code']:
            logger.warning('too much local currency: {}'.format(self.sentence_text))
            return None
        # check if root is damage-like
        token_root = next(iter([token for token in self.sentence if token.dep_ == 'ROOT']), None)
        if any(type in token_root.text for type in keywords['donation']):
            # donation, discard
            logger.debug('donation, discarding')
            return None
        else:
            if any(type == self.sentence_text.lower() for type in keywords['type_livelihood']):
                logger.debug('    proposing assignement: {} in damage_livelihood'.format(ent_text))
                impact_label = 'damage_livelihood'
            else:
                logger.debug('    proposing assignement: {} in damage_general'.format(ent_text))
                impact_label = 'damage_general'
            return number, addendum, impact_label

    def _get_object(self, ent, language):
        """
        Get what a given number refers to
        """
        obj = ''

        if language in LANGUAGES_WITH_ENTS :
            # get all tokens of which entity is composed
            tokens_in_ent = []
            for idx, word in enumerate(ent):
                tokens_in_ent.append(word)
            # get last token in sentence
            for idx, word in enumerate(self.sentence):
                if word.text == tokens_in_ent[-1].text:
                    # first attempt: look for head of type NOUN
                    if word.head.pos_ == 'NOUN':
                        obj = word.head.text
                        break
                    # second attempt: navigate the children list, look for an 'of'
                    for possible_of in word.children:
                        if possible_of.text == 'of':
                            for possible_object in possible_of.children:
                                obj = 'of ' + possible_object.text
                                break

        else:
            # If no ents, need to navigate the tree by hand
            obj = ent.head.text
        return obj

    @staticmethod
    def _process_number_words(text_raw, language):
        """
        Convert number words into numbers
        """
        if language == 'english':
            parser = w2n.word_to_num
        elif language == 'french':
            parser = text2num

        # make lowercase, remove commas
        text = text_raw.lower()
        text = re.sub('\n|\,|\.', '', text)
        text = text.strip()

        # fix misspelling: '30millions' --> '30 millions'
        for (number, word) in re.findall('([0-9\.]+)([a-z]+)', text):
            text = re.sub(str(number+word), str(number+' '+word), text)

        # special case: 'between x and y' --> '(x+y)/2'
        for (x_text, y_text) in re.findall('between\s([0-9a-z\s\-]+)\sand\s([0-9a-z\s\-]+)', text):
            try:
                x = parser(x_text)
                y = parser(y_text)
                text = str((x+y)/2.)
                return text
            except ValueError:
                logger.warning('number conversion failed (special case *between*): {}'.format(text))
                return text

        # special case: 'x per cent'
        for perc in re.findall('([0-9a-z\-]+)\sper\scent', text):
            try:
                text = str(parser(perc)) + '%'
                return text
            except ValueError:
                logger.warning('number conversion failed (special case *per cent*): {}'.format(text))
                return text

        # word_to_num not working, need to convert string to number
        for (number, word) in re.findall('([0-9\.]+)\s([a-z]+)', text):
            number_old = number
            if 'billion' in word:
                number = str(float(number)*1000000000)
            elif 'million' in word:
                number = str(float(number)*1000000)
            elif 'thousand' in word:
                number = str(float(number)*1000)
            text = re.sub(str(number_old+' '+word), number, text)

        # try first if it can be directly converted
        if not re.match('^\d+$', text):  # Only try on strings containing non-digits
            try:
                text = str(parser(text))
            except ValueError:
                # remove words that cannot be converted to numbers: 'more than seven' --> 'seven'
                text_clean = ''
                for word in re.findall('[a-z0-9\-]+', text):
                    try:
                        parser(word)
                        text_clean += word
                        if re.search(r'\d', word) is None:
                            text_clean += ' '
                    except ValueError:
                        continue

                # try to convert what is left into one number
                try:
                    text = str(parser(text_clean))
                except ValueError:
                    # if we have a vague number word: assign a reasonable number
                    if 'billions' in text:
                        text = '2000000000'
                    elif 'millions' in text:
                        text = '2000000'
                    elif 'hundreds of thousands' in text:
                        text = '200000'
                    elif 'tens of thousands' in text:
                        text = '20000'
                    elif 'thousands' in text:
                        text = '2000'
                    elif 'hundreds' in text:
                        text = '200'
                    elif 'dozens' in text:
                        text = '24'
                    elif 'tens' in text:
                        text = '20'
                    elif 'dozen' in text:
                        text = '12'
                    else:
                        logger.warning('number conversion failed ({}) !!!'.format(text))
                        text = re.sub('[^0-9\.]+', '', text)
        return text

    def _process_number_money(self, text, currencies_short, currencies_long, local_currency_names_short,
                              local_currency_names_long, local_currency_code, language):
        """
        Get unique currency format
        """
        currency = ''
        for currency_short in currencies_short:
            if currency_short in text.lower():
                currency = currency_short
                text = re.sub(re.compile(currency_short+'[\.]{0,1}', re.IGNORECASE), '', text)

        for currency_long in currencies_long:
            regex_currency = re.compile(currency_long, re.IGNORECASE)
            if re.search(regex_currency, self.sentence_text) is not None:
                for idx, word in enumerate(self.sentence):
                    if word.text in text:
                        if currency_long in self.sentence[idx+1].text or currency_long in self.sentence[idx+2].text:
                            currency = currency_long
                        if currency_long in self.sentence[idx-1].text or currency_long in self.sentence[idx-2].text:
                            currency = currency_long
        if currency != '':
            if currency in local_currency_names_short or currency in local_currency_names_long:
                currency = local_currency_code
            else:
                currency = 'USD'

        number = Ents._process_number_words(text, language)
        return number, currency

    def _check_if_money(self, ent_text, currencies_short, currencies_long,
                        local_currency_names_short, local_currency_names_long, local_currency_code):
        """
        Check if numerical entity is monetary value
        """
        is_money = False
        currency_found = ''
        currencies_all = currencies_long+currencies_short

        for currency in currencies_all:
            if currency in ent_text.lower():
                is_money, currency_found = True, currency

        for currency in currencies_all:
            regex_currency = re.compile(currency, re.IGNORECASE)
            if re.search(regex_currency, self.sentence.text) is not None:
                for idx, word in enumerate(self.sentence):
                    if word.text in ent_text:
                        try:
                            if currency == self.sentence[idx+1].text or currency == self.sentence[idx+2].text:
                                is_money, currency_found = True, currency
                            if currency == self.sentence[idx-1].text or currency == self.sentence[idx-2].text:
                                is_money, currency_found = True, currency
                        except:
                            pass

        if currency_found != '':
            if currency_found in local_currency_names_short or \
                    currency_found in local_currency_names_long:
                currency_found = local_currency_code
            else:
                currency_found = 'USD'

        return is_money, currency_found


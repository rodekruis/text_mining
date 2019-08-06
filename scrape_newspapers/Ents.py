import re

from word2number import w2n
from text_to_num import text2num

LANGUAGES_WITH_ENTS = ['english']

CRAZY_NUMBER_CUTOFF = 1E6
USD_CUTOFF = 1E7
LOCAL_CURRENCY_CUTOFF = 1E11


class Ents:

    def __init__(self, sentence, sentence_text, language):
        self.sentence = sentence
        self.sentence_text = sentence_text
        if language in LANGUAGES_WITH_ENTS:
            self.ents = filter(lambda w: (w.label_ == 'CARDINAL') | (w.label_ == 'MONEY'),
                               self.sentence.as_doc().ents)
        else:
            # Sometimes number tokens are classified as e.g. pronouns so also check for digits
            self.ents = [token for token in self.sentence if (token.pos_ == 'NUM' or token.is_digit)]

    def analyze(self, keywords, location_final, language):
        final_info_list = []
        for ent in self.ents:
            # get entity text and clean it
            ent_text = re.sub('\n', '', ent.text).strip()
            if ent_text == '':
                continue
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
                print('WARNING: impact_label NOT ASSIGNED !!!')
                continue

            # assign location
            location_impact_data = location_final

            # if multiple locations or lists of locations are found
            # check which is the closest one to the impact data
            if type(location_final) is list:
                # compute distances between entity (i.e. impact data) and locations, choose the closest one
                distances_locations_entities = []
                ent_text = ent_text.strip()
                ent_text = re.sub('\n', '', ent_text)
                for idx, (loc, num, loc_sublist) in enumerate(location_final):
                    pattern_entity = re.compile(str('('+re.escape(loc)+'(.*)'+re.escape(ent_text)+'|'+re.escape(ent_text)+'(.*)'+re.escape(loc)+')'), re.IGNORECASE)
                    distances_locations_entities += [(loc, len(chunk[0])-len(loc)-len(ent_text), num, loc_sublist) for chunk in re.finditer(pattern_entity, self.sentence_text)]
                closest_entity = min(distances_locations_entities, key=lambda t: t[1])
                # if closest location is a list, location_impact_data will be a list of strings
                # otherwise just a string
                if closest_entity[2] > 1:
                    location_impact_data = closest_entity[3] # get list of locations in the list
                else:
                    location_impact_data = closest_entity[0]

            # get final info
            if type(location_impact_data) is str:
                location_impact_data = location_impact_data.strip()
                # safety check
                if location_impact_data == '':
                    print('WARNING: location_impact_data NOT FOUND !!!')
                    continue
                final_info_list.append([location_impact_data, impact_label, number, addendum])
            elif type(location_impact_data) is list:
                # multiple locations, divide impact data equally among them
                number_divided = ''
                try:
                    number_divided = str(int(int(number)/len(location_impact_data)))
                except ValueError:
                    print('division failed: ', number)
                    number_divided = number
                for location in location_impact_data:
                    location = location.strip()
                    # safety check
                    if location == '':
                        print('WARNING: location_impact_data NOT FOUND !!!')
                        continue
                    final_info_list.append([location, impact_label, number_divided, addendum])
        return final_info_list

    def _deal_with_object(self, ent, ent_text, language, keywords):
        # get the object, i.e. what the number refers to
        obj = self._get_object(ent, language)
        number = Ents._process_number_words(ent_text, language)
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
                roots_ch = tok.children
                for tok in number_and_object:
                    roots_and_children = list()
                    roots_and_children.append(tok.head.text.lower())
                    roots_and_children += [ch.text.lower() for ch in roots_ch]
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
                print('WARNING: crazy number (not assigned)', number)
                print(self.sentence_text)
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
            print('WARNING: too many dollars:')
            print(self.sentence_text)
            return None
        if int(number) >= LOCAL_CURRENCY_CUTOFF and addendum == keywords['local_currency_code']:
            print('WARNING: too much local currency:')
            print(self.sentence_text)
            return None
        # check if root is damage-like
        token_root = next(iter([token for token in self.sentence if token.dep_ == 'ROOT']), None)
        if any(type in token_root.text for type in keywords['donation']):
            # donation, discard
            # print('donation, discarding')
            return None
        else:
            if any(type == self.sentence_text.lower() for type in keywords['type_livelihood']):
                # print('    proposing assignement: ', ent_text, ' in damage_livelihood')
                impact_label = 'damage_livelihood'
            else:
                # print('    proposing assignement: ', ent_text, ' in damage_general')
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
                print('number conversion failed (special case *between*): ', text)
                return text

        # special case: 'x per cent'
        for perc in re.findall('([0-9a-z\-]+)\sper\scent', text):
            try:
                text = str(parser(perc)) + '%'
                return text
            except ValueError:
                print('number conversion failed (special case *per cent*): ', text)
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
                        print('number conversion failed (', text, ') !!!')
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


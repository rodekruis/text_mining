import re

from text_to_num import text2num


class Article:

    def __init__(self,
                 generator,
                 id_row):

        self.text = generator.articles_df.iloc[id_row]['text']
        self.title = generator.articles_df.iloc[id_row]['title']
        self.doc_with_title = self.title + '.\n' + self.text
        self.article_num = generator.articles_df.iloc[id_row]['Unnamed: 0']
        self.publication_date = str(generator.articles_df.iloc[id_row]['publish_date'].date())

        self._preprocess_french_number_words()
        self._preprocess_numbers(generator)

    def _preprocess_numbers(self, generator):
        # merge numbers divided by whitespace: 20, 000 --> 20000
        # Also works with repeated groups, without comma, and with appended currency
        # e.g. 5 861 052 772FCFA --> 5861052772FCFA (won't work with accents though)
        numbers_divided = re.findall('\d+(?:\,*\s\d+\w*)+', self.text)
        if numbers_divided is not None:
            for number_divided in numbers_divided:
                if re.search('(20[0-9]{2}|19[0-9]{2})', number_divided) is not None:
                    continue
                else:
                    number_merged = re.sub('\,*\s', '', number_divided)
                    self.text = re.sub(number_divided, number_merged, self.text)

        # split money: US$20m --> US$ 20000000 or US$20 --> US$ 20
        numbers_changed = []
        for currency in generator.keywords['currency_short']:
            currency_regex = re.sub('\$', '\\\$', currency)
            numbers_divided = re.findall(re.compile(currency_regex+'[0-9.]+\s', re.IGNORECASE), self.text)
            for number_divided in numbers_divided:
                try:
                    number_final = currency + ' ' + re.search('[0-9.]+\s', number_divided)[0]
                    self.text = re.sub(re.sub('\$', '\\\$', number_divided), number_final, self.text)
                except:
                    pass
            numbers_divided = re.findall(re.compile(currency_regex+'[0-9.]+[a-z]', re.IGNORECASE), self.text)
            for number_divided in numbers_divided:
                try:
                    number_split_curr = re.sub(currency_regex, currency_regex+' ', number_divided)
                    number_isolated = re.search('[0-9.]+[a-z]', number_split_curr)[0]
                    number_text = re.search('[0-9.]+', number_isolated)[0]
                    appendix = re.search('[a-z]', number_isolated)[0].lower()
                    # try to convert number and appendix into one number
                    try:
                        number = float(number_text)
                        if appendix == 'b':
                            number *= 1E9
                        elif appendix == 'm':
                            number *= 1E6
                        elif appendix == 'k':
                            number *= 1E3
                        else:
                            print('money conversion failed (', self.text, ') !!!')
                    except:
                        pass
                    number_final = re.sub(appendix, '', str(int(number)))
                    number_final = currency + ' ' + number_final
                    self.text = re.sub(re.sub('\$', '\\\$', number_divided), number_final, self.text)
                    numbers_changed.append(number_final)
                except:
                    pass

    def _preprocess_french_number_words(self):
        # Since the French model has no number entities, need to deal with number words by hand
        # for now. Could eventually train our own cardinal entity, but in the medium
        # term this should probably be made a pipeline component, although the text
        # immutability may be an issue
        french_number_words = {'millier': 1E3, 'milliers': 1E3,
                               'million': 1E6, 'millions': 1E6,
                               'milliard': 1E9, 'milliards': 1E9}

        words = self.text.split(' ')
        for i, word in enumerate(words):
            if word in french_number_words.keys():
                prev_word = words[i-1]
                if re.match('^\\d+$', prev_word):
                    number = int(prev_word)
                    need_to_merge = True
                else:
                    try:
                        number = text2num(str(prev_word))
                        need_to_merge = True
                    except ValueError:
                        number = 2  # Multiply 1 million or whatever by 2
                        need_to_merge = False

                number *= french_number_words[word]
                if need_to_merge:
                    search_text = '{}\\s+{}'.format(prev_word, word)
                else:
                    search_text = word
                self.text = re.sub(search_text, str(int(number)), self.text)

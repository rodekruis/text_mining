import fitz


def pdf_search(keyword, filename):
    """Look into the pdf for values based on keywords in the main table"""

    # we open the given file for searching
    with fitz.open(filename) as doc:
        for page in doc:
            res = page.searchFor(keyword)
            if res:
                break
        if not res:
            print(f"Keyword {keyword} is not found in {filename}")
            return None  # return None if the keyword hasn't been found

        # Find the smallest block from the pdf containing  the  key word
        bl = page.getText("Blocks")
        xw0, yw0, xw1, yw1 = res[0] # coordinates of keyword
        #we iterate over every block
        for i in bl:
            x0, y0, x1, y1 = i[0:4]
            #  see if the keyword is in the current block by comparing the coordinates
            if xw0 >= x0 and xw1 <= x1 and yw0 >= y0 and yw1 <= y1:
                #analyze the block that contains the keyword
                #we iterate over rows if there are multiple
                if len(i[4].split('\n')) > 2:
                    for w in i[4].split('\n'):
                        w = w.replace(':', '')
                        if w.find(keyword) >= 0:
                            if keyword == 'budget' or keyword == 'people affected' or keyword == 'people assisted':
                                # for these keywords, we take out the numbers only
                                w = w.replace(keyword + ':', '')
                                w = w.replace(',', '')
                                w = w.replace(' ', '')
                                # we first remove the characters at the beginning
                                iden = 0
                                for j in range(len(w)):
                                    if w[j].isdigit():
                                        break
                                    else:
                                        iden += 1
                                w = w[iden:]
                                # Now we remove the characters at the end
                                wr = ''

                                for j in range(len(w)):
                                    if not w[j].isdigit():
                                        return wr
                                    wr += w[j]
                                return wr

                            return w.replace(keyword, '')
                else:
                    #th esituation whre we only hav one row
                    w = i[4]
                    if keyword == 'budget' or keyword == 'people affected' or keyword == 'people assisted':
                        # for these keywords, we take out the numbers only
                        w = w.replace(keyword + ':', '')
                        w = w.replace(',', '')
                        w = w.replace(' ', '')
                        # we first remove the characters at the beginning
                        iden = 0

                        for j in range(len(w)):
                            if w[j].isdigit():
                                break
                            else:
                                iden += 1

                        w = w[iden:]

                        # Now we remove the characters at the end
                        wr = ''

                        for j in range(len(w)):
                            if not w[j].isdigit():
                                return wr
                            wr += w[j]
                        return wr
                    return w.replace(keyword + ':', '')


def find_date(filename):
    """Finds the first date mentioned in the text."""
    f = fitz.open(filename)

    for page in f.pages():
        text = page.getText()

        numbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                  "November",
                  "December"]

        # different situation titles
        if "Situation analysis" in text or "Situation Analysis" in text or "SITUATION ANALYSIS" in text:
            words = []
            for word in text.split():
                words.append(word)

            # use this to not get date from first page
            start_index = 0

            # make sure to look after situation analysis
            for index in range(len(words) - 2):
                if words[index] == 'Situation' or words[index] == 'SITUATION':
                    start_index = index + 2
                    break

            for index in range(start_index, len(words) - 2):
                if words[index][0] in numbers and words[index + 1] in months:
                    date = words[index]
                    month = words[index + 1]
                    year = words[index + 2]
                    result = str(date) + "-" + str(months.index(month) + 1) + "-" + str(year)
                    if result[len(result) - 1] in [".", ",", "!", "?"]:  # Remove unnecessary additions
                        result = result[:len(result) - 1]
                    return result

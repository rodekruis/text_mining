import csv

import matplotlib.pyplot as plt
import pandas as pd
#Opens CSV file and decluterst data and puts it into a list
with open('data_clean.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=";")

    aff_people = []
    date = []
    for row in reader:
        stringy = row['budget']
        clean_string = stringy.replace("'", "")
        res = clean_string.strip('][').split(', ')
        aff_people += res

        stringy = row['Date']
        clean_string = stringy.replace("'", "")
        res = clean_string.strip('][').split(', ')
        date += res

result = zip(aff_people, date)

#Data is counted and stored into list, but only if prespecifies conditions hold
count = dict()
for elem in result:
    dat = elem[1][6:10]

    print(elem[0])
    print(dat)
    if not elem[0].isnumeric():
        continue
    if dat in count:
        count[dat] += int(elem[0])
    else:
        count[dat] = int(elem[0])

#Further checks on validity of the data
for key in list(count):
    # del count['']
    if count[key] <= 100000:
        del count[key]
    elif not key.isnumeric():
        del count[key]
    elif key[0] != "2":
        del count[key]
    elif key == "2013":
        del count[key]
#Data is plotted and plots are saved
dt = pd.DataFrame.from_dict(count, orient='index').sort_index()
dt.plot(kind='bar', legend=None)
plt.title("Allocated Budget to Disasters per Year")
plt.ylabel('Budget in CHF')
plt.xlabel('Year', labelpad=1)
plt.gcf().subplots_adjust(bottom=0.2)
plt.savefig('budg_year.png', format='png')
plt.show(block=True)

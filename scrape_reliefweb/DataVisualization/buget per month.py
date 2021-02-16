import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate

import csv
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
    dat = elem[1][3:5]

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
    elif int(key) > 12:
        del count[key]

#Data is plotted and plots are saved
dt = pd.DataFrame.from_dict(count, orient='index').sort_index()
print(tabulate(dt, headers=['Month', 'Budget Allocated'], tablefmt='psql'))

dt.plot(kind='bar', legend=None)
plt.title("Allocated Budget to Disasters per Month")
plt.ylabel('Budget in CHF')
plt.xlabel('Month', labelpad=1)
plt.gcf().subplots_adjust(bottom=0.2)
# axes = plt.gca()
# axes.set_ylim([0,55000000])
plt.savefig('budg_month.png', format='png')

plt.show(block=True)

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
        stringy = row['people affected']
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

for key in list(count):
    if count[key] <= 10000:
        del count[key]
    elif not (key[0:2]).isnumeric():
        del count[key]

#Data is plotted and plots are saved
dt = pd.DataFrame.from_dict(count, orient='index').sort_index()
print(tabulate(dt, headers=['Month', 'Number of Affected People'], tablefmt='psql'))

dt.plot(kind='bar', legend=None)
plt.title("Number of Affected People by Disasters per Month")
plt.ylabel('Number of Affected People')
plt.xlabel('Month in Year', labelpad=1)
plt.gcf().subplots_adjust(bottom=0.1)
plt.savefig('month_aff.png', format='png')

plt.show(block=True)

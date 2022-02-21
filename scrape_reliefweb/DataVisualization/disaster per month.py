import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter
import numpy

import csv
#Opens CSV file and decluterst data and puts it into a list
with open('data_clean.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=";")

    dis_type = []
    for row in reader:
        stringy =row['Date']
        clean_string = stringy.replace("'", "")
        res = clean_string.strip('][').split(', ')
        dis_type += res

#Data is counted and stored into list, but only if prespecifies conditions hold
months = []
for elem in dis_type:
    months += [elem[3:5]]


months_counts = Counter(months)

for key in list(months_counts):
    del months_counts['']
    if months_counts[key] <= 6:
        del months_counts[key]

#Data is plotted and plots are saved
dt = pd.DataFrame.from_dict(months_counts, orient='index').sort_index()
dt.plot(kind='bar', legend=None)
plt.title("Number of Monthly Disaster Occurrences")
plt.ylabel('Number of disasters')
plt.xlabel('Month', labelpad=1)
plt.gcf().subplots_adjust(bottom=0.1)
plt.savefig('dis_month.png', format='png')

plt.show(block=True)

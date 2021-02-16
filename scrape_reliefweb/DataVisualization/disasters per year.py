import csv
from collections import Counter

import matplotlib.pyplot as plt
import pandas as pd

#Opens CSV file and decluterst data and puts it into a list
with open('data_clean.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=";")

    dis_type = []
    for row in reader:
        stringy = row['Date']
        clean_string = stringy.replace("'", "")
        res = clean_string.strip('][').split(', ')
        dis_type += res

#Data is counted and stored into list, but only if prespecifies conditions hold
years = []
for elem in dis_type:
    years += [elem[6:10]]

year_counts = Counter(years)

for key in list(year_counts):
    del year_counts['']
    if year_counts[key] <= 4:
        del year_counts[key]

#Data is plotted and plots are saved
dt = pd.DataFrame.from_dict(year_counts, orient='index').sort_index()
dt.plot(kind='bar', legend=None)
plt.title("Number of Disaster Occurrences per Year")
plt.ylabel('Number of disasters')
plt.xlabel('Year', labelpad=2)
plt.gcf().subplots_adjust(bottom=0.15)
plt.savefig('dis_year.png', format='png')
plt.show(block=True)

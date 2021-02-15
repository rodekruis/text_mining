import csv
from collections import Counter

import matplotlib.pyplot as plt
import pandas as pd
#Opens CSV file and decluterst data and puts it into a list
with open('data_clean.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=";")

    dis_type = []
    for row in reader:
        stringy = row['Affected Countries']
        clean_string = stringy.replace("'", "")
        res = clean_string.strip('][').split(', ')
        dis_type += res

#Data is counted and stored into list, but only if prespecifies conditions hold
country_counts = Counter(dis_type)
for key in list(country_counts):
    del country_counts['']
    if country_counts[key] <= 1:
        del country_counts[key]

#Data is plotted and plots are saved
dt = pd.DataFrame.from_dict(country_counts, orient='index').sort_index()
dt.plot(kind='bar', legend=None)
plt.title("Number of Monthly Disaster Occurrences")
plt.ylabel('Number of disasters')
plt.xlabel('Month', labelpad=1)
plt.gcf().subplots_adjust(bottom=0.1)
plt.savefig('countries_dis.png', format='png')

plt.show(block=True)

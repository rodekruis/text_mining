import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter
from tabulate import tabulate

import csv
with open('data_clean.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=";")

    dis_type = []
    for row in reader:
        stringy =row['Type of disaster']
        clean_string = stringy.replace("'", "")
        res = clean_string.strip('][').split(', ')
        dis_type += res


dis_counts = Counter(dis_type)

for key in list(dis_counts):
    if dis_counts[key] <= 2:
        del dis_counts[key]
    if key == "":
        del dis_counts[key]

dt = pd.DataFrame.from_dict(dis_counts, orient='index').sort_index()
print(tabulate(dt, headers = ['Disaster Type', 'Number of Occurrences'], tablefmt = 'psql'))

dt.plot(kind='bar', legend=None)
plt.title("Occurrence of Different Disaster Types")
plt.ylabel('Number of occurrences')
plt.xlabel('Disaster Type', labelpad=1)
plt.gcf().subplots_adjust(bottom=0.4)
plt.savefig('dis_type.png', format='png')

plt.show(block=True)






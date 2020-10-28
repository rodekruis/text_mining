# -*- coding: utf-8 -*-
import pandas as pd
pd.options.display.max_columns=10

def clean_string(target_string):
    target_string = target_string.rstrip()
    target_string = target_string.rstrip(',')
    target_string = target_string.rstrip()
    return target_string
    

df = pd.read_csv('contacts.csv', header=None)

df.columns = ['name',
              'address',
              'postal_address',
              'tel',
              'fax',
              'telegram',
              'email',
              'web',
              'twitter',
              'facebook']

#df['name', 'address', 'postal_address', 'tel', 'fax', 'telegram', 'email', 'web', 'twitter', 'facebook']
df[df.columns] = df.apply(lambda x: x.str.translate(str.maketrans("\n\t\r", "   ")))
for i in range(10):
    df[df.columns] = df.apply(lambda x: x.str.rstrip())
    df[df.columns] = df.apply(lambda x: x.str.strip(','))

print(df.head())

df.to_csv('contacts_clean.csv')


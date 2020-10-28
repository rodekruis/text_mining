# -*- coding: utf-8 -*-
import pandas as pd  
import numpy as np

df_social = pd.read_csv('social_media.csv', header=None)

df_social.columns = ['web', 'facebook_from_local_website', 'twitter_from_local_website', 'instagram_from_local_website']

df_social[df_social.columns] = df_social.apply(lambda x: x.str.replace("[", ""))
df_social[df_social.columns] = df_social.apply(lambda x: x.str.replace("]", ""))
df_social[df_social.columns] = df_social.apply(lambda x: x.str.replace("'", ""))

df_contacts = pd.read_csv('contacts_clean.csv', header=0)

df = df_contacts.merge(df_social, on = 'web', how = 'left')

df[['facebook', 'twitter']] = df[['facebook', 'twitter']].apply(lambda x: x.str.lower())
df['facebook_all'] = df[['facebook', 'facebook_from_local_website']].apply(lambda x: None if x.isnull().all() else ', '.join(x.dropna()), axis=1)
df['twitter_all'] = df[['twitter', 'twitter_from_local_website']].apply(lambda x: None if x.isnull().all() else ', '.join(x.dropna()), axis=1)
df['instagram_all'] = df['instagram_from_local_website']


df.to_csv('contacts_and_social_media.csv')


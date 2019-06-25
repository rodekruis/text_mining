# -*- coding: utf-8 -*-
"""
Created on Sun Jun  2 12:22:40 2019

@author: LuisaB
"""

import pandas as pd
from sklearn.naive_bayes import MultinomialNB
import numpy as np
from sklearn.model_selection import cross_val_score
import sklearn
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import confusion_matrix
from sklearn.metrics import precision_score, recall_score, f1_score

df_corrected = pd.read_csv(#path to file)


#From here: https://www.geeksforgeeks.org/learning-model-building-scikit-learn-python-machine-learning-library/
# reading csv file 
data = df_corrected
print(data)


# shape of dataset 
print("Shape:", data.shape) 
  
# column names 
print("\nFeatures:", data.columns) 
  
# storing the feature matrix (X) and response vector (y) 
X = data.iloc[:,np.r_[6:28, 46:99]]#selecting the correct columns; change numbers as needed.
data.columns.get_loc('pas')
y = data[data.columns[44]]#selecting the correct column; change numbers as needed.

print(X)
print(y)

#Defining the model
model = MultinomialNB()

loo = LeaveOneOut() 

scores = cross_val_score(model, X = X, y = y, cv = loo, scoring='accuracy')
print(scores)

# Map dataframe to encode values and put values into a numpy array
# From here: https://stackoverflow.com/questions/39187875/scikit-learn-script-giving-vastly-different-results-than-the-tutorial-and-gives
encoded_labels = data['categories cyclone'].map(lambda x: 1 if x == 'high' else 0).values # low will be 0 and high will be 1
y = encoded_labels

#Creating a confusion matrix
y_actu = y
y_pred = scores
confusion_matrix(y_actu, y_pred)
pd.crosstab(y_actu, y_pred, rownames=['True'], colnames=['Predicted'], margins=True)

#Calculating precision, recall and F1-score
precision = precision_score(y_actu, y_pred, average='binary') 
recall = recall_score(y_actu, y_pred, average='binary') 
f1_score = f1_score(y_actu, y_pred, average='binary')


#Looking for most important features
#https://stackoverflow.com/questions/50526898/how-to-get-feature-importance-in-naive-bayes

#Features for "low" category
nb = MultinomialNB().fit(X, y)
likelihood_df = pd.DataFrame(nb.feature_log_prob_.transpose(),columns=['Low', 'High'])

#Using sklearn's Multinomial NaiveBayes's attribute feature_log_prob_
important_features_low = nb.feature_log_prob_[0, :]

neg_class_prob_sorted = nb.feature_log_prob_[0, :].argsort()
print(neg_class_prob_sorted)
pos_class_prob_sorted = nb.feature_log_prob_[1, :].argsort()
print(pos_class_prob_sorted)

#Loop over files to get indices of original terms
lst = []
for col in X.columns:
    print(col)
    lst.append(col)
column_names = pd.DataFrame(lst)

#Loop over files to get indices of sorted terms
index_lst = []
for i in neg_class_prob_sorted:
    print(i)
    index_lst.append(i)
index_fea = pd.DataFrame(index_lst) 

#Save log probabilities according to indices
log_fea = []
for t in important_features_low:
    print(t)
    log_fea.append(t)
log_fea = pd.DataFrame(log_fea)

#Reset index    
column_names.reset_index(level=0, inplace=True)

#Renaming columns
index_fea.rename(columns={ index_fea.columns[0]: "first_column" }, inplace=True)
column_names.rename(columns={ column_names.columns[1]: "keywords" }, inplace=True)

#Resetting index
log_fea.reset_index(level=0, inplace=True)
#Renaming column
log_fea.rename(columns={ log_fea.columns[1]: "logs" }, inplace=True)


#Creating dictionaries
column_names_dict = column_names['keywords'].to_dict()
index_fea_dict =  {value:key for key, value in column_names_dict.items()}
log_fea_dict = log_fea['logs'].to_dict()
log_fea_dict =  {value:key for key, value in log_fea_dict.items()}

#Printing the corresponding words next to indices
wordcolumn = []
for i in index_fea['first_column']:
    wordcolumn.append(column_names_dict[i])
index_fea['keywords'] = wordcolumn

#Merging into one dataframe
combined_log_ind = pd.merge(log_fea, index_fea, right_index=True, left_index=True)

combined_log_ind_ranked = combined_log_ind

#Sorting by log probabilty values
combined_log_ind_ranked.sort_values(by=['logs'], inplace=True, ascending=False)
print(combined_log_ind_ranked)

#Getting the top 15 words
top_15_low = combined_log_ind_ranked[:15]
#Saving the top 15 words as file
top_15_low_df = top_15_low.to_csv(#path to new file)


#Features for "high" category

important_features_high = nb.feature_log_prob_[1, :]
print(important_features_high)

#Getting indices of words
index_lst2 = []
for i in pos_class_prob_sorted:
    print(i)
    index_lst2.append(i)
index_fea2 = pd.DataFrame(index_lst) 

#Rename column
index_fea2.rename(columns={ index_fea2.columns[0]: "first_column" }, inplace=True)

#Printing the corresponding words next to indices
wordcolumn2 = []
for i in index_fea2['first_column']:
    wordcolumn2.append(column_names_dict[i])
index_fea2['keywords'] = wordcolumn2

#Save log probabilities according to indices
log_fea2 = []
for t in important_features_high:
    print(t)
    log_fea2.append(t)
log_fea2 = pd.DataFrame(log_fea2)
    
#Resetting index
log_fea2.reset_index(level=0, inplace=True)
#Renaming column
log_fea2.rename(columns={ log_fea2.columns[1]: "logs" }, inplace=True)


#Creating a dictionary
log_fea_dict2 = log_fea2['logs'].to_dict()
log_fea_dict2 =  {value:key for key, value in log_fea_dict2.items()}

#Merging into one dataframe
combined_log_ind_high = pd.merge(log_fea2, index_fea2, right_index=True, left_index=True)

combined_log_ind_ranked2 = combined_log_ind_high

#Sorting by log probabilty values
combined_log_ind_ranked2.sort_values(by=['logs'], inplace=True, ascending=False)

#Getting the top 15 words
top_15_high = combined_log_ind_ranked2[:15]
#Saving the top 15 words as file
top_15_high_df = top_15_high.to_csv(#path to new file)

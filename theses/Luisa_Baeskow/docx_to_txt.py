# -*- coding: utf-8 -*-
"""
Created on Thu Mar  7 10:40:08 2019

@author: luisab
"""

import os
from os import listdir
from os.path import isfile, join
import docx


mypath = #path to file
os.chdir(mypath)

list_files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
print(list_files)

for k in list_files:
    merge_path = mypath + k #Merging the path with the single file names
    doc = docx.Document(merge_path)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    help_var = '\n'.join(fullText)
    with open(merge_path + ".txt", "w", encoding='utf-8') as file1: #Opening and writing the txt files
        file1.write(repr(help_var))













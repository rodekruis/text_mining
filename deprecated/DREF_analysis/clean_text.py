#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 29 17:23:42 2019

@author: jacopo
"""

import os
import re

def get_ASCII_only(text):
    """ filter a string to get only ASCII char 
    """
    return ''.join([i if (ord(i) < 128) and (i!='\'') else '' for i in text])

def clean_text(txtDir):
    
    for text_file_name in os.listdir(txtDir): #iterate through text files
        fileExtension = text_file_name.split(".")[-1]
        fileName = ''.join(text_file_name.split(".")[:-1])
        
        if fileExtension == "txt" and 'clean' not in fileName:
            text_file = open(text_file_name,"r")
            text = text_file.read()
            
            # get onli ASCII characters, remove "\'"
            text = get_ASCII_only(text)
            
            # substitute two next line with oner space
            text = re.sub('\n\n', ' ', text)
            
            # remove everything after "Contact information"
            text = text.partition("Contact information")[0]
            
            with open(fileName + '_clean.' + fileExtension, "w") as text_file_clean:
                text_file_clean.write(text) #write text to text file
            
            text_file.close()
               
txtDir = "./data/"
clean_text(txtDir)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 29 17:23:42 2019

@author: jacopo
"""

from tika import parser
import os
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

#converts anything to string
def parsedPDF(pdfFilename, pages=None):
    parsedPDF = parser.from_file(pdfFilename)
    Text=(parsedPDF["content"])
    return Text 
    
#converts all files in pdfDir, saves all resulting txt files to txtDir
def convertMultiple(pdfDir, txtDir):

    if pdfDir == "": pdfDir = os.getcwd() + "\\" #if no pdfDir passed in 
    
    for pdf in os.listdir(pdfDir): #iterate through files directory

        pdfFilename = pdfDir + pdf         
        filename, file_extension = os.path.splitext(pdfFilename)
    
        text = parsedPDF(pdfFilename) #get string of text content of pdf
        
        with open(filename+".txt", "w") as textFile:
            textFile.write(text) #write text to text file
            
pdfDir = "./data/"
txtDir = "./data/"
convertMultiple(pdfDir, txtDir)
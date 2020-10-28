# -*- coding: utf-8 -*-
"""
Created on Mon Jun 25 14:10:02 2018

@author: DerkFrijmersum
"""


# encoding: utf-8
from io import StringIO
from tika import parser
from tika import language
import os

#converts pdf, returns its text content as a string
def parsedPDF(pdfFilename, pages=None):
    parsedPDF = parser.from_file(pdfFilename)
    Text=(parsedPDF["content"])

    return Text 

#%%
    
#converts all pdfs in directory pdfDir, saves all resulting txt files to txtdir
def convertMultiple(pdfDir, txtDir):
    if pdfDir == "": pdfDir = os.getcwd() + "\\" #if no pdfDir passed in 
    for pdf in os.listdir(pdfDir): #iterate through pdfs in pdf directory
        fileExtension = pdf.split(".")[-1]
        if fileExtension == "pdf":
            pdfFilename = pdfDir + pdf 
            text = parsedPDF(pdfFilename) #get string of text content of pdf
            textFilename = txtDir + pdf+ ".txt"
            textFile = open(textFilename, "wb") #make text file
            textFile.write(text) #write text to text file
            
pdfDir = "C:/Received/PDF/"
txtDir = "C:/Data/Text_Reports/"
convertMultiple(pdfDir, txtDir)
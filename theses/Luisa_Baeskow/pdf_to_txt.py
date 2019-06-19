
##Converting PDF files to txt files

import os
from os import listdir
from os.path import isfile, join
import shutil
mypath = #path to files
os.chdir(mypath)


#Reading the PDF files which are text (and not images)
import PyPDF2

list_files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
print(list_files)

for k in list_files:
    try:
        merge_path = mypath + k#Merging the path with the single file names
        output_path = mypath + "txt\\" + k
        output_path = output_path.rsplit('.', 1)[0]
        pdf_file = PyPDF2.PdfFileReader(open(merge_path, 'rb'))
        pdf_text = []
        for index in range(0,pdf_file.numPages):
            pdf_text.append(pdf_file.getPage(index).extractText())
        help_var = pdf_text
        with open(output_path + ".txt", "w", encoding='utf-8') as file1: #Opening and writing the txt files
            file1.write(repr(help_var))
    except:
        print(k)
    #the exception prints the files that were not readable


#Finding out which files we deleted because they were unreadable
txt_path = mypath + "txt\\"

txt_files = [f for f in listdir(txt_path) if isfile(join(txt_path, f))] 
txt_files = [item.rsplit('.', 1)[0] for item in txt_files]
pdf_files = [item.rsplit('.', 1)[0] for item in list_files]

txt_set = set(txt_files)
pdf_set = set(pdf_files)  

missing = list(sorted(pdf_set - txt_set)) 
print(missing)  

#Move these files to seperate folder

leftover_pdfs = #path to new folder

for item in missing:
    new_item = item + ".pdf"
    shutil.move(new_item, leftover_pdfs)

#Looping over the files using OCR on PDF. Turns out to be very slow. I ended up
#not using this because none of the files where about the Philippines
    
import pytesseract
import pdf2image

pdf_path = #path to files
leftover_files = [f for f in listdir(leftover_pdfs) if isfile(join(leftover_pdfs, f))]


for i in leftover_files:
    merge_path = leftover_pdfs + i
    print(merge_path)
    output_path = mypath + "txt\\" + i
    output_path = output_path.rsplit('.', 1)[0]
    img = pdf2image.convert_from_path(merge_path, 500)
    ocr_texts = []
    for page in img:
        readable_image = page.convert('L')
        pdf_content = ocr_texts.append(pytesseract.image_to_string(readable_image))
    with open(merge_path + ".txt", "w", encoding='utf-8') as file1: #Opening and writing the txt files
            file1.write(repr(ocr_texts))
    
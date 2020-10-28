from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from io import StringIO
import os
import codecs
import re

for country in os.listdir('Approved Plans'):

    for file in os.listdir('Approved Plans/'+country):

        if file.startswith('MDR'):
            output_string = StringIO()
            with open('Approved Plans/'+country+'/'+file, 'rb') as fh:
                parser = PDFParser(fh)
                doc = PDFDocument(parser)
                rsrcmgr = PDFResourceManager()
                device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
                interpreter = PDFPageInterpreter(rsrcmgr, device)
                for ix, page in enumerate(PDFPage.create_pages(doc)):
                    interpreter.process_page(page)
                file1 = codecs.open('Approved Plans/'+country+'/'+file.split('.')[0]+'.txt', "w", "utf-8")  # write mode
                file1.write(output_string.getvalue())
                file1.close()

        sectors = ['Livelihoods and basic needs', 'Water, sanitation and hygiene']

        if file.endswith('txt'):
            file1 = codecs.open('Approved Plans/' + country + '/' + file.split('.')[0] + '.txt', "r",
                                "utf-8")  # write mode
            text = file1.read()
            # get detailed operational plan
            text = re.split(r"(.*)Detailed Operational Plan", text, re.MULTILINE | re.DOTALL)[-1]

            for sector in sectors:
                text_sector = ' '.join(re.split(sector, text, re.MULTILINE | re.DOTALL))
                for line in re.split(r"\n", text_sector, re.MULTILINE | re.DOTALL)[:10]:
                    if 'People targeted:' in line:
                        peop_target = re.findall(r"[0-9,]+", line)[0]
                    if 'Requirements (CHF):' in line:
                        budget = re.findall(r"[0-9,]+", line)[0]

                activity_paragraphs = re.split("Activities planned", text_sector, re.MULTILINE | re.DOTALL)
                for activity_paragraph in activity_paragraphs[1:2]:
                    # TBI

            print(country)

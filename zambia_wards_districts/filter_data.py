from __future__ import unicode_literals, print_function
import plac
import random
from pathlib import Path
import spacy
import re
from spacy import displacy
import codecs
from nltk.tokenize import sent_tokenize
import os
import json
import pandas as pd

def FilterData():
    """Read HTML source, extract lists of wards and districts, save in json"""

    with open('Zambia_wards_districts_html.txt') as f:
        content = str(f.readlines())
        re1_matches = re.findall(r"data-wiki=\"\w+\"", content)
        re1_matches = [match.replace("\"","") for match in re1_matches]
        re1_matches = [match.replace("data-wiki=","") for match in re1_matches]
        re2_matches = re.findall(r"data-wiki=\"\w+\s\w+\"", content)
        re2_matches = [match.replace("\"","") for match in re2_matches]
        re2_matches = [match.replace("data-wiki=","") for match in re2_matches]
        re3_matches = re.findall(r"data-wiki=\"\w+,\s\w+\"", content)
        re3_matches = [match.replace("\"","") for match in re3_matches]
        re3_matches = [match.replace("data-wiki=","") for match in re3_matches]
        re3_matches = [re.sub(", \w+", "", match) for match in re3_matches]
        matches = re1_matches + re2_matches + re3_matches

    wards = [match for match in matches if 'District' not in match]
    districts = [match for match in matches if 'District' in match]
    districts = [re.sub("District", "", match) for match in districts]

    wards_and_districts = {'Districts': districts, 'Wards': wards}
    with open('Zambia_wards_districts.json', 'w') as fjson:
        json.dump(wards_and_districts, fjson)

if __name__ == "__main__": # executing module as script
    FilterData()

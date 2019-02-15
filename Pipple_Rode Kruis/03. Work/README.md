# impact data from doc
Extract impact data from red cross documents.

Working example based on reports of the Vulnerability Assessment Committee (VAC) of Zambia.

### workflow
The extraction of impact data proceed in 3 consecutive steps:
1) Transform .pdf into .txt files
2) Divide each document into paragraph and identify interesting ones (dates, locations, victims...)
3) Analyze each paragraph and extract structured impact data

### input
The inputs that the various scripts need are:
1) A set of documents, in pdf format
2) A list of geographical locations (typically country-based)
3) One or more lists of words relevant for impact data (victims, infrastructures, etc.)

### output
The final output of the pipeline is a table (in csv and/or h5) containg impact data, in the form 

<table>
<tr>
  <td>location</td>
  <td>date</td>
<td>damage_livelihood</td>
<td>damage_general</td>
<td>people_affected</td>
<td>people_dead</td>
<td>houses_affected</td>
<td>livelihood_affected</td>
<td>infrastructures_affected</td>
<td>infrastructures_mentioned</td>
</tr>
</table>

### requirements
modules required to run the scripts (all on PyPI):
1) [tika](https://pypi.org/project/tika/)
2) [nltk](https://pypi.org/project/nltk/)
3) [pandas](https://pypi.org/project/pandas/)
4) [spacy](https://pypi.org/project/spacy/)
5) [word2number](https://pypi.org/project/word2number/)

### TO DO
1) adapt output format to [DesInventar](https://www.desinventar.net/)
2) ...

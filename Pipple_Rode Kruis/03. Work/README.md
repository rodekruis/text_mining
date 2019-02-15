# impact data from doc
Extract impact data from red cross documents. Working example based on reports of the Vulnerability Assessment Committee (VAC) from Zambia.

### workflow
The extraction of impact data proceed in 3 consecutive steps:
1) Transform .pdf into .txt files
2) Divide each document into paragraph and identify interesting ones (dates, locations, victims...)
3) Analyze each paragraph and extract structured impact data

### input
The inputs that the various scripts needs are:
1) A set of documents, in pdf format
2) A list of geographical locations (typically country-based)
3) One or more lists of words relevant for impact data (victims, infrastructures, etc.)

### output
The final output of the pipeline is a table (in csv and/or h5) containg impact data

<table>
<tr>
  <td>Package Status</td>
  <td>
		<a href="https://pypi.org/project/pandas/">
		<img src="https://img.shields.io/pypi/status/pandas.svg" alt="status" /></td>
		</a>
</tr>
<tr>
  <td>License</td>
  <td>
    <a href="https://github.com/pandas-dev/pandas/blob/master/LICENSE">
    <img src="https://img.shields.io/pypi/l/pandas.svg" alt="license" />
    </a>
</td>
</tr>
</table>

### requirements
modules required to run the scripts:
1) spacy

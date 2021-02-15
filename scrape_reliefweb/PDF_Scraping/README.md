## pdf_reader.py
Calls function to download, process and delete pdf's.
It initializes variables, downloads and reads pdf to find the variables in the text and puts this into a csv file.
Then it deletes the pdf that was used.



## pdf_processing.py
It contains functions that are used to download and delete the target pdf files.

### pdf_download(url)
Download file and writes the content

### delete_file(filename)
Deletes earlier downloaded file from repository to keep a clean memory.

## pdf_miner.py
It contains functions that are used to extract different type of information from the target pdf file.

### pdf_search(keyword, filename)

pdf_search obtains the information corresponding to the 'keyword' from the beginning table of the file, where filename 
is the name of the downloaded pdf file that we want to scrape from. For numerical variables, such as budget, the function 
automatically removes the unit and return the numerical values only. However, the function is written after carefully 
analyzing the structure of the tables from the 'final reports' provided by reliefweb. The function performance might not 
be desirable if other type of files are used as input.

### find_date(filename)

find_date uses a simple heuristic to obtain an approximation of the date of the disaster. Namely IFRC final reports always state what happened when and where in the first sentence. The date mentioned in this sentence therefore indicates the start of the disasters.
The function returns the date in the format DD-MM-YYYY.

---

Notes:

- (1): More dates can be found in the disaster summary, which can be obtained in the future for a timeline for instance

## location_miner.py
Contains the function that mines the cities from the country of the disasters from the summary on the website

### find_cities(filename, country)
Uses the package geograpy to find mentioned cities.
Geograpy is fast and effective, yet it takes some workaround to get it properly installed with the additional required packages, which we describe here:

Install geograpy3
Install pymupdf
Install fitz
Install nltk
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download()

-> select punkt to be downloaded



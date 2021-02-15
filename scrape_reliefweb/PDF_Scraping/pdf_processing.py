import requests
import os


def pdf_download(url):
    """Download the pdf file from the input url and return the file name if the download is successful"""
    # print('Download Starting...') # For tracking purposes
    r = requests.get(url)
    filename = url.split('/')[-1]  # this will take only the last part of the splitted part of the url

    with open(filename, 'wb') as output_file:  # Write contents into file
        output_file.write(r.content)
    # print('Download Completed!!!') # For tracking purposes
    return filename


def delete_file(filename):
    """Delete file with filename f."""
    """Inspired by https://www.w3schools.com/python/python_file_remove.asp"""
    if os.path.exists(filename):
        os.remove(filename)
    else:
        print("The file does not exist")

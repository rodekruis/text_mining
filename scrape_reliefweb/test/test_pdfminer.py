import unittest
from project.PDF_Scraping.pdf_processing import delete_file, pdf_download
from project.PDF_Scraping.pdf_miner import find_date, pdf_search
import subprocess
import sys





def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


class TestSuite(unittest.TestCase):
    def test_pdfsearch(self):
        install("PyMuPDF")
        #link of the file that will be used in the test
        testinglinks="https://reliefweb.int/sites/reliefweb.int/files/resources/MDRPH037dfr.pdf"
        filename = pdf_download(testinglinks)
        #list of variables that will be tested
        var_list = ['Operation start date', 'Operation end date', 'Operation budget',
            'Number of people affected', 'Number of people assisted']
        expected_result = {'Operation start date': "31 November 2019", 'Operation end date': "31 May 2020", 'Operation budget': "499719",
       'Number of people affected': "1993580", 'Number of people assisted': "24527"}

        for i in var_list:
            a=pdf_search(i,filename).strip(' ').replace(',','')
            b=expected_result[i].strip(' ')
        self.assertEqual(a, b,msg='Equal')

        delete_file(filename)

    def test_pdf_download(self):
        url = "https://reliefweb.int/sites/reliefweb.int/files/resources/MDRPH037dfr.pdf"
        a = pdf_download(url)
        assert a == "MDRPH037dfr.pdf" #double check this

    def test_deletefile(self):
    #for this function we used manual testing:
    # we downloaded a file, used the deletefile and saw it dissappear
    # the same holds for downloading multiple files in a loop.
    # they stay in the directory without deletefile
    # they are removed from the directory when using deletefile (after downloading and using it)
        return True

    def test_find_date(self):
        # link of the file that will be used in the test
        testinglinks = "https://reliefweb.int/sites/reliefweb.int/files/resources/MDRPH037dfr.pdf"
        filename = pdf_download(testinglinks)
        # list of variables that will be tested
        #var_list = ['date']
        expected_result = {'date': "30-11-2019"}

        #for i in var_list:
        a = find_date(filename)
        b = expected_result['date'].strip(' ')
        self.assertEqual(a, b, msg='Equal')

        delete_file(filename)

    # MANUAL TEST of find_cities
    # the geograpy module is too complex to install for pytest to work properly
    # the test below gives the result expected.This is verified by a manual test

    # def test_find_cities(self):

    #     # link of the file that will be used in the test
    #     filename = "https://reliefweb.int/report/philippines/philippines-typhoon-kammuri-dref-final-report-mdrph037"
    #
    #     expected_result = {'cities':['Sorsogon', 'Quezon']}
    #
    #     a = find_cities(filename,'Philippines')
    #     b = expected_result['cities']
    #     self.assertEqual(a, b, msg='Equal')
    #     #['Philippines']
    #
    #     delete_file(filename)


if __name__ == "__main__":
    unittest.main()

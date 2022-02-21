## scrape_reliefweb

This project takes scrapes situation reports of the IFRC from ReliefWeb and mines impact data from them.
This impact data is placed into a dataset and visualized. The order of using the pipeline is as follows:
* Start with the WebScrapers folder to obtain datasets:
  * Dataset 1 contains final reports with more variables
  * Dataset 2 containns a list of all disasters reported on ReliefWeb
* Then use the PDF_Scraping folder to obtain the variables for dataset 1
* Lastly you can use the DataVisualization folder for plots and graphs of dataset 1
* You can use the DataEnrichment folder go get plots, graphs and maps of dataset 2

Dataset 1 (called dataset_final_reports.csv) and dataset 2 (called all_disasters.csv) are present in the Datasets folder.
Every folder has its own README for instructions of using the files within.

N.B. See **Delft report.pdf** for more details.

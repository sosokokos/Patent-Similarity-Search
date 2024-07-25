from webScraper import getPatent, get_patent_numbers
from vectorDatabase import *


patents = ["US10244791B2", "US11399571B2", "US20210401061A1", "US10327479B2", "US20190087302A1",
               "US20190045837A1", "US10765145B2", "USD871665S1", "US11462307B2", "US20120214107A1", 
               "US10251423B2", "US20050236006A1", "US4715387A", "US5893371A", "US20190387796A1"]

def main():
    deleteIndex("test-index")
    initializeDatabase("test-index")

    for patent in patents:
        tester(patent)

    printResults(patents)
    
main()
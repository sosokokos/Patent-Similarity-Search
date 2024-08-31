from webScraper import getPatent, get_similar_patents
from vectorDatabase import *

patents = ["US10244791B2", "US11399571B2", "US20210401061A1", "US10327479B2", "US20190087302A1",
               "US20190045837A1", "US10765145B2", "USD871665S1", "US11462307B2", "US20120214107A1", 
               "US10251423B2", "US20050236006A1", "US4715387A", "US5893371A", "US20190387796A1", "US11834668B2"
               "US20210045602A1", "US11386168B2", "US5677136A"]

def main():
    deleteIndex("working-index")
    deleteIndex("storage-index")
    initializeDatabase("working-index")
    initializeDatabase("storage-index")

    response = newNodes("working-index", "test-batch", patents)

    while len(response) > 0:
        response = newNodes("working-index", "test-batch", response)

    

main()


def newNodes(target_index, target_namespace, patents_input):
    upsert_patents_bulk(target_index,target_namespace, patents_input)
    responses = filter_test_batch()
    printResults("storage-index", "target-patents")
    return responses
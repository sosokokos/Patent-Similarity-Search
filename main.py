from webScraper import getPatent, get_similar_patents
from vectorDatabase import *


patents = ["US10244791B2", "US11399571B2", "US20210401061A1", "US10327479B2", "US20190087302A1",
               "US20190045837A1", "US10765145B2", "USD871665S1", "US11462307B2", "US20120214107A1", 
               "US10251423B2", "US20050236006A1", "US4715387A", "US5893371A", "US20190387796A1", 
               "US20210045602A1", "US11386168B2", "US11834668B2", "US5677136A"]


tester = ["US10251423B2", "US20050236006A1", "US4715387A",]

keywords = ["smoking" , "smoking cessation" ,"smoking alternative", "battery" , "electronic cigarette" , "e-cigarette" , "vaporizer" ,
                "liquid" , "nicotine substitute" , "nicotine reduction" , "health" , "nicotine" , "device" , "vaporization" , "atomizer" , "quit",
                "algorithm" , "tracking" , "portable device" , "smart device" , "health improvement" , "health impact" , "usage data", "quit smoking" ,
                "feedback mechanism", "usage feedback", "data collection", "habit combating", "cartridge chamber", "liquid substance", "oral" ,
                "nicotine dependence", "coil", "vapor flow rate", "nicotine modulation", "feedback system", "user experience", "non-nicotine liquid"]


def main():
    deleteIndex("working-index")
    initializeDatabase("working-index")
    upsert_patents_bulk("working-index","test-batch", patents)

    #upsert_patents_bulk("working-index","keeper-batch", tester)
    #deleteNamespace("working-index","keeper-batch")
    userInput_query = " ".join(keywords)
    query_embedding = get_MiniLM_embeddings(userInput_query.lower())
    
    
    print(querryDatabase(query_embedding, "working-index", "test-batch"))
    #printResults(patents)


main()
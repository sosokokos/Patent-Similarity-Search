from webScraper import getPatent
from vectorDatabase import *

keywords = ["smoking" , "smoking cessation" ,"smoking alternative", "battery" , "electronic cigarette" , "e-cigarette" , "vaporizer" ,
                "liquid" , "nicotine substitute" , "nicotine reduction" , "health" , "nicotine" , "device" , "vaporization" , "atomizer" , "quit",
                "algorithm" , "tracking" , "portable device" , "smart device" , "health improvement" , "health impact" , "usage data", "quit smoking" ,
                "feedback mechanism", "usage feedback", "data collection", "habit combating", "cartridge chamber", "liquid substance", "oral" ,
                "nicotine dependence", "coil", "vapor flow rate", "nicotine modulation", "feedback system", "user experience", "non-nicotine liquid"]
index_name = "test-index"

def querrySummary():
    userInput_query = " ".join(keywords)
    query_embedding = get_openai_embeddings(userInput_query.lower())
    results = querryDatabaseFiltered(query_embedding, index_name, "US20190387796A1")

    print("--------- Similarity Scores ---------")
    for i in range(len(results)):
        print("[" + results[i]['id'] + "] Score: " + str(results[i]['score']))


def main():
    #deleteIndex("test-index")
    #initializeDatabase("test-index")
    
    #listIndexes()
    
    patents = ["US10244791B2", "US11399571B2", "US20210401061A1", "US10327479B2", "US20190087302A1",
               "US20190045837A1", "US10765145B2", "USD871665S1", "US11462307B2", "US20120214107A1", 
               "US20120214107A1", "US10251423B2", "US20050236006A1", "US4715387A", "US5893371A", "US20190387796A1"]

    #for i in range(len(patents)):
    #   index_patent_num(index_name, patents[i])

    #index_patent_num(index_name, "US7931716")
    #index_patent_num(index_name, "EP2144547B1")
    querrySummary()
    #print("--------- Keywords ---------")
    #for i in range(len(paths)):
    #    meow, num_keywords = keyword_counter(extract_text_from_pdf_url(url), keywords)
    #    print(num_keywords)
    
main()

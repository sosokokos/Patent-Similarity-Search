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
    results = querryDatabase(query_embedding, index_name)

    print("--------- Similarity Scores ---------")
    for i in range(len(results)):
        print("[" + results[i]['id'] + "] Score: " + str(results[i]['score']))

def patentQuerrySummary(patent_num):
    userInput_query = " ".join(keywords)
    query_embedding = get_openai_embeddings(userInput_query.lower())
    results = querryDatabaseFiltered(query_embedding, index_name, patent_num)

    #print("--------- Similarity Scores ---------")
    #for i in range(len(results)):
    #    print("[" + results[i]['id'] + "] Score: " + str(results[i]['score']))
    return results

def querryResponse(patentArray):
    userInput_query = " ".join(keywords)
    query_embedding = get_openai_embeddings(userInput_query.lower())

    results = []

    for i in range(len(patentArray)):
        results[i] = querryDatabaseFiltered(query_embedding, index_name, patentArray[i])

    print("--------- Similarity Scores ---------")
    for i in range(len(results)):
        print("[" + results[i]['id'] + "] Score: " + str(results[i]['score']))

def calculateAverage(input):
    if len(input) <= 0:
        print("CALCULATE AVERAGE IS BITCHING WE'RE DIVIDING BY: " + str(len(input)))
        print(input)
        return 0

    accumulator = 0
    for i in range(len(input)):
        accumulator += input[i]['score']
    return accumulator / len(input)

def calculateMin(response):
    currentMin = response[0]['score']
    for i in range(len(response)):
        if(response[i]['score'] < currentMin):
            currentMin = response[i]['score']
    return currentMin
    
def calculateMax(response):
    currentMax = response[0]['score']
    for i in range(len(response)):
        if(response[i]['score'] > currentMax):
            currentMax = response[i]['score']
    return currentMax

def generateFormattedResponses(patents):
    responseData = []
    for i in range(len(patents)):
        response = patentQuerrySummary(patents[i])
        if len(response) < 1:
            resultERROR = {
                "id": patents[i],
                "title": patentObj['title'],
                "average": 1,
                "min": 1,
                "max": 1,
                "description": "THIS IS AN INVALID OBJECT BECAUSE OF A DIVISION BY 0, check the validity and go fuck yourself",
                "link": "NO URL HERE BROTHA"
            }
            return resultERROR

        average = calculateAverage(response)
        min = calculateMin(response)
        max = calculateMax(response)
        patentObj = getPatent(patents[i])

        result = {
            "id": patents[i],
            "title": patentObj['title'],
            "average": average,
            "min": min,
            "max": max,
            "description": patentObj['description'],
            "link": patentObj['url']
        }
        responseData.append(result)
    return responseData

def printResults(patents):
    responses = generateFormattedResponses(patents)

    # Ensure responses is a list
    if isinstance(responses, dict):
        responses = [responses]

    sorted_responses = sorted(responses, key=lambda x: x['average'])
    
    for i in range(len(sorted_responses)):
        print("------------RESPONSE [" + str(i) + "]------------")
        print("Patent ID: [" + sorted_responses[i]['id'] + "]")
        print("Title: " + sorted_responses[i]['title'])
        print("Average: " + str(sorted_responses[i]['average']))
        print("Min: " + str(sorted_responses[i]['min']))
        print("Max: " + str(sorted_responses[i]['max']))
        print("Description: " + sorted_responses[i]['description'])
        print("link: " + sorted_responses[i]['link'])
    
def indexPatentsBulk(patents_list):
    for i in range(len(patents_list)):
       index_patent_num(index_name, patents_list[i])

def main():
    patents = ["US10244791B2", "US11399571B2", "US20210401061A1", "US10327479B2", "US20190087302A1",
               "US20190045837A1", "US10765145B2", "USD871665S1", "US11462307B2", "US20120214107A1", 
               "US10251423B2", "US20050236006A1", "US4715387A", "US5893371A", "US20190387796A1"]
    
    test_patents = ["US10513334B2", "US20190375505A1", "US10457379B2", "US4899766A", "US9095174B2", "US4941486A",
                    "US4066088A", "US8186360B2", "US11503970B2", "US11287817B1", "US20200158527A1"]
    
    all_patents = patents + test_patents
    
    #deleteIndex("test-index")
    #listIndexes()

    #initializeDatabase("test-index")
    #indexPatentsBulk(all_patents)
    
    
    printResults(all_patents)

        
    
main()

#TODO Keywords
#print("--------- Keywords ---------")
    #for i in range(len(paths)):
    #    meow, num_keywords = keyword_counter(extract_text_from_pdf_url(url), keywords)
    #    print(num_keywords)
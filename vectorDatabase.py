from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import requests
import pdfplumber
from io import BytesIO
import csv
import datetime


from webScraper import getPatent, get_similar_patents

keywords = ["smoking" , "smoking cessation" ,"smoking alternative", "battery" , "electronic cigarette" , "e-cigarette" , "vaporizer" ,
                "liquid" , "nicotine substitute" , "nicotine reduction" , "health" , "nicotine" , "device" , "vaporization" , "atomizer" , "quit",
                "algorithm" , "tracking" , "portable device" , "smart device" , "health improvement" , "health impact" , "usage data", "quit smoking" ,
                "feedback mechanism", "usage feedback", "data collection", "habit combating", "cartridge chamber", "liquid substance", "oral" ,
                "nicotine dependence", "coil", "vapor flow rate", "nicotine modulation", "feedback system", "user experience", "non-nicotine liquid"]

index_name = "test-index"

#### API KEYS ####
pc = Pinecone(api_key="Key")


#### Pinecone ####
def initializeDatabase(nameInput):
    if nameInput not in pc.list_indexes().names():
        pc.create_index(
        name=nameInput, 
        dimension=384,  # Adjusted to match embedding dimensions
        metric='euclidean',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        ))
        print("Succesfully Initialized : [" + nameInput + "]")
    else:
        print("Unsuccesfully Initialized : [ " + nameInput + " ] -> Index alrady exists, choose a different name")
        return

def deleteIndex(index_name):
    pc.delete_index(index_name)
    print("Succesfullty Deleted : [" + index_name + "]")

def deleteNamespace(index_name, namespace):
    index = pc.Index(index_name)
    index.delete(namespace=namespace, delete_all=True)
    print("Namespace : [" + namespace + "], succesfully cleared")

def listIndexes():
    indexes = pc.list_indexes()
    print("Indexes:", indexes)

def patentQuerrySummary(index_name, namespace, patent_num):
    userInput_query = " ".join(keywords)
    query_embedding = get_MiniLM_embeddings(userInput_query.lower())
    results = querryDatabaseFiltered(index_name, namespace, query_embedding, patent_num)
    return results

def querryDatabaseFiltered(index_name, namespace, query_embedding, patent_num):
     index = pc.Index(index_name)
     query_results = index.query(
         namespace=namespace,
         vector=query_embedding,
         top_k=5000,
         include_metadata=True,
         filter={
         "parentID": {"$eq": patent_num}
         },   
     )
    
     filtered_results = [{'id': match['id'], 'score': match['score']} for match in query_results['matches']]
     return filtered_results

def querryDatabase(query, index_name, namespace):
     index = pc.Index(index_name)
     query_results = index.query(
         namespace=namespace,
         vector=query,
         top_k=5000,
         include_metadata=True,  
     )
     return query_results

def upsert_patent(index_name, namespace, patent_num):
    if testInvalidURL(patent_num):
        return 0
    
    index = pc.Index(index_name)
    
    patent_text = extract_text_from_pdf_url(getPatent(patent_num)['url'])

    print("Inserting Patent : " + patent_num)
   
    chunk_embeddings = get_MiniLM_embeddings(patent_text)
   
    print("Embeddings : " + str(len(chunk_embeddings)))
    i = 0
    for embedding in chunk_embeddings:
        id = patent_num + " - [" + str(i) + "]"
        print("Upserting : " + id)
        index.upsert(
            vectors=[
                {
                    "id": id,
                    "values": embedding,
                    "metadata": {"parentID": patent_num}
                }
            ],
        namespace=namespace)
        i += 1
    print("Patent [" + patent_num + "] succesfully inserted into the database")

def upsert_patents_bulk(index, namespace, patent_num_array):
    j = 0
    arrLen = len(patent_num_array)
    for patent in patent_num_array:
        upsert_patent(index, namespace, patent)
        j += 1
    print("[" + str(j) + "/" + str(arrLen) + "] patents succesfully inserted into Index: " + index + " | Namespace: " + namespace)

def findPatentIDs2(input_index, namespace):
    index = pc.Index(input_index)
    response = []
    for ids in index.list(namespace=namespace):
        for id_str in ids:
            filteredID = id_str.replace(" - [0]", "")
            response.append(filteredID)
    return response

def findPatentIDs(input_index, namespace):
    index = pc.Index(input_index)
    response = set()  # Use a set to ensure unique patent IDs
    for ids in index.list(namespace=namespace):
        for id_str in ids:
            filteredID = id_str.split(" - [")[0]  # Remove the suffix starting from " - ["
            response.add(filteredID)  # Add the filtered ID to the set
    return list(response)

### Model ### 
def get_MiniLM_embeddings(query):
    model = SentenceTransformer('all-MiniLM-L6-v2')  # Smaller and faster model
    chunk_size = 6000  # Number of characters per chunk
    chunks = [query[i:i + chunk_size] for i in range(0, len(query), chunk_size)]
    embeddings = model.encode(chunks, convert_to_tensor=True)
    return embeddings.tolist()


### Keyword Counter and Helper functions ###
def keyword_counter(text, keywords):
    word_count = {}
    total_count = 0
    for keyword in keywords:
        count = text.lower().split().count(keyword.lower())
        word_count[keyword] = count
        total_count += count
    return word_count, total_count

def calculateAverage(input): #TODO Fix this
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

def testInvalidURL(patent_num):
    patent_data = getPatent(patent_num)
    url = patent_data.get('url')
    if not url:
        print("No URL provided in the patent data [" + patent_num + "]")
        return 1 
    return 0

def extract_text_from_pdf_url(url):
    # Fetch the PDF content from the URL
    #print(f"Fetching PDF from URL: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch PDF: {response.status_code}")
        return ''
    
    # Open the PDF from the content in memory
    with pdfplumber.open(BytesIO(response.content)) as pdf:
        text = ""
        for page in pdf.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text
            else:
                print(f"Failed to extract text from page: {page.page_number}")
        #print(f"Succesfully extracted text from: " + url)  
        return text


### Response and CSV ###
def printResults(index, namespace):
    patents = findPatentIDs(index, namespace)
    responses = compute_scores(index, namespace, patents)
    current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename="patent_results_" + str(current_timestamp) + ".csv"

    # Ensure responses is a list
    if isinstance(responses, dict):
        responses = [responses]

    sorted_responses = sorted(responses, key=lambda x: x['min'])

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Patent ID", "Title", "Average", "Min", "Max", "Keyword's count", "Link", "Description"])

        for response in sorted_responses:
            word_count, total_count = keyword_counter(extract_text_from_pdf_url(response['link']), keywords)
            writer.writerow([
                response['id'],
                response['title'],
                response['average'],
                response['min'],
                response['max'],
                total_count,
                response['link'],
                response['description']
            ])

    print(f"Results have been written to {filename}")
    
    for i in range(len(sorted_responses)):
        word_count, total_count = keyword_counter(extract_text_from_pdf_url(sorted_responses[i]['link']), keywords)
        print("------------RESPONSE [" + str(i) + "]------------")
        print("Patent ID: [" + sorted_responses[i]['id'] + "]")
        print("Title: " + sorted_responses[i]['title'])
        print("Average: " + str(sorted_responses[i]['average']))
        print("Min: " + str(sorted_responses[i]['min']))
        print("Max: " + str(sorted_responses[i]['max']))
        print("Keyword's count: " + str(total_count))
        print("link: " + sorted_responses[i]['link'])
        print("Description: " + sorted_responses[i]['description'])

def compute_scores(index_name,namespace,patents):
    responseData = []
    for i in range(len(patents)):
        response = patentQuerrySummary(index_name, namespace, patents[i])
        patentObj = getPatent(patents[i])
        if len(response) < 1:
            resultERROR = {
                "id": patents[i],
                "title": patentObj['title'],
                "average": 1,
                "min": 1,
                "max": 1,
                "description": "THIS IS AN INVALID OBJECT BECAUSE OF A DIVISION BY 0, check the validity",
                "link": "NO----URL"
            }
            print(resultERROR)
            continue

        average = calculateAverage(response)
        min = calculateMin(response)
        max = calculateMax(response)
        word_count, total_count = keyword_counter(extract_text_from_pdf_url(patentObj['url']), keywords)

        result = {
            "id": patents[i],
            "title": patentObj['title'],
            "average": average,
            "min": min,
            "max": max,
            "keywords": total_count,
            "description": patentObj['description'],
            "link": patentObj['url']
        }

        responseData.append(result)
    return responseData


def filter_test_batch(index_name="working-index", namespace="test-batch", destination_index = "storage-index", destination_namespace_pass = "target-patents", destination_namespace_fail = "tested-insufficent"):
    patents = findPatentIDs(index_name, namespace)
    responses = compute_scores(index_name, namespace, patents)

    target_list = findPatentIDs(destination_index, destination_namespace_pass)
    fail_list =  findPatentIDs(destination_index, destination_namespace_fail)

    storage_lists = target_list + fail_list 
    hitResponses = []

    for response in responses:
        if response["id"] not in storage_lists: 
            if response["min"] <= 1.2 and response["keywords"] >= 25:
                upsert_patent(destination_index, destination_namespace_pass, response["id"])
                print( "[" + response["id"] + "] PASSED [Keywords:" + str(response["keywords"]) + " | MinScore: " + str(response["min"]) + "], Storing in " + destination_index + "/" + destination_namespace_pass)
                hitResponses.append(response["id"])
            else:
                upsert_patent(destination_index,destination_namespace_fail, response["id"])
                print("[" + response["id"] + "] FAILED [Keywords:" + str(response["keywords"]) + " | MinScore: " + str(response["min"]) + "], Storing in " + destination_index + "/" + destination_namespace_fail)
        else:
            print("[" + response["id"] + "] Already exists in cloud, skipping.")

    deleteNamespace(index_name, namespace)

    similarPatentResponses = []

    for hit in hitResponses:
        simPatents = get_similar_patents(hit)
        for pat in simPatents:
            similarPatentResponses.append(pat)

    return similarPatentResponses

from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import requests
import pdfplumber
from io import BytesIO
import csv
import datetime


from webScraper import getPatent

keywords = ["smoking" , "smoking cessation" ,"smoking alternative", "battery" , "electronic cigarette" , "e-cigarette" , "vaporizer" ,
                "liquid" , "nicotine substitute" , "nicotine reduction" , "health" , "nicotine" , "device" , "vaporization" , "atomizer" , "quit",
                "algorithm" , "tracking" , "portable device" , "smart device" , "health improvement" , "health impact" , "usage data", "quit smoking" ,
                "feedback mechanism", "usage feedback", "data collection", "habit combating", "cartridge chamber", "liquid substance", "oral" ,
                "nicotine dependence", "coil", "vapor flow rate", "nicotine modulation", "feedback system", "user experience", "non-nicotine liquid"]

index_name = "test-index"

#### API KEYS ####
pc = Pinecone(api_key="639f6487-bd60-453c-b0f4-24f1537a1c2f")

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
        print("Vector database initialized")
    else:
        print("Index [ " + nameInput + " ] alrady exists")
        return

def deleteIndex(index_name):
    pc.delete_index("test-index")
    print("Succesfullty Deleted : [" + index_name + "]")

def listIndexes():
    indexes = pc.list_indexes()
    print("Indexes:", indexes)

def querryDatabaseFiltered(query, index_name, patent_num):
     index = pc.Index(index_name)
     query_results = index.query(
         namespace="ns1",
         vector=query,
         top_k=5000,
         include_metadata=True,
         filter={
         "parentID": {"$eq": patent_num}
         },   
     )
    
     filtered_results = [{'id': match['id'], 'score': match['score']} for match in query_results['matches']]
     return filtered_results

### Keyword Counter and Helper functions ###
def keyword_counter(text, keywords):
    word_count = {}
    total_count = 0
    for keyword in keywords:
        count = text.lower().split().count(keyword.lower())
        word_count[keyword] = count
        total_count += count
    return word_count, total_count
    
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

def testInvalidURL(patent_num):
    patent_data = getPatent(patent_num)
    url = patent_data.get('url')
    if not url:
        print("No URL provided in the patent data [" + patent_num + "]")
        return 1 
    return 0


### Response and CSV ###
def printResults(patents):
    responses = generateFormattedResponses(patents)
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
            print(resultERROR)
            continue

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
    
def patentQuerrySummary(patent_num):
    userInput_query = " ".join(keywords)
    query_embedding = get_MiniLM_embeddings(userInput_query.lower())
    results = querryDatabaseFiltered(query_embedding, index_name, patent_num)
    return results

def get_MiniLM_embeddings(query):
    model = SentenceTransformer('all-MiniLM-L6-v2')  # Smaller and faster model
    chunk_size = 1000  # Number of characters per chunk
    chunks = [query[i:i + chunk_size] for i in range(0, len(query), chunk_size)]
    embeddings = model.encode(chunks, convert_to_tensor=True)
    return embeddings.tolist()








def tester(patent_num):
    
    index = pc.Index("test-index")
    
    if testInvalidURL(patent_num):
        return 0
    
    pdf_text = extract_text_from_pdf_url(getPatent(patent_num)['url'])
    # Load pre-trained SentenceTransformer model
    model = SentenceTransformer('all-MiniLM-L6-v2')  # Smaller and faster model


    #TODO Make into function chunk_text(text) -> list[str]
    # Split the text into larger chunks (e.g., paragraphs or fixed-size chunks)
    chunk_size = 1000  # Number of characters per chunk
    chunks = [pdf_text[i:i + chunk_size] for i in range(0, len(pdf_text), chunk_size)]
    

    # Function to get embeddings for text chunks
    def get_embeddings(chunks):
        embeddings = model.encode(chunks, convert_to_tensor=True)
        return embeddings

    # Get embeddings for text chunks
    chunk_embeddings = get_embeddings(chunks)

    j = 0
    for embedding in chunk_embeddings:
        id = patent_num + " - [" + str(j) + "]"
        index.upsert(
            vectors=[
                {
                    "id": id,
                    "values": embedding,
                    "metadata": {"parentID": patent_num}
                }
            ],
        namespace="ns1")
        #print("Patent: " + patent_obj['title'] + " [" + patent_obj['id'] + "], was successfully inserted into index: [" + index_name + "] insertion - [" + str(j) + "]")
        j += 1
    print("Patent [" + patent_num + "] succesfully inserted into the database")
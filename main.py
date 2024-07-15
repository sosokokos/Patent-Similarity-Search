from pinecone import Pinecone, ServerlessSpec
from nltk.stem import PorterStemmer
from openai import OpenAI
import PyPDF2
import re
import os

from webScraper import scrape_google_patent


#### API KEYS ####
client = OpenAI(api_key="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")
pc = Pinecone(api_key="639f6487-bd60-453c-b0f4-24f1537a1c2f")

#### Text Pre-Processing ###
stop_words = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", 
    "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", 
    "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", 
    "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", 
    "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", 
    "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", 
    "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", 
    "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", 
    "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", 
    "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", 
    "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"
}

def remove_stopwords(text):
    words = text.split()
    filtered_text = ' '.join(word for word in words if word.lower() not in stop_words)
    return filtered_text

def stem_text(text): #NOT Stemming/Lemmatization
    stemmer = PorterStemmer()
    words = text.split()
    stemmed_text = ' '.join(stemmer.stem(word) for word in words)
    return stemmed_text

def split_text_into_chunks(text, max_tokens):
    words = text.split()
    chunks = []
    current_chunk = []
    current_tokens = 0

    for word in words:
        current_tokens += len(word.split())
        if current_tokens > max_tokens:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_tokens = len(word.split())
        else:
            current_chunk.append(word)
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def pdf_to_string(pdf_path):
    # Create a PDF file reader object
    pdf_reader = PyPDF2.PdfReader(pdf_path)
    # Initialize an empty string to store the text
    pdf_text = ""
    # Iterate through all the pages in the PDF
    for page_num in range(len(pdf_reader.pages)):
        # Get the page object
        page = pdf_reader.pages[page_num]
        # Extract text from the page and append it to the pdf_text string
        pdf_text += page.extract_text()

    # Clean the string response of excessive whitespace
    cleaned_text = re.sub(r'\s+', ' ', pdf_text).strip()
    # Make all the characters lowercase
   # cleaned_text = pdf_text.lower()
    # Remove punctuation
    #cleaned_text = cleaned_text.translate(str.maketrans('', '', string.punctuation))
    # Remove Stopwords that are stated above
    #response = remove_stopwords(cleaned_text)
    return cleaned_text

### Keyword Counter ###

def keyword_counter(text, keywords):
    word_count = {}
    for keyword in keywords:
        count = text.lower().split().count(keyword.lower())
        word_count[keyword] = count
    return word_count

def keyword_counter(text, keywords):
    word_count = {}
    total_count = 0
    for keyword in keywords:
        count = text.lower().split().count(keyword.lower())
        word_count[keyword] = count
        total_count += count
    return word_count, total_count

#### Embeddings ####
def get_openai_embeddings(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"  
    )
    return response.data[0].embedding # CHECK! Potentially error prone

#### Pinecone ####
def initializeDatabase(nameInput):
    if nameInput not in pc.list_indexes().names():
        pc.create_index(
        name=nameInput, 
        dimension=1536,  # Adjusted to match OpenAI embedding dimensions
        metric='euclidean',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        ))
        print("Vector database initialized")
    else:
        print("Index [ " + nameInput + " ] alrady exists")
        return
    
def index_pdf_in_pinecone(pdf_text, index_name, id):
    index = pc.Index(index_name)
    chunks = split_text_into_chunks(pdf_text, 5000)
    embeddings = []

    i = 0
    for chunk in chunks:
        embeddings.append(get_openai_embeddings(chunk))
        print("Chunk #" + str(i) + " created")
        i += 1

    for embedding in embeddings:
        id = id + "I"
        index.upsert(
            vectors=[
                {"id": id, "values": embedding}
            ],
        namespace="ns1")
        print("vectorID: [" + id + "], was successfully inserted into index: [" + index_name + "]")

def querryDatabase(query, index_name):
    index = pc.Index(index_name)
    query_results = index.query(
        namespace="ns1",
        vector=query,
        top_k=500,
        include_values=True
    )
    
    filtered_results = [{'id': match['id'], 'score': match['score']} for match in query_results['matches']]
    return filtered_results

def start(): 
    keywords = ["smoking" , "smoking cessation" ,"smoking alternative", "battery" , "electronic cigarette" , "e-cigarette" , "vaporizer" ,
                "liquid" , "nicotine substitute" , "nicotine reduction" , "health" , "nicotine" , "device" , "vaporization" , "atomizer" , "quit",
                "algorithm" , "tracking" , "portable device" , "smart device" , "health improvement" , "health impact" , "usage data", "quit smoking" ,
                "feedback mechanism", "usage feedback", "data collection", "habit combating", "cartridge chamber", "liquid substance", "oral" ,
                "nicotine dependence", "coil", "vapor flow rate", "nicotine modulation", "feedback system", "user experience", "non-nicotine liquid"]
    
    paths = [ "/Users/danielsurina/Desktop/Nuevotine/Data/CN114343254B-ENGLISH.pdf", 
              "/Users/danielsurina/Desktop/Nuevotine/Data/CN114343255B-ENGLISH.pdf",
              "/Users/danielsurina/Desktop/Nuevotine/Data/US4715387.pdf",
              "/Users/danielsurina/Desktop/Nuevotine/Data/US5893371.pdf",
              "/Users/danielsurina/Desktop/Nuevotine/Data/US10244791.pdf",
              "/Users/danielsurina/Desktop/Nuevotine/Data/US10251423.pdf",
              "/Users/danielsurina/Desktop/Nuevotine/Data/US10327479.pdf",
              "/Users/danielsurina/Desktop/Nuevotine/Data/emptyData.pdf",
              "/Users/danielsurina/Desktop/Nuevotine/Data/article1.pdf",
              "/Users/danielsurina/Desktop/Nuevotine/Data/vacuumCleaner.pdf",
              "/Users/danielsurina/Desktop/Nuevotine/Data/hookah.pdf",
              "/Users/danielsurina/Desktop/Nuevotine/Data/hairBrush.pdf",
              "/Users/danielsurina/Desktop/Nuevotine/Data/smokeDetector.pdf",
              "/Users/danielsurina/Desktop/Nuevotine/Data/particleMonitor.pdf",
              "/Users/danielsurina/Desktop/Nuevotine/Data/cigaretteTest.pdf"]
    
    filenames = [os.path.basename(path) for path in paths]
    index_name = "test-index"

    #for i in range(len(paths)):
    #    index_pdf_in_pinecone(pdf_to_string(paths[i]), index_name, filenames[i])
 
    userInput_query = " ".join(keywords)
    query_embedding = get_openai_embeddings(userInput_query.lower())
    results = querryDatabase(query_embedding, index_name)

    print("--------- Similarity Scores ---------")
    for i in range(len(results)):
        print("[" + results[i]['id'] + "] Score: " + str(results[i]['score']))
    
    print("--------- Keywords ---------")
    for i in range(len(paths)):
        meow, num_keywords = keyword_counter(pdf_to_string(paths[i]), keywords)
        print("[" + filenames[i] + "]: " + str(num_keywords))

#TODO wash my armpits

def main():
    # Listing  and Deleting of indexes
    #indexes = pc.list_indexes()
    #print("Indexes:", indexes)
    #pc.delete_index("test-index")

    #initializeDatabase("test-index")
    #start()
    scrape_google_patent("US11825522B2")


    

main()
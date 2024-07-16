from pinecone import Pinecone, ServerlessSpec
from nltk.stem import PorterStemmer
from openai import OpenAI
import PyPDF2
import re
import os
import requests
import pdfplumber
from io import BytesIO

import fitz

from webScraper import getPatent

#### API KEYS ####
client = OpenAI(api_key="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")
pc = Pinecone(api_key="639f6487-bd60-453c-b0f4-24f1537a1c2f")


#### Text Pre-Processing ###
def remove_stopwords(text):
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
    
    words = text.split()
    filtered_text = ' '.join(word for word in words if word.lower() not in stop_words)
    return filtered_text

def stem_text(text): #NOT Stemming/Lemmatization
    stemmer = PorterStemmer()
    words = text.split()
    stemmed_text = ' '.join(stemmer.stem(word) for word in words)
    return stemmed_text

import openai
import tiktoken
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Tokenizer setup
tokenizer = tiktoken.get_encoding("p50k_base")

def split_text_into_chunks(text, max_tokens=6000):
    tokens = tokenizer.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i + max_tokens]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
    logging.info(f"Created {len(chunks)} chunks")
    for idx, chunk in enumerate(chunks):
        logging.info(f"Chunk {idx} length (tokens): {len(tokenizer.encode(chunk))}")
    return chunks


#TODO FIX Pre-Processing of data
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
    #cleaned_text = pdf_text.lower()
    # Remove punctuation
    #cleaned_text = cleaned_text.translate(str.maketrans('', '', string.punctuation))
    # Remove Stopwords that are stated above
    #response = remove_stopwords(cleaned_text)
    return cleaned_text


### Keyword Counter ###
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
    return response.data[0].embedding #TODO CHECK! Potentially error prone

#### Pinecone ####
def initializeDatabase(nameInput):
    if nameInput not in pc.list_indexes().names():
        pc.create_index(
        name=nameInput, 
        dimension=1536,  # Adjusted to match embedding dimensions
        metric='euclidean',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        ))
        print("Vector database initialized")
    else:
        print("Index [ " + nameInput + " ] alrady exists")
        return

#TODO REFORMAT THE for loop with embeddings so it creates nice names
def index_text_pinecone(pdf_text, index_name, patent_num):
    index = pc.Index(index_name)

    # Clean the string response of excessive whitespace
    cleaned_text = re.sub(r'\s+', ' ', pdf_text).strip()
    # Make all the characters lowercase
    cleaned_text_lower = cleaned_text.lower()
    # Remove punctuation
    #cleaned_text = cleaned_text.translate(str.maketrans('', '', string.punctuation))
    # Remove Stopwords that are stated above
    #response = remove_stopwords(cleaned_text_lower)

    chunks = split_text_into_chunks(cleaned_text_lower)
    embeddings = []

    i = 0
    for chunk in chunks:
        embeddings.append(get_openai_embeddings(chunk))
        print("Chunk #" + str(i) + " created")
        i += 1

    patent_obj = getPatent(patent_num)

    j = 0
    for embedding in embeddings:
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
        print("Patent: " +patent_obj['title'] + " [" + patent_obj['id'] + "], was successfully inserted into index: [" + index_name + "] insertion - [" + j + "]")
        j += 1

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

def querryDatabaseFiltered(query, index_name, patent_num):
    index = pc.Index(index_name)
    query_results = index.query(
        namespace="ns1",
        vector=query,
        top_k=500,
        include_metadata=True,
        filter={
        "parentID": {"$eq": patent_num}
        },   
    )
    
    filtered_results = [{'id': match['id'], 'score': match['score']} for match in query_results['matches']]
    return filtered_results

def querryDatabase2(query, index_name):
    index = pc.Index(index_name)
    query_results = index.query(
        namespace="ns1",
        vector=query,
        top_k=500,
        include_values=True
    )
    
    filtered_results = [{'id': match['id'], 'score': match['score']} for match in query_results['matches']]
    return filtered_results

def extract_text_from_pdf_url(url):
    # Fetch the PDF content from the URL
    print(f"Fetching PDF from URL: {url}")
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
        print(f"Succesfully extracted text from: " + url)  
        return text

def index_patent_num(index, patent_num):
    localIndex = index
    patentObject = getPatent(patent_num)
    print("Indexing Patent: [" + patentObject["title"]+ "], with ID: " + patentObject["id"])

    link = patentObject['url']
    text = extract_text_from_pdf_url(link)

    index_text_pinecone(text, localIndex, patentObject['id'])
    print("Patent [" + patentObject['id'] + "] was succesfully inserted")

def deleteIndex(index_name):
    pc.delete_index("test-index")
    print("Succesfullty Deleted : [" + index_name + "]")

def listIndexes():
    indexes = pc.list_indexes()
    print("Indexes:", indexes)
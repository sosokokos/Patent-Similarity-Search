import requests
from bs4 import BeautifulSoup

def getPatent(patent_number):
    url = f'https://patents.google.com/patent/{patent_number}'
    response = requests.get(url)
    if response.status_code != 200:
        print(f'Failed to retrieve the page. Status code: {response.status_code}')
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extracting the relevant information
    full_title = soup.find('title').text.strip()
    description = soup.find('meta', {'name': 'DC.description'}).get('content', '').strip()
    
    # Split title into patent title and number
    patent_number = patent_number
    # Extract the patent title by removing the patent number and 'Google Patents' from the full title
    if " - " in full_title:
        parts = full_title.split(" - ")
        patent_title = parts[1].strip() if len(parts) > 1 else full_title.strip()
    else:
        patent_title = full_title
    
    # Find the link with text "Download PDF"
    pdf_link_tag = soup.find('a', string="Download PDF")
    pdf_link = pdf_link_tag['href'] if pdf_link_tag else 'No PDF link available' 
    
    response = {
        "title" : patent_title,
        "id" : patent_number,
        "description" : description,
        "url" : pdf_link
    }

    return response

import requests
from bs4 import BeautifulSoup

def get_patent_numbers(patent_id):
    url = f"https://patents.google.com/patent/{patent_id}/similar"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    patent_numbers = []
    for link in soup.find_all('a', href=True):
        if link['href'].startswith('/patent/'):
            patent_number = link['href'].split('/')[2]
            if patent_number not in patent_numbers:
                patent_numbers.append(patent_number)
    
    return patent_numbers

#
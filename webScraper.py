import requests
from bs4 import BeautifulSoup

def scrape_google_patent(patent_number):
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
    
    print("Title: " + patent_title)
    print("Patent Number: " + patent_number)
    print("Description: " + description)
    print("PDF Link: " + pdf_link)
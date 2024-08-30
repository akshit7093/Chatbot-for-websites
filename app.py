#Web scraps the data 
import pandas as pd
import ollama
from ollama import generate
import spacy
import requests
from bs4 import BeautifulSoup
import json

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

def scrape_and_process_doj_website():
    url = "https://doj.gov.in/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract all text content
    all_text = soup.get_text(separator=' ', strip=True)
    
    # Process text with spaCy
    doc = nlp(all_text)
    
    # Extract and structure information
    structured_data = []
    for sent in doc.sents:
        sentence_data = {
            'text': sent.text,
            'entities': [{'text': ent.text, 'label': ent.label_} for ent in sent.ents],
            'key_phrases': [chunk.text for chunk in sent.noun_chunks],
        }
        structured_data.append(sentence_data)
    
    # Extract links and their text
    links = [{'text': a.text.strip(), 'href': a['href']} for a in soup.find_all('a', href=True) if a.text.strip()]
    
    # Combine all extracted data
    website_data = {
        'structured_content': structured_data,
        'links': links,
    }
    
    return website_data

# Scrape and process the website
doj_content = scrape_and_process_doj_website()

# Save the content to a file
def save_content_to_file(content, filename="doj_content.json"):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(content, file, ensure_ascii=False, indent=4)
    print(f"Content saved to {filename}")

# Save the processed content
save_content_to_file(doj_content)

# Function to generate response using Ollama
def generate_response(query):
    context = json.dumps(doj_content, ensure_ascii=False)
    prompt = f"Based on the following context about the Department of Justice website:\n\n{context}\n\nAnswer this question: {query}"
    response = generate(model="llama3.1", prompt=prompt)
    return response['response']

# Example usage
question = "what's new "
answer = generate_response(question)
print(f"Q: {question}\nA: {answer}")
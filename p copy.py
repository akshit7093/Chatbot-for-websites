#Important
import pandas as pd
import ollama
from ollama import generate
import spacy
import requests
from bs4 import BeautifulSoup
import json
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import nltk

# Download necessary NLTK data
nltk.download('stopwords')
nltk.download('wordnet')

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

def scrape_and_process_doj_website():
    # Scrape the website
    url = "https://doj.gov.in/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract relevant content
    content = []
    for paragraph in soup.find_all('p'):
        content.append(paragraph.text.strip())
    
    return content

def save_extracted_data_to_txt(content, filename="extracted_data.txt"):
    with open(filename, "w") as file:
        for item in content:
            file.write(f"{item}\n")

def load_and_process_data(filename="extracted_data.txt"):
    # Read the data from the text file
    with open(filename, "r") as file:
        content = file.readlines()
    
    # Remove any leading/trailing whitespace characters
    content = [line.strip() for line in content if line.strip()]
    
    # Preprocess content using spaCy and OLLAMA
    lemmatizer = WordNetLemmatizer()
    processed_data = []
    
    for item in content:
        doc = nlp(item)
        
        # Tokenize and lemmatize
        tokens = [lemmatizer.lemmatize(token.lemma_) for token in doc if not token.is_stop]
        processed_item = " ".join(tokens)
        
        processed_data.append(processed_item)
    
    # Save processed data to JSON file
    with open("processed_data.json", "w") as file:
        json.dump(processed_data, file, indent=4)
    
    return processed_data

def generate_response(query, processed_content):
    # Join the processed content into a single string
    context = "\n".join(processed_content)
    
    # Modify the prompt to be more suitable for a DOJ chatbot
    prompt = f"""
    You are an official representative of the Department of Justice of India. Use the following context to answer questions:

    {context}

    Analyze the provided information and answer the following question:
    {query}

    Provide a response that is clear, concise, and accurate. If the answer is not directly in the context, use your knowledge to provide a relevant response.

    Format your response as if you were communicating with a member of the public.
    """
    
    # Use the llama3.1 model to generate a response
    response = generate(model="llama3.1", prompt=prompt)
    
    # Modify the response to be more suitable for a DOJ chatbot
    response_text = response['response']
    response_text = response_text.replace("The Department of Justice", "DOJ").replace("the website", "our website")
    response_text = response_text.replace("you can visit", "visit our website at").replace("for more information", "on our website")
    
    return response_text

if __name__ == "__main__":
    # Scrape and process the website
    doj_content = scrape_and_process_doj_website()
    
    # Save extracted data to a text file
    save_extracted_data_to_txt(doj_content)
    
    # Load and process data from the text file
    processed_content = load_and_process_data()
    
    # Interactive Q&A loop
    print("Ask questions about the Department of Justice website (type 'exit' to quit):")
    while True:
        question = input("Q: ")
        if question.lower() == 'exit':
            break
        answer = generate_response(question, processed_content)
        print(f"A: {answer}\n")

#ask ques from the txt file
import pandas as pd
import ollama
from ollama import generate
import spacy
import requests
from bs4 import BeautifulSoup

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Function to scrape content from the website
def scrape_doj_website():
    url = "https://doj.gov.in/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract relevant information (modify as needed)
    content = ""
    for paragraph in soup.find_all('p'):
        content += paragraph.text + "\n"
    
    return content

# Load the website content
doj_content = scrape_doj_website()

def preprocess_text(text):
    doc = nlp(text)
    return " ".join([token.lemma_ for token in doc if not token.is_stop and not token.is_punct])

def answer_question(question):
    # Preprocess the question
    processed_question = preprocess_text(question)
    
    # Prepare the context
    context = f"Department of Justice, Government of India Website Content:\n\n{doj_content}"
    
    # Prepare the prompt
    prompt = f"""Based on the following content from the Department of Justice, Government of India website, please answer this question:

Content:
{context}

Question: {processed_question}

Answer:"""

    # Generate the answer using Llama 3.1
    response = generate(model='llama3.1', prompt=prompt)
    
    return response['response']

# Chatbot loop
print("Welcome to the Department of Justice, Government of India Chatbot!")
print("Ask me anything about the Department of Justice or type 'exit' to quit.")

while True:
    user_question = input("\nYou: ")
    if user_question.lower() == 'exit':
        print("Thank you for using the DOJ Chatbot. Goodbye!")
        break
    answer = answer_question(user_question)
    print(f"\nDOJ Chatbot: {answer}")

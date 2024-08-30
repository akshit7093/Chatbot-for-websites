#Important
import random
import pandas as pd
import ollama
from ollama import generate
import spacy
import requests
from bs4 import BeautifulSoup
import json
import nltk
from collections import deque
from urllib.parse import urljoin, urlparse
from nltk.stem import WordNetLemmatizer
# Download necessary NLTK data
nltk.download('stopwords')
nltk.download('wordnet')

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

def scrape_and_process_doj_website():
    base_url = "https://doj.gov.in/"
    queue = deque([base_url])
    visited = set()
    structured_content = []

    while queue:
        url = queue.popleft()
        if url in visited:
            continue

        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            visited.add(url)

            # Use NLP to identify headings and their associated content
            page_content = {}
            page_content['link'] = url
            page_content['content'] = []

            current_section = {"heading": None, "text": ""}

            for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
                text = element.get_text(strip=True)
                if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    # Save previous section if it exists
                    if current_section['heading'] or current_section['text']:
                        page_content['content'].append(current_section)
                    # Start a new section
                    current_section = {"heading": text, "text": ""}
                elif element.name == 'p':
                    # Add paragraph text to the current section
                    current_section['text'] += text + " "

            # Save the last section
            if current_section['heading'] or current_section['text']:
                page_content['content'].append(current_section)

            if page_content['content']:
                structured_content.append(page_content)
                print(f"Scraped content from: {url}")

            # Find all links on the current page
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                
                # Only add URLs from the same domain
                if urlparse(full_url).netloc == urlparse(base_url).netloc and full_url not in visited:
                    queue.append(full_url)

        except Exception as e:
            print(f"Error scraping {url}: {e}")

    return structured_content

def save_extracted_data_to_json(content, filename="extracted_data.json"):
    if not content:
        print("No content to save.")
        return
    
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(content, file, indent=4, ensure_ascii=False)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving data to {filename}: {e}")

# def load_and_process_data(filename="processed_data.json"):
#     # Load the data from the JSON file
#     try:
#         with open(filename, "r", encoding="utf-8") as file:
#             content = json.load(file)
#         print(f"Data successfully loaded from {filename}")
#     except FileNotFoundError:
#         print(f"{filename} not found.")
#         return None
    
#     # Preprocess content using spaCy and Ollama
#     lemmatizer = WordNetLemmatizer()
    
#     for page in content:
#         for section in page['content']:
#             doc = nlp(section['text'])
            
#             # Tokenize and lemmatize
#             tokens = [lemmatizer.lemmatize(token.lemma_) for token in doc if not token.is_stop]
#             processed_text = " ".join(tokens)
            
#             section['processed_text'] = processed_text

#     # Save processed data back to JSON file
#     try:
#         with open("processed_data.json", "w", encoding="utf-8") as file:
#             json.dump(content, file, indent=4, ensure_ascii=False)
#         print("Processed data successfully saved to processed_data.json")
#     except Exception as e:
#         print(f"Error saving processed data: {e}")
    
#     return content

def load_and_process_data(filename="ollama_processed_data.json"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            content = json.load(file)
        print(f"Data successfully loaded from {filename}")
    except FileNotFoundError:
        print(f"{filename} not found.")
        return None
    
    lemmatizer = WordNetLemmatizer()
    
    for page in content:
        # Process the URL if it exists
        if 'url' in page:
            parsed_url = urlparse(page['url'])
            page['processed_url'] = parsed_url.netloc + parsed_url.path
        else:
            page['processed_url'] = "No URL provided"

        # Process the summary
        if 'summary' in page and page['summary']:  # Add check for None
            doc = nlp(page['summary'])
            tokens = [lemmatizer.lemmatize(token.lemma_) for token in doc if not token.is_stop]
            page['processed_summary'] = " ".join(tokens)
        else:
            page['processed_summary'] = "No summary provided"
        
        # Process main topics
        if 'main_topics' in page:
            processed_topics = []
            for topic in page['main_topics']:
                if topic:  # Add check for None
                    doc = nlp(topic)
                    tokens = [lemmatizer.lemmatize(token.lemma_) for token in doc if not token.is_stop]
                    processed_topics.append(" ".join(tokens))
                else:
                    processed_topics.append("No topic provided")
            page['processed_topics'] = processed_topics
        else:
            page['processed_topics'] = []

    try:
        with open("processed_data.json", "w", encoding="utf-8") as file:
            json.dump(content, file, indent=4, ensure_ascii=False)
        print("Processed data successfully saved to processed_data.json")
    except Exception as e:
        print(f"Error saving processed data: {e}")
    
    return content

from fuzzywuzzy import fuzz

def generate_response(query, processed_content):
    # Load the JSON data
    with open('ollama_processed_data.json', 'r') as f:
        json_data = json.load(f)

    # Extract key terms from the query for matching
    doc = nlp(query)
    query_tokens = {token.lemma_ for token in doc if not token.is_stop}

    # Search for relevant content in the JSON data
    relevant_pages = []
    for page in json_data:
        title = page.get('title', '')
        summary = page.get('summary', '')
        main_topics = page.get('main_topics', [])
        
        # Calculate similarity scores
        title_score = fuzz.token_set_ratio(query, title)
        summary_score = fuzz.token_set_ratio(query, summary)
        topics_score = max([fuzz.token_set_ratio(query, topic) for topic in main_topics]) if main_topics else 0
        
        # If any score is above a threshold, consider it relevant
        if max(title_score, summary_score, topics_score) > 60:
            relevant_pages.append(page)

    # Sort relevant pages by similarity score
    relevant_pages.sort(key=lambda x: fuzz.token_set_ratio(query, x['title']), reverse=True)

    # Create the context from the relevant pages
    context = ""
    for page in relevant_pages[:3]:  # Limit to top 3 most relevant pages
        title = page.get('title', 'No title available')
        summary = page.get('summary', 'No summary available')
        main_topics = page.get('main_topics', [])
        url = page.get('url', 'No URL available')

        context += f"Title: {title}\n"
        context += f"Summary: {summary}\n"
        context += "Main Topics: " + ", ".join(main_topics) + "\n"
        context += f"URL: {url}\n\n"

    # Create a prompt using the collected context and query
    prompt = f"""
    You are an official, professional, and helpful chatbot for the Department of Justice website. Use the following context to answer the question:

    {context}

    Question: {query}

    Provide a clear, accurate, and detailed response. Include the relevant URL in the response.
    Format your response in a friendly, conversational tone, as if you were a chatbot on the DOJ website.
    """
    
    # Use the llama3.1 model to generate a response (replace with your actual model function)
    response = generate(model="llama3.1", prompt=prompt)
    
    response_text = response.get('response', 'I apologize, but I am unable to generate a response at the moment.')
    
    # Add a friendly opening and closing
    opening = "Hello! Thank you for your question. "
    closing = " Is there anything else I can help you with?"
    
    response_text = opening + response_text + closing
    
    return response_text


if __name__ == "__main__":

    # Scrape and process the website (now includes crawling and NLP-based content structuring)
    # doj_content = scrape_and_process_doj_website()
    
    # # Save extracted data to a JSON file
    # save_extracted_data_to_json(doj_content)
    
    # Load and process data from the JSON file
    processed_content = load_and_process_data()
    
    # Interactive Q&A loop
    print("Ask questions about the Department of Justice website (type 'exit' to quit):")
    while True:
        question = input("Q: ")
        if question.lower() == 'exit':
            break
        if processed_content:
            answer = generate_response(question, processed_content)
            print(f"A: {answer}\n")
        else:
            print("No processed content available. Please check the data extraction and processing steps.")

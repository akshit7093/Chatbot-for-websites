
import random
import pandas as pd
import ollama
from ollama import generate
import spacy
import requests
# from bs4 import BeautifulSoup
import tensorflow as tf
import json
import nltk
from collections import deque
from urllib.parse import urljoin, urlparse
from nltk.stem import WordNetLemmatizer
import os
from datetime import datetime
spacy.cli.download("en_core_web_sm")
nltk.download('stopwords')
nltk.download('wordnet')
# Load spaCy model
nlp = spacy.load("en_core_web_sm")
with tf.device('/GPU:0'):
    def authenticate_user():
        while True:
            choice = input("Enter 'login' or 'signup': ").lower()
            if choice == 'login':
                username = input("Enter your username: ")
                password = input("Enter your password: ")
                if check_credentials(username, password):
                    return username
                else:
                    print("Invalid credentials. Please try again.")
            elif choice == 'signup':
                username = input("Choose a username: ")
                password = input("Choose a password: ")
                if create_user(username, password):
                    return username
                else:
                    print("Username already exists. Please try again.")
            else:
                print("Invalid choice. Please enter 'login' or 'signup'.")

    def check_credentials(username, password):
        if os.path.exists('users.json'):
            with open('users.json', 'r') as f:
                users = json.load(f)
                return users.get(username) == password
        return False

    def create_user(username, password):
        if os.path.exists('users.json'):
            with open('users.json', 'r') as f:
                users = json.load(f)
        else:
            users = {}
        
        if username in users:
            return False
        
        users[username] = password
        with open('users.json', 'w') as f:
            json.dump(users, f)
        return True

    def save_conversation(username, question, answer):
        if os.path.exists('conversations.json'):
            with open('conversations.json', 'r') as f:
                conversations = json.load(f)
        else:
            conversations = {}
        
        if username not in conversations:
            conversations[username] = []
        
        conversations[username].append({
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'answer': answer
        })
        
        with open('conversations.json', 'w') as f:
            json.dump(conversations, f)

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


        
        return content

    from fuzzywuzzy import fuzz
    import tensorflow as tf
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
        if os.path.exists('conversations.json'):
            with open('conversations.json', 'r') as f:
                conversations = json.load(f)
                if username in conversations:
                    user_history = conversations[username][-5:]  # Get last 5 conversations
                    for conv in user_history:
                        context += f"Previous Q: {conv['question']}\n"
                        context += f"Previous A: {conv['answer']}\n\n"

        # Create a prompt using the collected context and query
        # with tf.device('/GPU:0'):
            # Create a prompt using the collected context and query


       
        prompt = f"""
    You are an official representative of the Department of Justice of India. Use the following context to answer questions:

    {context}

    Analyze the provided information and answer the following question:
    {query}

    Provide a response that is clear, concise, and accurate. If the answer is not directly in the context, use your knowledge to provide a relevant response.

    Format your response as if you were communicating with a member of the public.
    """

            # Use the llama3.1 model to generate a response (replace with your actual model function)
        response = generate(model="mistral:7b", prompt=prompt)
        
        response_text = response.get('response', 'I apologize, but I am unable to generate a response at the moment.')
        
        # Add a friendly opening and closing
        opening = "Hello! Thank you for your question. "
        closing = " Is there anything else I can help you with?"
        
        response_text = opening + response_text + closing
        save_conversation(username, query, response_text)
        
        return response_text


    if __name__ == "__main__":

        username = authenticate_user()
        print(f"Welcome, {username}!")

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




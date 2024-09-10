import random
import pandas as pd
import ollama
from ollama import generate
import spacy
import requests
import torch
import torch.cuda
from bs4 import BeautifulSoup
import json
import nltk
from collections import deque
from urllib.parse import urljoin, urlparse
from nltk.stem import WordNetLemmatizer
import os
from datetime import datetime
from fuzzywuzzy import fuzz
import speech_recognition as sr
import pyttsx3
import time 
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


# Download necessary NLTK data
nltk.download('stopwords')
nltk.download('wordnet')

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Initialize speech recognition and text-to-speech engines

recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Set up GPU device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")


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
        if 'url' in page:
            parsed_url = urlparse(page['url'])
            page['processed_url'] = parsed_url.netloc + parsed_url.path
        else:
            page['processed_url'] = "No URL provided"

        if 'summary' in page and page['summary']:
            doc = nlp(page['summary'])
            tokens = [lemmatizer.lemmatize(token.lemma_) for token in doc if not token.is_stop]
            page['processed_summary'] = " ".join(tokens)
        else:
            page['processed_summary'] = "No summary provided"
        
        if 'main_topics' in page:
            processed_topics = []
            for topic in page['main_topics']:
                if topic:
                    doc = nlp(topic)
                    tokens = [lemmatizer.lemmatize(token.lemma_) for token in doc if not token.is_stop]
                    processed_topics.append(" ".join(tokens))
                else:
                    processed_topics.append("No topic provided")
            page['processed_topics'] = processed_topics
        else:
            page['processed_topics'] = []
    
    return content


def generate_response(query, processed_content):
    with open('ollama_processed_data.json', 'r') as f:
        json_data = json.load(f)

    doc = nlp(query)
    query_tokens = {token.lemma_ for token in doc if not token.is_stop}

    relevant_pages = []
    for page in json_data:
        title = page.get('title', '')
        summary = page.get('summary', '')
        main_topics = page.get('main_topics', [])
        
        title_score = fuzz.token_set_ratio(query, title)
        summary_score = fuzz.token_set_ratio(query, summary)
        topics_score = max([fuzz.token_set_ratio(query, topic) for topic in main_topics]) if main_topics else 0
        
        if max(title_score, summary_score, topics_score) > 60:
            relevant_pages.append(page)

    relevant_pages.sort(key=lambda x: fuzz.token_set_ratio(query, x['title']), reverse=True)

    context = ""
    for page in relevant_pages[:3]:
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
                user_history = conversations[username][-5:]
                for conv in user_history:
                    context += f"Previous Q: {conv['question']}\n"
                    context += f"Previous A: {conv['answer']}\n\n"

    prompt = f"""
    You are a official helpful AI voice assistant for the Department of Justice website. Use the following context to answer the question:

    {context}

    Question: {query}

    Strictly respond in the same language as Question 

    Please respond in a very natural, conversational tone. Use professional language to sound more human-like. Vary your sentence structure and length.

    Keep the response concise and easy to understand. Aim for a response that sounds like it's coming from a knowledgeable formal AI system.
    """

    response = generate(model="llama3.1", prompt=prompt)
    
    response_text = response.get('response', 'I apologize, but I am unable to generate a response at the moment.')
    
    save_conversation(username, query, response_text)
    
    return response_text


def listen_for_input():
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
    
    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I couldn't understand that.")
        return None
    except sr.RequestError:
        print("Sorry, there was an error with the speech recognition service.")
        return None

def speak_response(text):
    engine = pyttsx3.init()
    
    # Set properties for a more natural voice
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)  # Use a female voice (adjust index if needed)
    engine.setProperty('volume', 0.8)  # Adjust volume

    # Base rate (words per minute)
    base_rate = 175

    sentences = text.split('.')
    for sentence in sentences:
        if sentence.strip():
            # Vary rate slightly for each sentence
            rate_variation = random.uniform(-25, 25)
            current_rate = base_rate + rate_variation
            engine.setProperty('rate', current_rate)

            # Add filler words and pauses
            filler_words = ["Um", "Ah", "Well", "You see", "Let's see"]
            if random.random() < 0.2:  # 20% chance to add a filler word
                filler = random.choice(filler_words)
                sentence = f"{filler}, {sentence}"

            engine.say(sentence.strip())
            engine.runAndWait()
            
            # Add natural pauses between sentences
            pause_duration = random.uniform(0.3, 0.7)
            time.sleep(pause_duration)

    # Reset rate to default after speaking
    engine.setProperty('rate', base_rate)


if __name__ == "__main__":
    username = authenticate_user()
    print(f"Welcome, {username}!")

    processed_content = load_and_process_data()
    
    greetings = [
        f"Hey there, {username}! Great to have you on board.",
        f"Welcome, {username}! How can I help you today?",
        f"Hi {username}! I'm all ears. What would you like to know about the Department of Justice?"
    ]
    speak_response(random.choice(greetings))
    
    print("Ask me anything about the Department of Justice website. Just say 'goodbye' when you're done.")
    speak_response("Feel free to ask me anything about the Department of Justice website. ... Just say 'goodbye' when you're done.")
    
    while True:
        question = listen_for_input()
        if question:
            if question.lower() in ['goodbye', 'bye', 'exit']:
                break
            if processed_content:
                answer = generate_response(question, processed_content)
                print(f"AI: {answer}\n")
                speak_response(answer)
            else:
                print("Oops! I don't have any information to work with at the moment.")
                speak_response("Oops! ... I don't have any information to work with at the moment. ... Could you try again later?")

    farewells = [
        "It was great chatting with you! Have an awesome day ahead.",
        "Thanks for stopping by. Don't hesitate to come back if you need anything else!",
        "Always a pleasure helping you out. Take care and see you next time!"
    ]
    speak_response(random.choice(farewells))
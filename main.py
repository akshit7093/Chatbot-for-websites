from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
from datetime import datetime
import nltk
import spacy
from fuzzywuzzy import fuzz
import tensorflow as tf
from ollama import generate
from fastapi.middleware.cors import CORSMiddleware
from nltk.stem import WordNetLemmatizer
from urllib.parse import urljoin, urlparse
nltk.download('stopwords')
nltk.download('wordnet')

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request and response models
class QuestionRequest(BaseModel):
    question: str
    username: str

class AuthRequest(BaseModel):
    username: str
    password: str

# Authentication and User Management
def check_credentials(username: str, password: str) -> bool:
    if os.path.exists('users.json'):
        with open('users.json', 'r') as f:
            users = json.load(f)
            return users.get(username) == password
    return False

def create_user(username: str, password: str) -> bool:
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

def save_conversation(username: str, question: str, answer: str):
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

def generate_response(query: str, processed_content: list, username: str) -> str:
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
    convo = ''
    if os.path.exists('conversations.json'):
        with open('conversations.json', 'r') as f:
            conversations = json.load(f)
            if username in conversations:
                user_history = conversations[username][-5:]
                for conv in user_history:
                    convo += f"Previous Q: {conv['question']}\n"
                    convo += f"Previous A: {conv['answer']}\n\n"

    prompt = f"""
        You are an expert chatbot for the Department of Justice website India, dedicated to providing accurate and helpful information to users. Use the following context to answer the question:

        {context}

        Question: {query}

        Please respond with a clear, concise, and engaging answer that:

        1. Directly addresses the user's question
        2. Provides relevant and up-to-date information
        3. Includes links to specific DOJ webpages or resources (if applicable)
        4. Offers additional support or next steps (if necessary)

        Respond in a friendly, approachable, and professional tone, as if you are a knowledgeable guide on the DOJ website.
        check previous conversations for any followup questions
        {convo}
        Note: Please avoid generic responses and focus on providing personalized support to the user.
        Do not repeat yourself, give priority to the current asked question and less priority to the past conversations
        """    

    response = generate(model="mistral:7b", prompt=prompt)

    response_text = response.get('response', 'I apologize, but I am unable to generate a response at the moment.')

    opening = "Hello! Thank you for your question. "
    closing = " Is there anything else I can help you with?"

    response_text = opening + response_text + closing
    save_conversation(username, query, response_text)

    return response_text

@app.post("/signup")
async def signup(auth: AuthRequest):
    if create_user(auth.username, auth.password):
        return {"message": "User created successfully"}
    else:
        raise HTTPException(status_code=400, detail="Username already exists")

@app.post("/login")
async def login(auth: AuthRequest):
    if check_credentials(auth.username, auth.password):
        return {"message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/chat")
async def chat(request: QuestionRequest):
    processed_content = load_and_process_data()
    if processed_content:
        answer = generate_response(request.question, processed_content, request.username)
        return {"answer": answer}
    else:
        raise HTTPException(status_code=500, detail="No processed content available")

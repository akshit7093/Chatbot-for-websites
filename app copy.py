from flask import Flask, render_template, request, jsonify, send_from_directory
import json
from flask_cors import CORS
import os
from datetime import datetime
import spacy
from fuzzywuzzy import fuzz
from ollama import generate
import nltk
from nltk.stem import WordNetLemmatizer
from urllib.parse import urlparse
import tensorflow as tf
from deep_translator import GoogleTranslator
from langdetect import detect
from langdetect import detect, DetectorFactory
# from googletrans import Translator
with tf.device('/GPU:0'):
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})
    # Load spaCy model and NLTK resources
    spacy.cli.download("en_core_web_sm")
    nltk.download('stopwords')
    nltk.download('wordnet')
    nlp = spacy.load("en_core_web_sm")
    # Fix for langdetect's seed issue
    DetectorFactory.seed = 0

    # Initialize GoogleTranslator
    translator = GoogleTranslator()


    # Helper functions
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

    def load_and_process_data(filename="ollama_processed_data copy.json"):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                content = json.load(file)
        except FileNotFoundError:
            return None

        lemmatizer = WordNetLemmatizer()

        for page in content:
            if 'url' in page:
                parsed_url = urlparse(page['url'])
                page['processed_url'] = parsed_url.netloc + parsed_url.path
            else:
                page['processed_url'] = "No URL provided"

            if 'summary' in page and isinstance(page['summary'], str):
                doc = nlp(page['summary'])
                tokens = [lemmatizer.lemmatize(token.lemma_) for token in doc if not token.is_stop]
                page['processed_summary'] = " ".join(tokens)
            else:
                page['processed_summary'] = "No summary provided"

            if 'main_topics' in page:
                processed_topics = []
                for topic in page['main_topics']:
                    if topic and isinstance(topic, str):
                        doc = nlp(topic)
                        tokens = [lemmatizer.lemmatize(token.lemma_) for token in doc if not token.is_stop]
                        processed_topics.append(" ".join(tokens))
                    else:
                        processed_topics.append("No topic provided")
                page['processed_topics'] = processed_topics
            else:
                page['processed_topics'] = []

        return content

    def generate_response(query, username):
        with tf.device('/GPU:0'):
            with open('ollama_processed_data copy.json', 'r') as f:
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
            
            prompt = f"""
            You are an official, professional, and helpful chatbot for the Department of Justice website of India. Your task is to provide a detailed, accurate, and reliable response to the user's question using the provided context.

            When answering, follow these guidelines:
            1. **Precise URL Mapping**: Ensure that each URL included in the response directly corresponds to the content it is associated with. Only include URLs that are directly relevant to the information being discussed.
            2. **Detailed Information**: Provide comprehensive explanations, ensuring that all the information is accurate and relevant to the user's query. If the context contains multiple sources of information, choose the most relevant one and explain why it is the most pertinent.
            3. **Structured Response**: Clearly separate different sections of the response, ensuring that the URL is placed right after the information it relates to.
            4. **Avoid Repetition**: Do not repeat the question in the response. Focus on providing a clear and direct answer.

            Use the following context to answer the question:

            {context}

            **Question**: {query}

            Provide a structured, accurate, and detailed response to the question. Ensure that the URLs are directly related to the content they follow and that the information provided is reliable and clear. The response should be written in a professional and helpful tone, appropriate for the Department of Justice website. Do not include the question itself in your response.

            Start your response below:
            """

            response = generate(model="llama3.1", prompt=prompt)
            response_text = response.get('response', 'I apologize, but I am unable to generate a response at the moment.')

            opening = "Hello! Thank you for your question. "
            closing = " Is there anything else I can help you with?"

            response_text = opening + response_text + closing
        save_conversation(username, query, response_text)

        return response_text

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login', methods=['POST'])
    def login():
        data = request.json
        username = data.get('username')
        password = data.get('password')
        if check_credentials(username, password):
            return jsonify({'message': 'Login successful!'})
        else:
            return jsonify({'message': 'Invalid credentials. Please try again.'})

    @app.route('/signup', methods=['POST'])
    def signup():
        data = request.json
        username = data.get('username')
        password = data.get('password')
        if create_user(username, password):
            return jsonify({'message': 'Signup successful!'})
        else:
            return jsonify({'message': 'Username already exists. Please try again.'})

    @app.route('/ask', methods=['POST'])
    def ask():
        data = request.json
        question = data.get('question', '')
        username = 'vin'
        
        try:
            # Detect the language of the input query
            detected_language = detect(question)
            
            # Translate question to English
            translated_question = translator.translate(text=question, source=detected_language, target='en')
            
            # Generate response based on the translated question
            if processed_content:
                answer = generate_response(translated_question, username)
                
                # Translate answer back to the original language
                translated_answer = translator.translate(text=answer, source='en', target=detected_language)
                return jsonify({'response': translated_answer})
            else:
                return jsonify({'response': 'No processed content available.'})
        except Exception as e:
            return jsonify({'response': f'Error occurred: {str(e)}'})

    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory('static', filename)

    if __name__ == "__main__":
        processed_content = load_and_process_data()
        app.run(debug=True)

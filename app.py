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
with tf.device('/GPU:0'):
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})
    # Load spaCy model and NLTK resources
    spacy.cli.download("en_core_web_sm")
    nltk.download('stopwords')
    nltk.download('wordnet')
    nlp = spacy.load("en_core_web_sm")

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

    def load_and_process_data(filename="ollama_processed_data.json"):
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


    def generate_response(query, username, processed_content):
        with tf.device('/GPU:0'):
            # Use the preprocessed content from `load_and_process_data`
            json_data = processed_content

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
            
            user_conversations = processed_content.get('user_conversations', [])
            conversation_context = "\nPrevious conversations:\n"
            for conv in user_conversations[-3:]:  # Include last 3 conversations
                conversation_context += f"Q: {conv['question']}\nA: {conv['answer']}\n\n"

            context += conversation_context

            prompt = f"""
            You are an official, professional, and helpful chatbot for the Department of Justice website of India. Your task is to provide a detailed, accurate, and reliable response to the user's question using the provided context.

            When answering, follow these guidelines:
            1. Provide a concise, structured response with the following sections:
            - **Introductory Section**
            - **Related Section**
            - **Responsive Section**
            - **Conclusion**
            2. Clearly separate the sections with paragraph breaks.
            3. Include any relevant URLs directly after the content they refer to.

            Use the following context to answer the question:

            {context}

            **Question**: {query}

            Provide a structured, accurate, and professional response.
            """

            response = generate(model="tinyllama", prompt=prompt)
            response_text = response.get('response', 'I apologize, but I am unable to generate a response at the moment.')

            structured_response = (
                "Introductory Section\n"
                f"Hello! Thank you for your question. {response_text}\n\n"
                "Related Section\n"
                "Here are some related topics that might interest you:\n"
                f"{context}\n\n"
                "Responsive Section\n"
                "Please find the detailed response based on the information provided above.\n\n"
                "Conclusion\n"
                "Thank you for your patience. Please don't hesitate to ask any further questions."
            )

            return structured_response



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
        question = data.get('question')
        username = request.args.get('username')  # Get the username from the request args
        # username='vin'
        if not username:
            return jsonify({'response': 'User not authenticated'})
        # processed_content = load_and_process_data()
        if processed_content:
            answer = generate_response(question, username,processed_content)
            return jsonify({'response': answer})
        else:
            return jsonify({'response': 'No processed content available.'})

    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory('static', filename)

    if __name__ == "__main__":
        processed_content = load_and_process_data()
        app.run(debug=True)

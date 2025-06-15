# Chatbot for Websites

## Project Overview

This project delivers a sophisticated chatbot solution designed for seamless integration with various websites. It leverages advanced AI capabilities, natural language processing, and web crawling to provide intelligent, context-aware responses. The system supports user authentication and maintains conversation history, offering a personalized and continuous user experience. To ensure flexibility and broad applicability, the project provides implementations using both Flask and FastAPI frameworks.

## Key Features

*   **Intelligent Information Retrieval**: The chatbot efficiently processes and utilizes data from a structured `training_data.txt` file and dynamically crawled web content to generate highly relevant and accurate responses.
*   **Advanced Natural Language Processing (NLP)**: Utilizing robust libraries such as `spaCy` and `NLTK`, the system performs comprehensive text analysis, enabling a deep understanding of user queries and facilitating effective, human-like interactions.
*   **AI-Powered Response Generation**: Integration with `ollama`, specifically leveraging the `mistral:7b` large language model, allows the chatbot to produce intelligent, contextually appropriate, and coherent responses. The system is optimized for GPU acceleration to ensure high performance.
*   **Secure User Authentication**: A robust authentication system manages user registrations and logins, safeguarding access to personalized chatbot functionalities and conversation data.
*   **Persistent Conversation History**: The application meticulously saves and retrieves individual user conversation logs, ensuring a seamless and personalized chat experience across sessions.
*   **Dynamic Web Content Crawling**: An integrated `WebCrawler` class is capable of extracting structured information from specified URLs, continuously expanding and updating the chatbot's knowledge base.
*   **Flexible API Architecture**: The project offers dual backend implementations using Flask (`app.py`) and FastAPI (`main.py`), providing developers with the flexibility to choose the framework best suited for their deployment environment and performance requirements.

## Project Structure

```
Chatbot-for-websites/
├── app.py                  # Flask-based chatbot application with user authentication and conversation management.
├── main.py                 # FastAPI-based chatbot application, offering similar functionalities with asynchronous support.
├── crawler.py              # Utility for web crawling, extracting and structuring data from websites.
├── training_data.txt       # Core dataset containing structured information for chatbot training and response generation.
├── conversations.json      # JSON file storing historical conversation data for all users.
├── users.json              # JSON file managing user credentials and authentication details.
├── extracted_data.json     # Stores data extracted by the web crawler.
├── ollama_processed_data.json # Data processed and optimized for Ollama model consumption.
├── static/                 # Contains static assets for the web interface.
│   ├── scripts/
│   │   └── scripts.js      # Frontend JavaScript for interactive elements.
│   └── styles/
│       └── style.css       # Frontend CSS for styling the user interface.
└── templates/
    └── index.html          # Main HTML template for the chatbot's web interface.
```

## Technologies and Libraries

*   **Backend Frameworks**: Python (Flask, FastAPI)
*   **Natural Language Processing**: `spaCy`, `NLTK`
*   **AI/ML**: `Ollama` (with `mistral:7b` model)
*   **Web Scraping**: `BeautifulSoup4`, `Requests`
*   **Data Storage**: JSON files (easily extensible to relational or NoSQL databases)
*   **Frontend**: HTML5, CSS3, JavaScript
*   **Server**: `uvicorn` (for FastAPI)

## Setup and Installation

To set up and run this project, follow these steps:

1.  **Clone the Repository**:

    ```bash
    git clone https://github.com/your-username/Chatbot-for-websites.git
    cd Chatbot-for-websites
    ```

2.  **Create a Virtual Environment** (Highly Recommended):

    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    # source venv/bin/activate
    ```

3.  **Install Python Dependencies**:

    First, generate a `requirements.txt` file (if not already present) to ensure all necessary packages are listed:

    ```bash
    pip freeze > requirements.txt
    ```

    Then, install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

    If `requirements.txt` is not available or you prefer manual installation:

    ```bash
    pip install Flask FastAPI uvicorn requests beautifulsoup4 spacy nltk ollama
    ```

    **Download NLP Models and Data**:

    ```bash
    python -m spacy download en_core_web_sm
    python -c "import nltk; nltk.download('punkt'); nltk.download('wordnet')"
    ```

4.  **Install and Configure Ollama**:

    *   **Download Ollama**: Visit the official Ollama website at [ollama.ai](https://ollama.ai/) and follow the instructions to download and install the application for your operating system.
    *   **Download the Mistral 7B Model**: Once Ollama is installed, open your terminal or command prompt and pull the `mistral:7b` model:

        ```bash
        ollama run mistral:7b
        ```
        This command will download the model and keep it running. Ensure Ollama is running in the background when you use the chatbot.

## Running the Applications

Choose one of the following methods to run the chatbot application:

### Running the Flask Application (`app.py`)

To start the Flask server, execute the following command in your terminal:

```bash
python app.py
```

The Flask application will typically be accessible at `http://127.0.0.1:5000/`.

### Running the FastAPI Application (`main.py`)

To start the FastAPI server using `uvicorn`, execute:

```bash
uvicorn main:app --reload
```

The FastAPI application will typically be accessible at `http://127.0.0.1:8000/`. The `--reload` flag enables live-reloading during development.

## Usage Guide

1.  **Access the Web Interface**:
    Open your preferred web browser and navigate to the appropriate URL (e.g., `http://127.0.0.1:5000/` for Flask or `http://127.0.0.1:8000/` for FastAPI).

2.  **User Registration and Login**:
    Upon first access, you will be prompted to register a new user account. Existing users can log in with their credentials. This ensures personalized conversation history management.

3.  **Interact with the Chatbot**:
    Utilize the chat interface to submit your queries. The chatbot will process your input and provide AI-generated responses based on its training data and crawled content.

4.  **Web Crawling (Developer Workflow)**:
    The `crawler.py` script is designed for populating the `extracted_data.json` file with new web content. This can be run independently to expand the chatbot's knowledge base. Ensure that `training_data.txt` is updated or re-processed after crawling to integrate new information effectively.

## Project Goals

*   To provide a robust and extensible framework for integrating AI-powered chatbots into web applications.
*   To demonstrate the effective use of modern NLP techniques and large language models for conversational AI.
*   To offer flexible deployment options through both Flask and FastAPI.
*   To facilitate easy expansion of the chatbot's knowledge base via automated web crawling.

## Future Enhancements

*   **Database Integration**: Migrate from JSON file storage to a more scalable database solution (e.g., PostgreSQL, MongoDB) for user data and conversation history.
*   **Advanced NLP Features**: Implement more sophisticated NLP techniques, such as sentiment analysis, intent recognition, and entity extraction, to enhance conversational capabilities.
*   **Multi-model Support**: Allow dynamic switching between different large language models or integrate with external LLM APIs.
*   **Improved Web Crawler**: Enhance the crawler with features like sitemap parsing, dynamic content rendering (e.g., using Selenium), and more robust error handling.
*   **Containerization**: Provide Dockerfiles and Docker Compose configurations for easier deployment and scalability.
*   **Testing Suite**: Develop a comprehensive suite of unit and integration tests to ensure reliability and maintainability.
*   **User Interface Improvements**: Enhance the frontend with a more modern design, real-time updates, and additional user-friendly features.

## Contributing

Contributions are welcome! If you'd like to contribute, please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/YourFeature`).
3.  Make your changes and commit them (`git commit -m 'Add some feature'`).
4.  Push to the branch (`git push origin feature/YourFeature`).
5.  Open a Pull Request.

Please ensure your code adheres to the existing style and includes appropriate tests.
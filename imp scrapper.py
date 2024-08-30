#Important

import ollama
from ollama import generate
from bs4 import BeautifulSoup
import requests
from collections import deque
from urllib.parse import urljoin, urlparse
import json

def scrape_and_process_website_with_ollama(base_url):
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

            # Extract text content from the page
            page_text = soup.get_text(separator='\n', strip=True)

            # Use Ollama to process and summarize the content
            prompt = f"""
            Analyze the following web page content and provide a structured summary:

            {page_text}

            Format the summary as JSON with the following structure:
            {{
                "url": "{url}",
                "title": "Page title",
                "main_topics": ["Topic 1", "Topic 2", ...],
                "summary": "A brief summary of the page content"
            }}
            """

            ollama_response = generate(model="llama3.1", prompt=prompt)
            processed_content = ollama_response['response']

            # More robust parsing of the Ollama response
            try:
                # First, try to find JSON-like content within the response
                json_start = processed_content.find('{')
                json_end = processed_content.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_content = processed_content[json_start:json_end]
                    content_json = json.loads(json_content)
                else:
                    # If no JSON-like content found, create a basic structure
                    content_json = {
                        "url": url,
                        "title": soup.title.string if soup.title else "No title",
                        "main_topics": [],
                        "summary": processed_content[:500]  # Use first 500 characters as summary
                    }
                
                structured_content.append(content_json)
                print(f"Processed content from: {url}")
            except json.JSONDecodeError:
                print(f"Error parsing Ollama response for {url}. Using fallback structure.")
                # Use a fallback structure
                content_json = {
                    "url": url,
                    "title": soup.title.string if soup.title else "No title",
                    "main_topics": [],
                    "summary": "Error in processing. Please check the original page."
                }
                structured_content.append(content_json)

            # Find all links on the current page
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                
                # Only add URLs from the same domain
                if urlparse(full_url).netloc == urlparse(base_url).netloc and full_url not in visited:
                    queue.append(full_url)

        except Exception as e:
            print(f"Error processing {url}: {e}")

    return structured_content

# Usage example
if __name__ == "__main__":
    base_url = "https://doj.gov.in/"  # Replace with the website you want to crawl
    result = scrape_and_process_website_with_ollama(base_url)
    
    # Save the result to a JSON file
    with open("ollama_processed_data.json", "w") as f:
        json.dump(result, f, indent=4)

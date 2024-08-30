import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json

class WebCrawler:
    def __init__(self, base_url):
        self.base_url = base_url
        self.visited = set()
        self.data = {}
    
    def crawl(self, url):
        # Skip if this URL has already been visited
        if url in self.visited:
            return
        
        # Mark this URL as visited
        self.visited.add(url)
        
        # Fetch the content from the URL
        response = requests.get(url)
        if response.status_code != 200:
            return
        
        # Parse the content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract and store page data
        page_data = {
            'url': url,
            'title': soup.title.string if soup.title else 'No title',
            'links': []
        }
        
        # Find all internal links
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            if self.is_internal_link(full_url):
                page_data['links'].append(full_url)
                # Recursively crawl this new link
                self.crawl(full_url)
        
        # Store page data
        self.data[url] = page_data
    
    def is_internal_link(self, url):
        # Check if the URL is internal to the base website
        parsed_base = urlparse(self.base_url)
        parsed_url = urlparse(url)
        return parsed_base.netloc == parsed_url.netloc
    
    def save_to_json(self, filename="crawled_data.json"):
        with open(filename, "w") as file:
            json.dump(self.data, file, indent=4)
    
    def start(self):
        self.crawl(self.base_url)
        self.save_to_json()

if __name__ == "__main__":
    # Replace with the base URL of the website you want to crawl
    base_url = "https://doj.gov.in/"
    crawler = WebCrawler(base_url)
    crawler.start()

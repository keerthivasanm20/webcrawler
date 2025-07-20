import requests
from bs4 import BeautifulSoup

def scrape_url(url: str) -> str:
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()
        text = soup.get_text(separator=' ', strip=True)
        return text[:5000]  # Limit length for Claude
    except Exception as e:
        return f"Error scraping URL: {str(e)}"
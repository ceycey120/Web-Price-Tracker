import requests
from bs4 import BeautifulSoup
import re
import scrapy
from scrapy.crawler import CrawlerProcess
from datetime import datetime

# ORIGINAL FUNCTION - UNCHANGED
def get_price_kitapyurdu(url):
    """
    Extract product price from Kitapyurdu website
    Args:
        url (str): Product page URL
    Returns:
        float: Product price or None if failed
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        print(f"Downloading page: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try different price element selectors
        price_element = soup.find('div', class_='price__item')
        if not price_element:
            price_element = soup.find('div', class_='pr_price_content')
        
        if price_element:
            price_text = price_element.get_text(strip=True)
            print(f"Found price text: '{price_text}'")
            
            # Extract and clean price numbers
            numbers = re.findall(r'[\d,]+', price_text)
            if numbers:
                # Combine numbers and convert to float
                full_price = ''.join(numbers).replace(',', '.')
                price_number = float(full_price)
                print(f"Cleaned price: {price_number} TL")
                return price_number
            else:
                print("No price numbers found!")
                return None
        else:
            print("Price element not found!")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

# SCRAPY FUNCTION
class KitapyurduScraper(scrapy.Spider):
    name = "kitapyurdu"
    
    def __init__(self, urls=None, *args, **kwargs):
        super(KitapyurduScraper, self).__init__(*args, **kwargs)
        self.start_urls = urls or []
    
    def parse(self, response):
        """Extract price using Scrapy"""
        price = self.extract_price_scrapy(response)
        product_name = response.css('h1[itemprop="name"]::text').get() or "Unknown Product"
        
        yield {
            'name': product_name.strip(),
            'url': response.url,
            'price': price,
            'timestamp': datetime.now().isoformat()
        }
    
    def extract_price_scrapy(self, response):
        """Extract price using Scrapy selectors"""
        selectors = [
            'div.price__item::text',
            'div.pr_price_content::text',
            '.price::text'
        ]
        
        for selector in selectors:
            price_text = response.css(selector).get()
            if price_text:
                return self.clean_price(price_text)
        return None
    
    def clean_price(self, price_text):
        """Clean price text"""
        try:
            numbers = re.findall(r'[\d,]+', price_text.strip())
            if numbers:
                full_price = ''.join(numbers).replace(',', '.')
                return float(full_price)
        except (ValueError, IndexError):
            pass
        return None

def scrape_with_scrapy(urls):
    """
    Args:
        urls: List of URLs to scrape
    Returns:
        list: Price data
    """
    results = []
    
    class ResultCollector:
        def __init__(self):
            self.items = []
        
        def process_item(self, item, spider):
            self.items.append(item)
            return item
    
    collector = ResultCollector()
    
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'LOG_LEVEL': 'ERROR'
    })
    
    process.crawl(KitapyurduScraper, urls=urls)
    process.start()
    
    return collector.items

# TEST
if __name__ == "__main__":
    # Test normal function
    print("Testing normal function...")
    test_url = "https://www.kitapyurdu.com/kitap/harry-potter-ve-felsefe-tasi/32780.html"
    price = get_price_kitapyurdu(test_url)
    if price:
        print(f"Normal function: {price} TL")
    
    # Test Scrapy
    print("\nTesting Scrapy (+10 points)...")
    test_urls = [
        "https://www.kitapyurdu.com/kitap/harry-potter-ve-felsefe-tasi/32780.html",
        "https://www.kitapyurdu.com/kitap/harry-potter-ve-efsaneler-kitabi/677276.html"
    ]
    
    scrapy_results = scrape_with_scrapy(test_urls)
    for result in scrapy_results:
        print(f"Scrapy: {result['name']} - {result['price']} TL")

import requests
from bs4 import BeautifulSoup
import re
import sqlite3

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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
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

def check_all_products():
    """
    Check and update prices for all products in database
    """
    try:
        # Connect to database
        conn = sqlite3.connect('price_tracker.db')
        cursor = conn.cursor()
        
        # Get all product URLs from database
        cursor.execute("SELECT id, url, name FROM products")
        all_products = cursor.fetchall()
        
        print(f"Checking {len(all_products)} products...")
        
        updated_count = 0
        for product_id, product_url, product_name in all_products:
            print(f"Checking: {product_name}")
            
            # Get current price using our function
            current_price = get_price_kitapyurdu(product_url)
            
            if current_price:
                # Save new price to database
                cursor.execute(
                    """INSERT INTO price_history 
                    (product_id, price, date) 
                    VALUES (?, ?, datetime('now'))""",
                    (product_id, current_price)
                )
                updated_count += 1
                print(f"Price updated: {current_price} TL")
            else:
                print(f"Failed to get price")
        
        # Save changes and close connection
        conn.commit()
        conn.close()
        print(f"Completed! Updated {updated_count} products.")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def add_sample_products():
    """
    Add sample products for testing (optional)
    """
    conn = sqlite3.connect('price_tracker.db')
    cursor = conn.cursor()
    
    sample_products = [
        ("Harry Potter 1", "https://www.kitapyurdu.com/kitap/harry-potter-ve-felsefe-tasi/32780.html", 120.0),
        ("Harry Potter 2", "https://www.kitapyurdu.com/kitap/harry-potter-ve-efsaneler-kitabi/677276.html", 130.0)
    ]
    
    for name, url, target_price in sample_products:
        cursor.execute(
            "INSERT OR IGNORE INTO products (name, url, target_price) VALUES (?, ?, ?)",
            (name, url, target_price)
        )
    
    conn.commit()
    conn.close()
    print("Sample products added!")

# Test functions
if __name__ == "__main__":
    # Test single product price
    test_url = "https://www.kitapyurdu.com/kitap/harry-potter-ve-felsefe-tasi/32780.html"
    
    print("Testing single product...")
    price = get_price_kitapyurdu(test_url)
    
    if price:
        print(f"Success! Price: {price} TL")
        
        # Uncomment below to test database functions
        # print("\nTesting database functions...")
        # add_sample_products()  # Add test data first
        # check_all_products()   # Then check all products
    else:
        print("Failed to get price!")
import sqlite3
from datetime import datetime
from tabulate import tabulate  # To display data nicely in table form

class PriceDataManager:
    def __init__(self, db_name="prices.db"):
        self.db_name = db_name
        self.create_table()
    
    def create_table(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                date TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def add_price(self, product_name, price, date=None):
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO prices (product_name, price, date) VALUES (?, ?, ?)",
                       (product_name, price, date))
        conn.commit()
        conn.close()
    
    def get_price_history(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT product_name, price, date FROM prices ORDER BY date DESC")
        data = cursor.fetchall()
        conn.close()
        return data
    
    def display_price_history(self):
        data = self.get_price_history()
        if data:
            print(tabulate(data, headers=["Product Name", "Price", "Date"], tablefmt="fancy_grid"))
        else:
            print("No price data available.")

# --- Example Usage ---
if __name__ == "__main__":
    manager = PriceDataManager()

    # Add some sample data (simulating raw prices from a collector)
    manager.add_price("Laptop", 1299.99)
    manager.add_price("Smartphone", 799.50)
    manager.add_price("Headphones", 149.90)

    # Display organized price history
    manager.display_price_history()

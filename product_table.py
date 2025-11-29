import sqlite3
from datetime import datetime
from tabulate import tabulate

# Define the tiers and points
DB_TIERS = {
    "SQLite": {"tier": 0, "points": 15},
    "MySQL": {"tier": 1, "points": 15},
    "MSSQL": {"tier": 1, "points": 10},
    "PostgreSQL": {"tier": 2, "points": 15},
    "MongoDB": {"tier": 3, "points": 10},  # assuming 10 points
}

class PriceDataManager:
    def __init__(self, db="prices.db"):
        self.db = db
        self.create_tables()

    def create_tables(self):
        self._execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                tier INTEGER,
                points INTEGER
            )
        """)
        self._execute("""
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                price REAL NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """)

    def _execute(self, query, params=(), fetch=False):
        with sqlite3.connect(self.db) as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            return cur.fetchall() if fetch else None

    # ---------------- PRODUCT FUNCTIONS ---------------- #
    def add_product(self, name):
        tier = DB_TIERS.get(name, {}).get("tier", None)
        points = DB_TIERS.get(name, {}).get("points", None)

        self._execute(
            "INSERT OR IGNORE INTO products (name, tier, points) VALUES (?, ?, ?)",
            (name, tier, points)
        )
        result = self._execute("SELECT id FROM products WHERE name = ?", (name,), fetch=True)
        return result[0][0]  # return product ID

    # ---------------- PRICE FUNCTIONS ------------------- #
    def add_price(self, product_name, price, date=None):
        product_id = self.add_product(product_name)
        date = date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._execute(
            "INSERT INTO prices (product_id, price, date) VALUES (?, ?, ?)",
            (product_id, price, date)
        )

    def get_price_history(self):
        return self._execute("""
            SELECT products.name, products.tier, products.points, prices.price, prices.date
            FROM prices
            JOIN products ON prices.product_id = products.id
            ORDER BY prices.date DESC
        """, fetch=True)

    def display_price_history(self):
        data = self.get_price_history()
        print(tabulate(data, headers=["Product", "Tier", "Points", "Price", "Date"], tablefmt="fancy_grid") 
              if data else "No price data available.")


# ------------ Example Usage ------------ #
if __name__ == "__main__":
    m = PriceDataManager()
    m.add_price("SQLite", 23)       # product = database
    m.add_price("MySQL", 4)
    m.add_price("PostgreSQL", 8)
    m.add_price("MongoDB", 17)
    m.display_price_history()

    

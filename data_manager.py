import os
import json
from datetime import datetime
from typing import Dict, Any, List
from contextlib import contextmanager

# Database ORM for bonus points
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship 
import pymongo # MongoDB desteği için tutulmalı

Base = declarative_base()

# Database Models
class Product(Base):
    """Represents each unique product in the database."""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True) # Primary Key
    
    # We keep the product_id as an external ID (as in KitapYurdu), but we don't enforce uniqueness.
    # The URL will make the product unique anyway.
    product_id = Column(String(100), unique=False, nullable=True) 
    
    name = Column(String(500), nullable=False) # Size increased to 500
    url = Column(String(1000), unique=True, nullable=False) #URL must be unique
    site = Column(String(100))
    category = Column(String(100))
    image_url = Column(String(1000))
    created_at = Column(DateTime, default=datetime.now)

    # Relationship from Product to PriceHistory
    price_history = relationship("PriceHistory", back_populates="product_info", cascade="all, delete-orphan")


class PriceHistory(Base):
    """Keeps price history of products."""
    __tablename__ = 'price_history'
    
    id = Column(Integer, primary_key=True)
    
    product_base_id = Column(Integer, ForeignKey('products.id'), nullable=False) 
    
    current_price = Column(Float, nullable=False)
    original_price = Column(Float)
    currency = Column(String(10), default='TRY')
    stock_status = Column(String(50))
    timestamp = Column(DateTime, default=datetime.now)
    scraped_by = Column(String(50))
    data_source = Column(String(50))
    
    # PriceHistory'den Product'a ilişki (Eklendi)
    product_info = relationship("Product", back_populates="price_history")

class PriceDataManager:
    """
    Person 2: Data Storage Manager
    Receives price data from Person 1 and stores in database
    """
    
    def __init__(self, database_type="SQLite", database_name="price_tracker"):
        self.database_type = database_type
        self.database_name = database_name
        
        print(f"Setting up {database_type} database...")
        self._setup_database()
        
        if database_type != "MongoDB":
            self._create_tables()
    
    def _setup_database(self):
            """Setup database connection (SQLite, PostgreSQL, or MongoDB)"""
            
            if self.database_type == "PostgreSQL":
                # PostgreSQL bağlantı dizesi (Şu an kullanılmıyor)
                connection_string = os.getenv(
                    "DATABASE_URL", 
                    "postgresql://postgres:1234@localhost:5433/price_tracker"
                )
                self.engine = create_engine(connection_string)
                self.SessionLocal = sessionmaker(bind=self.engine)
                
            elif self.database_type == "MongoDB":
                # MongoDB bağlantı kodu (Şu an kullanılmıyor)
                # self.client = pymongo.MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
                # self.db = self.client[self.database_name]
                return
                
            elif self.database_type == "SQLite":
                # A file named price_tracker.db is created
                self.engine = create_engine(f"sqlite:///{self.database_name}.db")
                self.SessionLocal = sessionmaker(bind=self.engine)
                
            else:
                raise ValueError(f"Unknown database type: {self.database_type}")
    
    def _create_tables(self):
        """Create database tables for SQL databases"""
        if hasattr(self, 'engine'):
            Base.metadata.create_all(bind=self.engine)
            print("Database tables created")
    
    @contextmanager
    def get_db_session(self):
        """Get database session"""
        if self.database_type == "MongoDB":
            yield self.db
        else:
            db = self.SessionLocal()
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()
    
    def save_price_data(self, price_data: Dict[str, Any]) -> bool:
        """
        Save price data from Person 1 to database
        
        Args:
            price_data: Dictionary with product and price info
                Example: {
                    'product_name': 'Harry Potter',
                    'url': 'https://...',
                    'current_price': 59.99,
                    'site': 'kitapyurdu',
                    'timestamp': '2024-01-15T10:30:00',
                    ...
                }
        
        Returns:
            bool: True if saved successfully
        """
        try:
            if self.database_type == "MongoDB":
                return self._save_to_mongodb(price_data)
            else:
                return self._save_to_sql(price_data)
                
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    def _save_to_sql(self, data: Dict[str, Any]) -> bool:
        """Save to SQL database using ORM"""
        
        try:
            with self.get_db_session() as db:
                # 1. Search for existing product by URL
                product = db.query(Product).filter_by(url=data['url']).first()
                
                if not product:
                    # If the product does not exist, create a new Product record
                    product = Product(
                        product_id=data.get('product_id'),
                        name=data['product_name'],
                        url=data['url'],
                        site=data.get('site'),
                        category=data.get('category'),
                        image_url=data.get('image_url')
                    )
                    db.add(product)
                    db.flush() #Flush is required to assign the ID
                
                # 2. Save price history record
                price_record = PriceHistory(
                    # FIX: Use of Foreign Key (product_base_id)
                    product_base_id=product.id,  
                    current_price=data['current_price'],
                    original_price=data.get('original_price'),
                    currency=data.get('currency', 'TRY'),
                    stock_status=data.get('stock_status'),
                    timestamp=datetime.fromisoformat(data['timestamp']), 
                    scraped_by=data.get('scraped_by', 'PriceCollector'),
                    data_source=data.get('data_source', 'scraper')
                )
                db.add(price_record)
                
                return True
        except Exception as e:
            print(f"SQL Save Error: {e}")
            return False
    
    def _save_to_mongodb(self, data: Dict[str, Any]) -> bool:
        """Save to MongoDB"""
        products_col = self.db['products']
        prices_col = self.db['price_history']
        
        # Product document
        product_doc = {
            'product_id': data.get('product_id'),
            'name': data['product_name'],
            'url': data['url'],
            'site': data.get('site'),
            'category': data.get('category'),
            'image_url': data.get('image_url'),
            'created_at': datetime.now()
        }
        
        # Price document
        price_doc = {
            'product_id': data.get('product_id'),
            'current_price': data['current_price'],
            'original_price': data.get('original_price'),
            'currency': data.get('currency', 'TRY'),
            'stock_status': data.get('stock_status'),
            'timestamp': datetime.fromisoformat(data['timestamp']),
            'scraped_by': data.get('scraped_by', 'PriceCollector'),
            'data_source': data.get('data_source'),
            'stored_at': datetime.now()
        }
        
        # Update or insert product
        products_col.update_one(
            {'url': data['url']},
            {'$set': product_doc},
            upsert=True
        )
        
        # Insert price record
        prices_col.insert_one(price_doc)
        
        return True
    
    def import_from_scraper(self, json_file: str = "prices.json") -> int:
        """
        Import data from Person 1's JSON output file
        
        Args:
            json_file: Path to JSON file from Person 1
        
        Returns:
            int: Number of successfully imported records
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                scraper_data = json.load(f)
            
            print(f"Importing {len(scraper_data)} records from {json_file}")
            
            success_count = 0
            for item in scraper_data:
                if self.save_price_data(item):
                    success_count += 1
            
            print(f"Imported {success_count}/{len(scraper_data)} records")
            return success_count
            
        except FileNotFoundError:
            print(f"File not found: {json_file}")
            return 0
        except json.JSONDecodeError:
            print(f"Invalid JSON file: {json_file}")
            return 0
    
    def get_price_history(self, product_url: str = None, site: str = None) -> List[Dict]:
        """Get price history for products"""
        with self.get_db_session() as db:
            if self.database_type == "MongoDB":
                return self._get_mongo_history(product_url, site)
            else:
                return self._get_sql_history(db, product_url, site)
    
    def _get_sql_history(self, db, product_url: str = None, site: str = None) -> List[Dict]:
        """Get history from SQL database"""
        from sqlalchemy.orm import joinedload
        
        query = db.query(
            Product.name,
            PriceHistory.current_price,
            PriceHistory.timestamp,
            Product.site,
            Product.url
        ).join(
            PriceHistory,
            PriceHistory.product_base_id == Product.id
        )
        
        if product_url:
            query = query.filter(Product.url == product_url)
        if site:
            query = query.filter(Product.site == site)
        
        results = query.order_by(PriceHistory.timestamp.desc()).all()
        
        return [
            {
                'product': r.name,
                'price': r.current_price,
                'date': r.timestamp,
                'site': r.site,
                'url': r.url
            }
            for r in results
        ]
    
    def _get_mongo_history(self, product_url: str = None, site: str = None) -> List[Dict]:
        """Get history from MongoDB"""
        pipeline = [
            {
                '$lookup': {
                    'from': 'price_history',
                    'localField': 'product_id',
                    'foreignField': 'product_id',
                    'as': 'prices'
                }
            },
            {'$unwind': '$prices'},
            {'$sort': {'prices.timestamp': -1}}
        ]
        
        if product_url:
            pipeline.insert(0, {'$match': {'url': product_url}})
        if site:
            pipeline.insert(0, {'$match': {'site': site}})
        
        results = self.db['products'].aggregate(pipeline)
        
        return [
            {
                'product': r['name'],
                'price': r['prices']['current_price'],
                'date': r['prices']['timestamp'],
                'site': r['site'],
                'url': r['url']
            }
            for r in results
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_db_session() as db:
            if self.database_type == "MongoDB":
                product_count = self.db['products'].count_documents({})
                price_count = self.db['price_history'].count_documents({})
            else:
                product_count = db.query(Product).count()
                price_count = db.query(PriceHistory).count()
            
            return {
                'database_type': self.database_type,
                'product_count': product_count,
                'price_records': price_count
            }

# Example usage
if __name__ == "__main__":
    # Use SQLite for better performance
    manager = PriceDataManager(database_type="SQLite")
    
    # Sample data from Person 1
    sample_data = {
        "product_name": "Harry Potter ve Felsefe Taşı",
        "product_id": "32780",
        "url": "https://www.kitapyurdu.com/kitap/harry-potter-ve-felsefe-tasi/32780.html",
        "current_price": 59.99,
        "original_price": 79.99,
        "currency": "TRY",
        "site": "kitapyurdu",
        "stock_status": "In Stock",
        "timestamp": datetime.now().isoformat()
    }
    
    # Save the data
    manager.save_price_data(sample_data)
    
    # Or import from Person 1's JSON file
    # manager.import_from_scraper("prices.json")
    
    # Get price history
    history = manager.get_price_history()
    print(f"Stored {len(history)} price records")
    
    # Get statistics
    stats = manager.get_stats()
    print(f"Database: {stats['database_type']}")
    print(f"Products: {stats['product_count']}")
    print(f"Price records: {stats['price_records']}")

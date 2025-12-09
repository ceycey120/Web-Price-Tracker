"""
PROFESSIONAL PRICE COLLECTOR - Birleştirilmiş Sistem
Personel 1 (Scraper) ve Personel 2 (Data Manager) Kodlarının Entegre Hali.

Destekler: KitapYurdu, Hepsiburada, Amazon.com.tr
Veritabanı: SQLAlchemy ORM (SQLite, PostgreSQL) ve MongoDB Desteği.
"""

import scrapy
import requests
import re
import json
import argparse
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, ClassVar
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
from enum import Enum
from scrapy.crawler import CrawlerProcess
from scrapy.item import Item, Field
from itemloaders.processors import TakeFirst, MapCompose
from urllib.parse import urlparse
from contextlib import contextmanager

# --- Database Dependencies (Personel 2) ---
import sqlalchemy as sa
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pymongo  # MongoDB desteği için

# SQLAlchemy uyarısını görmezden gelmek için
sa.exc.MovedIn20Warning.warn_if_needed = lambda *a, **kw: None

Base = declarative_base()

# ============================================
# DATA MODELS (Personel 1)
# ============================================


@dataclass
class ProductInfo:
    """Data model for product information (Personel 1)"""

    name: str
    current_price: float
    original_price: Optional[float] = None
    url: str = ""
    site: str = ""
    currency: str = "TRY"
    stock_status: str = "Unknown"
    product_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    image_url: Optional[str] = None
    category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DB persistence"""
        data = asdict(self)
        # Datetime objesini ISO formatına dönüştür (JSON/DB uyumluluğu)
        data["timestamp"] = self.timestamp.isoformat()
        data["product_name"] = data.pop("name")  # DataManager'ın beklediği anahtar
        return {k: v for k, v in data.items() if v is not None}


class PriceItem(Item):
    """Scrapy Item definition (Personel 1)"""

    product_name = Field(output_processor=TakeFirst())
    current_price = Field(output_processor=TakeFirst())
    original_price = Field(output_processor=TakeFirst())
    url = Field(output_processor=TakeFirst())
    site = Field(output_processor=TakeFirst())
    currency = Field(output_processor=TakeFirst())
    stock_status = Field(output_processor=TakeFirst())
    product_id = Field(output_processor=TakeFirst())
    timestamp = Field(output_processor=TakeFirst())


# ============================================
# ORM / DATABASE MODELS (Personel 2 Düzeltilmiş)
# ============================================


class Product(Base):
    """Represents each unique product in the database."""

    __tablename__ = "products"  # Düzeltme: _tablename_ -> __tablename__

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(100), index=True)
    name = Column(String(500), nullable=False)
    url = Column(Text, nullable=False, unique=True, index=True)
    site = Column(String(50))
    category = Column(String(100))
    image_url = Column(Text)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    price_history = relationship(
        "PriceHistory", back_populates="product_info", cascade="all, delete-orphan"
    )


class PriceHistory(Base):
    """Keeps price history of products. (Nihai ve Doğru Model)"""

    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key: Ürünün ana ID'sine bağlanır.
    product_base_id = Column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )

    current_price = Column(Float, nullable=False)
    original_price = Column(Float)
    currency = Column(String(10), default="TRY")
    stock_status = Column(String(50))
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    scraped_by = Column(String(50))
    data_source = Column(String(50))

    product_info = relationship("Product", back_populates="price_history")


# ============================================
# PRICE PROCESSOR / UTILITY (Personel 1)
# ============================================


class AdvancedPriceProcessor:
    """Extended price processor with currency handling"""

    currency_symbols = {"₺", "TL", "USD", "€", "£", "$"}

    def _clean_number(self, text: str) -> float:
        """Clean and convert number string to float"""
        cleaned = text.replace(",", ".").replace(" ", "")
        # Birden fazla nokta varsa, ilk noktadan sonrasını ondalık kabul et
        parts = cleaned.split(".")
        if len(parts) > 2:
            cleaned = parts[0] + "." + "".join(parts[1:])
        return float(cleaned)

    def process_price(
        self, price_text: str, remove_symbols: bool = True
    ) -> Optional[float]:
        """Process price with currency symbol removal"""
        if not price_text:
            return None

        if remove_symbols:
            for symbol in self.currency_symbols:
                price_text = price_text.replace(symbol, "")

        # Regex ile sadece sayıları ve ondalık işaretini al
        numbers = re.findall(r"[\d,.]+", price_text)
        if numbers:
            try:
                return self._clean_number(numbers[0])
            except ValueError:
                return None
        return None


def _extract_text(
    response: scrapy.http.Response, selectors: List[str], default: str = ""
) -> str:
    """Helper method to extract text from multiple selectors"""
    for selector in selectors:
        text = response.css(selector).get()
        if text and text.strip():
            return text.strip()
    return default


# ============================================
# DATA MANAGER (Personel 2 Düzeltilmiş)
# ============================================


class PriceDataManager:
    """Personel 2: Data Storage Manager"""

    # __init__ metodunun adındaki hatayı düzelt
    def __init__(
        self, database_type="SQLite", database_name="price_tracker_V2"
    ):  # Değiştirildi!
        self.database_type = database_type
        self.database_name = database_name
        print(f"Setting up {database_type} database...")
        self._setup_database()
        if database_type != "MongoDB":
            self._create_tables()

    def _setup_database(self):
        if self.database_type == "PostgreSQL":
            connection_string = os.getenv(
                "DATABASE_URL",
                "postgresql://user:password@localhost:5432/price_tracker",
            )
            self.engine = create_engine(connection_string)
            self.SessionLocal = sessionmaker(bind=self.engine)
        elif self.database_type == "MongoDB":
            self.mongo_client = pymongo.MongoClient(
                os.getenv("MONGO_URI", "mongodb://localhost:27017/")
            )
            self.db = self.mongo_client[self.database_name]
        elif self.database_type == "SQLite":
            self.engine = create_engine(f"sqlite:///{self.database_name}.db")
            self.SessionLocal = sessionmaker(bind=self.engine)

    def _create_tables(self):
        if hasattr(self, "engine"):
            Base.metadata.create_all(bind=self.engine)
            print("Database tables created")

    @contextmanager
    def get_db_session(self):
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
        """Save price data from Personel 1 to database"""
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
        with self.get_db_session() as db:
            clean_url = data["url"].strip()

            # 1. Product (Ürün) Kaydı
            product = db.query(Product).filter_by(url=clean_url).first()
            if not product:
                product = Product(
                    product_id=data.get("product_id"),
                    name=data["product_name"],
                    url=clean_url,
                    site=data.get("site"),
                    category=data.get("category"),
                    image_url=data.get("image_url"),
                )
                db.add(product)
                db.flush()  # ID almak için zorunlu

            # 2. PriceHistory (Fiyat Geçmişi) Kaydı
            ts_str = data["timestamp"]
            if isinstance(ts_str, str):
                if ts_str.endswith("Z"):
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                else:
                    ts = datetime.fromisoformat(ts_str)
            else:
                ts = ts_str

            price_record = PriceHistory(
                product_base_id=product.id,  # Foreign Key tanımlı olmadığı için yorum satırı yapıldı
                current_price=float(data["current_price"]),
                original_price=(
                    float(data["original_price"])
                    if data.get("original_price")
                    else None
                ),
                currency=data.get("currency", "TRY"),
                stock_status=data.get("stock_status"),
                timestamp=ts,
                scraped_by=data.get("scraped_by", "PriceCollector"),
                data_source=data.get("data_source", "scraper"),
            )
            db.add(price_record)
            return True

    def _save_to_mongodb(self, data: Dict[str, Any]) -> bool:
        # Kişi 2'nin orijinal kodu kullanılabilir (Mongo için uygundur)
        products_col = self.db["products"]
        prices_col = self.db["price_history"]

        clean_url = data["url"].strip()
        product_doc = {
            "product_id": data.get("product_id"),
            "name": data["product_name"],
            "url": clean_url,
            "site": data.get("site"),
            "category": data.get("category"),
            "image_url": data.get("image_url"),
            "created_at": datetime.now(timezone.utc),
        }

        ts_str = data["timestamp"]
        if isinstance(ts_str, str):
            if ts_str.endswith("Z"):
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            else:
                ts = datetime.fromisoformat(ts_str)
        else:
            ts = ts_str

        price_doc = {
            "product_url": clean_url,
            "current_price": float(data["current_price"]),
            "original_price": (
                float(data["original_price"]) if data.get("original_price") else None
            ),
            "currency": data.get("currency", "TRY"),
            "stock_status": data.get("stock_status"),
            "timestamp": ts,
            "scraped_by": data.get("scraped_by", "PriceCollector"),
            "data_source": data.get("data_source"),
            "stored_at": datetime.now(timezone.utc),
        }

        products_col.update_one({"url": clean_url}, {"$set": product_doc}, upsert=True)
        prices_col.insert_one(price_doc)
        return True


# ============================================
# CORE COMPONENTS / SPIDERS (Personel 1)
# ============================================


class BasePriceSpider(scrapy.Spider, ABC):
    """Base spider for all price collectors"""

    name: ClassVar[str]
    allowed_domains: ClassVar[List[str]] = []

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 5.0,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.0,
        "AUTOTHROTTLE_MAX_DELAY": 5.0,
        "LOG_LEVEL": "INFO",  # Log seviyesini düşürdük
    }

    def __init__(self, urls: Optional[List[str]] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = urls if urls else self.get_default_urls()

    @abstractmethod
    def get_default_urls(self) -> List[str]:
        """Get default URLs to scrape"""
        pass

    @abstractmethod
    def parse_product_page(self, response: scrapy.http.Response) -> ProductInfo:
        """Parse product page and extract information"""
        pass

    def parse(self, response: scrapy.http.Response):
        """Main parsing method: Sends data to pipeline/database"""
        try:
            product_info = self.parse_product_page(response)
            if product_info and product_info.current_price > 0:
                # Doğrudan Pipeline'a Item olarak gönder
                yield self._create_scrapy_item(product_info)
            else:
                self.logger.warning(
                    f"Skipping product due to invalid price/info: {response.url}"
                )
        except Exception as e:
            self.logger.error(f"Error parsing {response.url}: {e}")

    def _create_scrapy_item(self, info: ProductInfo) -> PriceItem:
        """Convert ProductInfo to Scrapy Item object"""
        return PriceItem(
            product_name=info.name,
            current_price=info.current_price,
            original_price=info.original_price,
            url=info.url,
            site=info.site,
            currency=info.currency,
            stock_status=info.stock_status,
            product_id=info.product_id,
            timestamp=info.timestamp.isoformat(),
        )


# ==================== SITE-SPECIFIC SPIDERS ====================


class KitapyurduSpider(BasePriceSpider):
    """Spider for KitapYurdu.com"""

    name = "kitapyurdu"
    allowed_domains = ["kitapyurdu.com"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.price_processor = AdvancedPriceProcessor()

    def get_default_urls(self) -> List[str]:
        return [
            "https://www.kitapyurdu.com/kitap/harry-potter-ve-felsefe-tasi/32780.html",
            "https://www.kitapyurdu.com/kitap/beyaz-zambaklar-ulkesinde/528653.html",
        ]

    def parse_product_page(self, response: scrapy.http.Response) -> ProductInfo:
        name_selectors = ['h1[itemprop="name"]::text', ".product-heading h1::text"]
        product_name = _extract_text(response, name_selectors, "Unknown Product")

        price_selectors = [
            "div.price__item::text",
            ".price.price--now::text",
            '[itemprop="price"]::attr(content)',
        ]
        price_text = _extract_text(response, price_selectors)
        current_price = (
            self.price_processor.process_price(price_text) if price_text else 0.0
        )

        original_price_selectors = [".price.price--old::text", ".price__old::text"]
        original_price_text = _extract_text(response, original_price_selectors)
        original_price = (
            self.price_processor.process_price(original_price_text)
            if original_price_text
            else None
        )

        stock_text = _extract_text(
            response,
            [
                ".stock-status.in-stock::text",
                '[itemprop="availability"]::attr(content)',
            ],
        )
        stock_status = "In Stock" if "stok" in stock_text.lower() else "Unknown"

        product_id_match = re.search(r"/(\d+)\.html$", response.url)
        product_id = product_id_match.group(1) if product_id_match else None

        return ProductInfo(
            name=product_name.strip(),
            current_price=current_price,
            original_price=original_price,
            url=response.url,
            site=self.name,
            stock_status=stock_status,
            product_id=product_id,
        )


class HepsiburadaSpider(BasePriceSpider):
    """Spider for Hepsiburada.com"""

    name = "hepsiburada"
    allowed_domains = ["hepsiburada.com"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.price_processor = AdvancedPriceProcessor()

    def get_default_urls(self) -> List[str]:
        return ["https://www.hepsiburada.com/apple-iphone-15-128-gb-pm-HBC00004E3WIR"]

    def parse_product_page(self, response: scrapy.http.Response) -> ProductInfo:
        name = (
            response.css('h1[data-test-id="product-name"]::text').get()
            or "Unknown Product"
        )
        price_text = response.css('[data-test-id="price-current-price"]::text').get()
        current_price = (
            self.price_processor.process_price(price_text) if price_text else 0.0
        )

        product_id_match = re.search(r"pm-([A-Z0-9]+)", response.url)
        product_id = product_id_match.group(1) if product_id_match else None

        return ProductInfo(
            name=name.strip(),
            current_price=current_price,
            url=response.url,
            site=self.name,
            product_id=product_id,
        )


class AmazonSpider(BasePriceSpider):
    """Spider for Amazon.com.tr (YENİ EKLENTİ)"""

    name = "amazon"
    allowed_domains = ["amazon.com.tr"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.price_processor = AdvancedPriceProcessor()

    def get_default_urls(self) -> List[str]:
        return [
            "https://www.amazon.com.tr/Apple-AirPods-Nesil-Şarj-Kutusu/dp/B0BDK6Z2C3"
        ]

    def parse_product_page(self, response: scrapy.http.Response) -> ProductInfo:
        name_selectors = ["#productTitle::text"]
        product_name = _extract_text(response, name_selectors, "Unknown Product")

        # Güncel Fiyat: Genellikle .a-offscreen içinde gizlidir
        price_selectors = [
            "#corePrice_feature_div .a-offscreen::text",
            ".a-price-whole::text",
        ]
        price_text = _extract_text(response, price_selectors)
        current_price = (
            self.price_processor.process_price(price_text) if price_text else 0.0
        )

        # Orijinal Fiyat: Çizili fiyat
        original_price_selectors = [".a-text-price .a-offscreen::text"]
        original_price_text = _extract_text(response, original_price_selectors)
        original_price = (
            self.price_processor.process_price(original_price_text)
            if original_price_text
            else None
        )

        # ASIN ID'yi URL'den al (10 karakterli)
        product_id_match = re.search(r"(?:/dp/|/gp/product/)(\w{10})", response.url)
        product_id = product_id_match.group(1) if product_id_match else None

        # Stok durumu (basitleştirilmiş)
        stock_text = response.css("#availability span::text").get(default="").lower()
        stock_status = (
            "In Stock"
            if "stokta" in stock_text or current_price > 0
            else "Out of Stock"
        )

        return ProductInfo(
            name=product_name.strip(),
            current_price=current_price,
            original_price=original_price,
            url=response.url,
            site=self.name,
            product_id=product_id,
            stock_status=stock_status,
        )


# ============================================
# FACTORY & RUNNER (Personel 1 & 2 Entegrasyonu)
# ============================================


class DatabasePipeline:
    """CRITICAL: Item'ları doğrudan DataManager'a kaydetmek için Pipeline"""

    def __init__(self, db_manager: PriceDataManager):
        self.db_manager = db_manager

    @classmethod
    def from_crawler(cls, crawler):
        # YENİ MANTIK: Bağlantı tipini (string) settings'ten alın.
        db_type = crawler.settings.get("DB_CONNECTION_TYPE", "SQLite")

        # Modül nesnelerini kopyalama hatasını önlemek için burada PriceDataManager nesnesini oluşturun.
        try:
            db_manager = PriceDataManager(database_type=db_type)
        except Exception as e:
            # Eğer bağlantı başarısız olursa, bir hata fırlatın.
            raise ValueError(f"Failed to initialize PriceDataManager in Pipeline: {e}")

        return cls(db_manager)

    def process_item(self, item, spider):
        # Scrapy Item'ı, DataManager'ın beklediği dict formatına dönüştür
        item_dict = dict(item)

        # Personel 2'nin beklediği formatta kaydet
        success = self.db_manager.save_price_data(item_dict)

        if not success:
            spider.logger.error(
                f"Failed to save item to database: {item_dict['product_name']}"
            )

        return item


class SpiderFactory:
    """Factory for creating spider instances"""

    _spiders = {
        "kitapyurdu": KitapyurduSpider,
        "hepsiburada": HepsiburadaSpider,
        "amazon": AmazonSpider,  # YENİ EKLENDİ
    }

    @classmethod
    def create_spider(cls, site_name: str, urls: Optional[List[str]] = None):
        spider_class = cls._spiders.get(site_name.lower())
        if spider_class:
            return spider_class(urls=urls)
        return None


def _detect_site_from_url(url: str) -> str:
    """Detect site from URL"""
    domain = urlparse(url).netloc.lower()

    if "kitapyurdu" in domain:
        return "kitapyurdu"
    elif "hepsiburada" in domain:
        return "hepsiburada"
    elif "amazon" in domain:
        return "amazon"
    else:
        return "unknown"


def _run_spider(
    spider_class, urls: Optional[List[str]] = None, db_connection_type: str = "SQLite"
):
    """Run a spider and save results using the Database Pipeline."""

    # Data Manager'ı oluştur
    db_manager = PriceDataManager(database_type=db_connection_type)

    settings = {
        "LOG_LEVEL": "INFO",
        "TWISTED_REACTOR": "twisted.internet.selectreactor.SelectReactor",
        "ITEM_PIPELINES": {
            "__main__.DatabasePipeline": 300,  # Yeni Pipeline
        },
        # Pipeline'a Data Manager'ı iletmek için custom setting kullan
        "DB_CONNECTION_TYPE": db_connection_type,
    }

    process = CrawlerProcess(settings)
    process.crawl(spider_class, urls=urls)

    # Blocking call waits until Scrapy completes
    try:
        process.start()
    except Exception as e:
        print(f"Scrapy Process Error: {e}")
        return []

    # Scrapy bittikten sonra istatistikleri yazdır (opsiyonel)
    # process.stop() yapmaya gerek yok, process.start() tamamlandığında durur.

    print("\n✅ Scraped data saved to database.")


# ============================================
# MAIN EXECUTION
# ============================================


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Professional Price Collector")
    parser.add_argument(
        "--site",
        choices=["kitapyurdu", "hepsiburada", "amazon", "multi"],
        default="kitapyurdu",
    )
    parser.add_argument("--urls", help="Comma-separated URLs to scrape")
    parser.add_argument(
        "--db",
        default="SQLite",
        choices=["SQLite", "PostgreSQL", "MongoDB"],
        help="Database type",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("PROFESSIONAL PRICE COLLECTOR (Birleşik Sistem)")
    print("============================================================")

    urls = [u.strip() for u in args.urls.split(",")] if args.urls else None

    if args.site == "multi" and urls:

        # Multi-site: URL'leri siteye göre grupla
        url_map = {}
        for url in urls:
            site = _detect_site_from_url(url)
            if site not in url_map:
                url_map[site] = []
            url_map[site].append(url)

        for site, site_urls in url_map.items():
            spider_class = SpiderFactory._spiders.get(site)
            if spider_class:
                print(f"\nRunning {site.upper()} spider for {len(site_urls)} URLs...")
                _run_spider(spider_class, site_urls, args.db)
            else:
                print(f"⚠️ Warning: No spider found for site: {site}")

    else:
        spider_class = SpiderFactory._spiders.get(args.site)
        if spider_class:
            print(f"Running {args.site.upper()} spider...")
            _run_spider(spider_class, urls, args.db)
        else:
            print(f"Error: Invalid site selected or spider not found: {args.site}")

    print("\n" + "=" * 60)
    print("✅ Price collection and database save completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

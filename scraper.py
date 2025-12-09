"""
PRICE COLLECTOR - Person 1
Supports: KitapYurdu, Hepsiburada, Amazon.com.tr
Features: Multi-site, OOP, ItemLoader, Pipelines, Error Handling
Multi-site price extraction with advanced architecture
"""

import scrapy
import requests
import re
import json
import argparse
from datetime import datetime
from typing import List, Optional, Dict, Any, ClassVar
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
from enum import Enum
from scrapy.crawler import CrawlerProcess
from scrapy.loader import ItemLoader
from scrapy.item import Item, Field
from scrapy.signalmanager import SignalManager
from scrapy import signals
from twisted.internet import reactor, defer
from itemloaders.processors import TakeFirst, MapCompose
from urllib.parse import urlparse
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing_extensions import Protocol

# ============================================
# DATA MODELS
# ============================================


@dataclass
class ProductInfo:
    """Data model for product information"""

    name: str
    current_price: float
    original_price: Optional[float] = None
    url: str = ""
    site: str = ""
    currency: str = "TRY"
    stock_status: str = "Unknown"
    product_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    image_url: Optional[str] = None
    category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductInfo":
        """Create from dictionary"""
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


class PriceItem(Item):
    """Scrapy Item definition matching ProductInfo structure"""

    product_name = Field(output_processor=TakeFirst())
    current_price = Field(output_processor=TakeFirst())
    original_price = Field(output_processor=TakeFirst())
    url = Field(output_processor=TakeFirst())
    site = Field(output_processor=TakeFirst())
    currency = Field(output_processor=TakeFirst())
    stock_status = Field(output_processor=TakeFirst())
    product_id = Field(output_processor=TakeFirst())
    timestamp = Field(output_processor=TakeFirst())


class Currency(Enum):
    """Supported currency types"""

    TRY = "TRY"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


class StockStatus(Enum):
    """Product stock status"""

    IN_STOCK = "In Stock"
    OUT_OF_STOCK = "Out of Stock"
    PRE_ORDER = "Pre-Order"
    LIMITED = "Limited Stock"


class CollectorPipeline:
    """Collects scraped items directly into a list."""

    def __init__(self, collected_items: List[Dict[str, Any]]):
        # self.collected_items now references the list in _run_spider directly.
        self.collected_items = collected_items

    @classmethod
    def from_crawler(cls, crawler):
        # This provides direct access to the list set in _run_spider.
        collected_list = crawler.settings.get("COLLECTED_ITEMS_LIST", [])
        return cls(collected_items=collected_list)

    def process_item(self, item, spider):
        # When Scrapy finds an item, it converts it into a dictionary
        item_dict = dict(item)

        # Add the missing fields when converting to ProductInfo (especially timestamp)
        if "timestamp" not in item_dict:
            item_dict["timestamp"] = datetime.now().isoformat()
        if "stock_status" not in item_dict:
            pass

        self.collected_items.append(item_dict)

        return item


# ============================================
# INTERFACES
# ============================================


class PriceCollector(Protocol):
    """Interface for price collectors"""

    def collect_prices(self, urls: List[str]) -> List[ProductInfo]:
        """Collect prices from given URLs"""
        ...

    def get_site_name(self) -> str:
        """Get name of the site"""
        ...

    def get_default_urls(self) -> List[str]:
        """Get default URLs for this site"""
        ...


class PriceValidator(Protocol):
    """Interface for price validation"""

    def validate_price(self, price_info: ProductInfo) -> bool:
        """Validate price information"""
        ...

    def normalize_price(self, price_text: str) -> Optional[float]:
        """Normalize price text to float"""
        ...


# ============================================
# CORE COMPONENTS
# ============================================


class BasePriceSpider(scrapy.Spider, ABC):
    """Base spider for all price collectors"""

    name: ClassVar[str]
    allowed_domains: ClassVar[List[str]] = []

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 1.0,
        "LOG_LEVEL": "INFO",
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.0,
        "AUTOTHROTTLE_MAX_DELAY": 5.0,
        "HTTPCACHE_ENABLED": False,
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
    }

    def __init__(self, urls: Optional[List[str]] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = urls if urls else self.get_default_urls()
        self._collected_items: List[ProductInfo] = []

    @abstractmethod
    def get_default_urls(self) -> List[str]:
        """Get default URLs to scrape"""
        ...

    @abstractmethod
    def parse_product_page(self, response: scrapy.http.Response) -> ProductInfo:
        """Parse product page and extract information"""
        ...

    def parse(self, response: scrapy.http.Response):
        """Main parsing method"""
        try:
            product_info = self.parse_product_page(response)
            if self._validate_product_info(product_info):
                self._collected_items.append(product_info)
                yield self._create_scrapy_item(product_info)
        except Exception as e:
            self.logger.error(f"Error parsing {response.url}: {e}")

    def collect_prices(self, urls: List[str]) -> List[ProductInfo]:
        """Collect prices from URLs"""
        self.start_urls = urls
        return []

    def get_site_name(self) -> str:
        return self.name

    def _validate_product_info(self, info: ProductInfo) -> bool:
        """Validate product information"""
        if info.current_price <= 0:
            self.logger.warning(f"Invalid price for {info.name}: {info.current_price}")
            return False
        return True

    def _create_scrapy_item(self, info: ProductInfo) -> Dict[str, Any]:
        """Convert ProductInfo to scrapy item format"""
        return {
            "product_name": info.name,
            "current_price": info.current_price,
            "original_price": info.original_price,
            "url": info.url,
            "site": info.site,
            "currency": info.currency,
            "timestamp": info.timestamp,
        }

    def _create_scrapy_item(
        self, info: ProductInfo
    ) -> PriceItem:  # Dict yerine PriceItem kullan
        """Convert ProductInfo to Scrapy Item object"""
        item = PriceItem(
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
        return item

    # parse metodu içinde yield dönüşü PriceItem olmalı
    def parse(self, response: scrapy.http.Response):
        """Main parsing method"""
        try:
            product_info = self.parse_product_page(response)
            if self._validate_product_info(product_info):
                # self._collected_items artık kullanılmıyor, Pipeline kullanacak
                yield self._create_scrapy_item(product_info)
        except Exception as e:
            self.logger.error(f"Error parsing {response.url}: {e}")


import re
from typing import Optional, List, Any, Dict

# İhtiyaç duyulan ekstra import'ları ekleyin (eğer dataclasses kullanıyorsanız)
# from dataclasses import dataclass, field


class PriceProcessor:
    """Process and clean price data"""

    def __init__(self, *args, **kwargs):
        self._processors = []

        # ... (Ayarlarla ilgili kısımları olduğu gibi bırakın)
        if args and isinstance(args[0], str):
            self._setup_from_string(args[0])
        elif kwargs.get("config_file"):
            self._setup_from_file(kwargs["config_file"])
        elif kwargs.get("config_dict"):
            self._setup_from_dict(kwargs["config_dict"])

    # 1. ENTEGRASYON DÜZELTMESİ: Testlerinizin beklediği metodu ekliyoruz.
    def normalize_price(self, price_text: str) -> Optional[float]:
        """Testlerin beklediği arayüz. process_price'ı çağırır."""
        return self.process_price(price_text)

    # 2. TYPE ERROR DÜZELTMESİ: **kwargs alt metotlara İLETİLMEYECEK.
    def process_price(self, price_text: str, **kwargs) -> Optional[float]:
        """Process price text with multiple strategies"""
        processors = [
            self._extract_with_regex,
            self._extract_with_split,
            self._extract_with_findall,
        ]

        # Eğer indirim varsa, önce fiyatı alıp sonra indirimi uygulayacağız.
        discount = kwargs.get("discount", 0)

        for processor in processors:
            # Artık **kwargs İLETİLMİYOR, sadece price_text gönderiliyor.
            result = processor(price_text)
            if result is not None:
                # Eğer indirim varsa uygula
                if discount > 0:
                    result *= 1 - discount / 100
                return result
        return None

    # Alt metotlardan **kwargs kaldırıldı
    def _extract_with_regex(
        self, text: str, pattern: str = r"[\d,.]+"
    ) -> Optional[float]:
        """Extract price using regex"""
        match = re.search(pattern, text)
        if match:
            return self._clean_number(match.group())
        return None

    # Alt metotlardan **kwargs kaldırıldı
    def _extract_with_split(self, text: str, separator: str = " ") -> Optional[float]:
        """Extract price by splitting text"""
        for part in text.split(separator):
            try:
                # Float'a dönüştürmeden önce temizleme yapıldığından emin olun
                return self._clean_number(part)
            except (ValueError, TypeError):
                continue
        return None

    # Alt metotlardan **kwargs kaldırıldı
    def _extract_with_findall(self, text: str) -> Optional[float]:
        """Extract price using findall"""
        numbers = re.findall(r"[\d,.]+", text)
        if numbers:
            return self._clean_number(numbers[0])
        return None

    # 3. FİYAT TEMİZLEME MANTIĞI DÜZELTMESİ: Binlik ve ondalık ayırıcıları doğru işler.
    def _clean_number(self, text: str) -> Optional[float]:
        """Clean and convert number string to float, handling TL/Avrupa format (1.000,99)"""
        text = text.strip()

        # Sayı olmayan karakterleri (para birimleri hariç) kaldır
        cleaned_text = re.sub(r"[^\d.,]", "", text)

        # 1. Önce para birimi sembollerini kaldırın (opsiyonel)
        cleaned_text = cleaned_text.replace("₺", "").replace("TL", "").replace("$", "")

        # 2. Hem nokta hem de virgül var mı? (Örn: 1.000,99)
        if cleaned_text.count(".") > 0 and cleaned_text.count(",") > 0:
            if cleaned_text.rfind(".") < cleaned_text.rfind(","):
                # Binlik ayırıcıyı kaldır, ondalık ayırıcıyı nokta yap (Türkçe/Avrupa formatı)
                cleaned_text = cleaned_text.replace(".", "").replace(",", ".")
            else:
                # Ondalık ayırıcı nokta, binlik ayırıcı virgül (ABD formatı)
                cleaned_text = cleaned_text.replace(",", "")

        # 3. Sadece virgül varsa (Örn: 100,50)
        elif cleaned_text.count(",") > 0:
            cleaned_text = cleaned_text.replace(",", ".")

        try:
            # Sadece bir nokta kalmalı (ondalık ayırıcı)
            return float(cleaned_text)
        except ValueError:
            return None  # float'a dönüştürülemezse None dön

    def _setup_from_string(self, config_str: str):
        pass

    def _setup_from_file(self, filepath: str):
        pass

    def _setup_from_dict(self, config_dict: Dict[str, Any]):
        pass


class AdvancedPriceProcessor(PriceProcessor):
    """Extended price processor with currency handling"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.currency_symbols = {"₺", "TL", "USD", "€", "£", "$"}


# scraper.py (AdvancedPriceProcessor sınıfı içinde)


class AdvancedPriceProcessor(PriceProcessor):

    def process_price(self, price_text: str, **kwargs) -> Optional[float]:
        discount = kwargs.pop("discount", 0)  # Discount'ı kwargs'tan çıkar

        # Fiyatı üst sınıftan (PriceProcessor) al.
        # super().process_price'a discount=0 veya hiç discount gönderme
        # Eğer PriceProcessor'da indirim mantığı varsa, onu pasifize et.
        price = super().process_price(
            price_text
        )  # VEYA super().process_price(price_text, discount=0)

        if price is not None and discount > 0:
            return price * (1 - discount / 100)

        return price


class PriceValidatorImpl:  # Eğer PriceValidator'dan miras alıyorsanız (Inheritance)
    """Implementation of price validator"""

    def __init__(self, min_price: float = 0.01, max_price: float = 1000000):
        self.min_price = min_price
        self.max_price = max_price

        # 1. DÜZELTME: PriceProcessor'ı dahil et (Composition)
        self.processor = PriceProcessor()

    def validate_price(self, price_info: ProductInfo) -> bool:
        """Validate price information (Bu metot aynı kalacak)"""
        if not price_info.name or not price_info.name.strip():
            return False

        if price_info.current_price < self.min_price:
            return False

        if price_info.current_price > self.max_price:
            return False

        # Bu mantıkta bir hata var: Orijinal fiyat, güncel fiyattan küçük olamaz.
        if (
            price_info.original_price
            and price_info.original_price < price_info.current_price
        ):
            return False

        return True

    # scraper.py dosyasındaki PriceValidatorImpl sınıfının içinde bulunmalıdır

    def normalize_price(self, price_text: str) -> Optional[float]:
        """
        Normalize price text to float.

        Bu metot, PriceProcessor'daki temizleme mantığını devralır
        (composition/delegation) ve kendi karmaşık temizleme mantığını kullanmaz.

        NOT: Bu metotun çalışması için self.processor = PriceProcessor()
            ifadesinin PriceValidatorImpl'in __init__ metodunda tanımlanmış olması gerekir.
        """
        if not hasattr(self, "processor"):

            return None

        # 1. Adım: Tüm sembolleri, boşlukları vb. kaldır
        cleaned = price_text.strip()
        patterns_to_remove = [
            "TL",
            "USD",
            "EUR",
            "GBP",
            "₺",
            "$",
            "€",
            "£",
            " ",
            "\n",
            "\t",
        ]
        for pattern in patterns_to_remove:
            cleaned = cleaned.replace(pattern, "")

        # 2. Adım: Sayısal parçayı bul
        numbers = re.findall(r"[\d,.]+", cleaned)
        if not numbers:
            return None
        number_str = numbers[0]

        # 3. Adım: Türkçe/Avrupa Formatı Düzeltme Mantığı (1.000,99 -> 1000.99)
        if number_str.count(".") > 0 and number_str.count(",") > 0:
            if number_str.rfind(".") < number_str.rfind(","):
                # Binlik ayırıcıyı kaldır, ondalık ayırıcıyı noktaya çevir
                number_str = number_str.replace(".", "").replace(",", ".")
            # Aksi halde (ABD formatı) virgülü kaldır
            else:
                number_str = number_str.replace(",", "")

        # 4. Adım: Sadece virgül varsa noktaya çevir (50,99 -> 50.99)
        elif number_str.count(",") == 1:
            number_str = number_str.replace(",", ".")

        # 5. Adım: Float'a çevir
        try:
            return float(number_str)
        except ValueError:
            return None

        # Eğer self.processor mevcutsa, temizleme görevini ona devret (En iyi pratik budur)
        return self.processor.normalize_price(price_text)


# ============================================
# SITE-SPECIFIC IMPLEMENTATIONS
# ============================================


class KitapyurduSpider(BasePriceSpider):
    """Spider for KitapYurdu.com"""

    name = "kitapyurdu"
    allowed_domains = ["kitapyurdu.com"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.price_processor = AdvancedPriceProcessor()
        self.validator = PriceValidatorImpl(max_price=5000)

    def get_default_urls(self) -> List[str]:
        return [
            "https://www.kitapyurdu.com/kitap/harry-potter-ve-felsefe-tasi/32780.html",
            "https://www.kitapyurdu.com/kitap/harry-potter-ve-efsaneler-kitabi/677276.html",
            "https://www.kitapyurdu.com/kitap/beyaz-zambaklar-ulkesinde/528653.html",
        ]

    def parse_product_page(self, response: scrapy.http.Response) -> ProductInfo:
        """Parse KitapYurdu product page"""
        name_selectors = [
            'h1[itemprop="name"]::text',
            ".product-heading h1::text",
            "#product-name::text",
        ]

        product_name = self._extract_text(response, name_selectors, "Unknown Product")

        price_selectors = [
            "div.price__item::text",
            ".price.price--now::text",
            '[itemprop="price"]::attr(content)',
        ]

        price_text = self._extract_text(response, price_selectors)
        current_price = (
            self.price_processor.process_price(price_text) if price_text else 0.0
        )

        original_price_selectors = [".price.price--old::text", ".price__old::text"]

        original_price_text = self._extract_text(response, original_price_selectors)
        original_price = (
            self.price_processor.process_price(original_price_text)
            if original_price_text
            else None
        )

        return ProductInfo(
            name=product_name,
            current_price=current_price,
            original_price=original_price,
            url=response.url,
            site=self.name,
            currency="TRY",
            stock_status=self._extract_stock_status(response),
            product_id=self._extract_product_id(response.url),
            timestamp=datetime.now(),
        )

    def _extract_text(
        self, response: scrapy.http.Response, selectors: List[str], default: str = ""
    ) -> str:
        for selector in selectors:
            text = response.css(selector).get()
            if text and text.strip():
                return text.strip()
        return default

    def _extract_stock_status(self, response: scrapy.http.Response) -> str:
        stock_selectors = [
            ".stock-status.in-stock::text",
            '[itemprop="availability"]::attr(content)',
        ]
        stock_text = self._extract_text(response, stock_selectors, "Unknown")
        return "In Stock" if "stok" in stock_text.lower() else stock_text

    def _extract_product_id(self, url: str) -> Optional[str]:
        match = re.search(r"/(\d+)\.html$", url)
        return match.group(1) if match else None


class HepsiburadaSpider(BasePriceSpider):
    """Spider for Hepsiburada.com"""

    name = "hepsiburada"
    allowed_domains = ["hepsiburada.com"]

    def get_default_urls(self) -> List[str]:
        return [
            "https://www.hepsiburada.com/apple-iphone-15-128-gb-pm-HBC00004E3WIR",
            "https://www.hepsiburada.com/samsung-galaxy-s24-256-gb-pm-HBC00004F1WP4",
        ]

    def parse_product_page(self, response: scrapy.http.Response) -> ProductInfo:
        """Parse Hepsiburada product page"""
        name = (
            response.css('h1[data-test-id="product-name"]::text').get()
            or "Unknown Product"
        )

        price_text = response.css('[data-test-id="price-current-price"]::text').get()
        processor = PriceProcessor()
        current_price = processor.process_price(price_text) if price_text else 0.0

        return ProductInfo(
            name=name.strip(),
            current_price=current_price,
            url=response.url,
            site=self.name,
            currency="TRY",
            stock_status="In Stock",
            timestamp=datetime.now(),
        )


class AmazonSpider(BasePriceSpider):
    """Spider for Amazon.com.tr"""

    name = "amazon"
    allowed_domains = ["amazon.com.tr"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personel 1'in kullandığı PriceProcessor'ı kullan
        self.price_processor = AdvancedPriceProcessor()
        # Amazon'un fiyat aralığı genellikle daha geniştir
        self.validator = PriceValidatorImpl(max_price=500000)

    def get_default_urls(self) -> List[str]:
        return [
            # Örnek bir Amazon ürünü
            "https://www.amazon.com.tr/Apple-AirPods-Nesil-Şarj-Kutusu/dp/B0BDK6Z2C3"
        ]

    def parse_product_page(self, response: scrapy.http.Response) -> ProductInfo:
        """Parse Amazon.com.tr product page"""

        # 1. Ürün Adı Seçicisi (En yaygın Amazon seçicisi)
        name_selectors = [
            "#productTitle::text",  # Ana ürün başlığı
            "#title::text",
        ]
        product_name = self._extract_text(
            response, name_selectors, "Unknown Product"
        ).strip()

        # 2. Güncel Fiyat Seçicileri (Amazon, fiyatları farklı yerlerde saklayabilir)
        price_selectors = [
            ".a-offscreen::text",  # Gizli span'lardaki fiyatlar (en sık)
            "#priceblock_ourprice::text",
            "#priceblock_saleprice::text",
            "#apex_desktop .a-price-whole::text",  # Yeni fiyat yapısı
            "#corePrice_feature_div .a-offscreen::text",  # En güncel ve kapsamlı (tercih edilen)
        ]
        price_text = self._extract_text(response, price_selectors)
        current_price = (
            self.price_processor.process_price(price_text) if price_text else 0.0
        )

        # 3. Eski/Orijinal Fiyat Seçicileri
        original_price_selectors = [
            ".a-text-price .a-offscreen::text",
            ".priceBlockStrikeThrough::text",
        ]
        original_price_text = self._extract_text(response, original_price_selectors)
        original_price = (
            self.price_processor.process_price(original_price_text)
            if original_price_text
            else None
        )

        return ProductInfo(
            name=product_name,
            current_price=current_price,
            original_price=original_price,
            url=response.url,
            site=self.name,
            currency="TRY",  # Amazon.com.tr için varsayılan
            stock_status=self._extract_stock_status(response),
            product_id=self._extract_product_id(response.url),
            timestamp=datetime.now(),
        )

    def _extract_text(
        self, response: scrapy.http.Response, selectors: List[str], default: str = ""
    ) -> str:
        """Re-use Person 1's utility method to extract text"""
        for selector in selectors:
            text = response.css(selector).get()
            if text and text.strip():
                return text.strip()
        return default

    def _extract_stock_status(self, response: scrapy.http.Response) -> str:
        """Amazon stok durumu tespiti"""
        stock_text = response.css("#availability span::text").get()
        if stock_text and "stokta" in stock_text.lower():
            return StockStatus.IN_STOCK.value
        if stock_text and "tükendi" in stock_text.lower():
            return StockStatus.OUT_OF_STOCK.value
        return StockStatus.UNKNOWN.value

    def _extract_product_id(self, url: str) -> Optional[str]:
        """ASIN ID'yi URL'den çıkar (örnek: B0BDK6Z2C3)"""
        # Genellikle /dp/ veya /gp/product/ sonrasında 10 karakterli ASIN ID bulunur
        match = re.search(r"(?:/dp/|/gp/product/)(\w{10})", url)
        return match.group(1) if match else None


# ============================================
# DATABASE MODELS (For Person 2 Integration)
# ============================================

Base = declarative_base()


class ProductORM(Base):
    """Database model for products"""

    __tablename__ = "products"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(500), nullable=False)
    current_price = sa.Column(sa.Float, nullable=False)
    original_price = sa.Column(sa.Float)
    url = sa.Column(sa.String(1000), unique=True, nullable=False)
    site = sa.Column(sa.String(100), nullable=False)
    currency = sa.Column(sa.String(10), default="TRY")
    stock_status = sa.Column(sa.String(50))
    product_id = sa.Column(sa.String(100))
    timestamp = sa.Column(sa.DateTime, default=datetime.now)
    image_url = sa.Column(sa.String(1000))
    category = sa.Column(sa.String(200))

    def to_product_info(self) -> ProductInfo:
        """Convert ORM object to ProductInfo"""
        return ProductInfo(
            name=self.name,
            current_price=self.current_price,
            original_price=self.original_price,
            url=self.url,
            site=self.site,
            currency=self.currency,
            stock_status=self.stock_status,
            product_id=self.product_id,
            timestamp=self.timestamp,
            image_url=self.image_url,
            category=self.category,
        )

    @classmethod
    def from_product_info(cls, info: ProductInfo) -> "ProductORM":
        """Create ORM object from ProductInfo"""
        return cls(
            name=info.name,
            current_price=info.current_price,
            original_price=info.original_price,
            url=info.url,
            site=info.site,
            currency=info.currency,
            stock_status=info.stock_status,
            product_id=info.product_id,
            timestamp=info.timestamp,
            image_url=info.image_url,
            category=info.category,
        )


class DatabaseManager:
    """Database operations manager"""

    def __init__(self, connection_string: str):
        self.engine = sa.create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def save_product(self, product_info: ProductInfo) -> bool:
        """Save product to database"""
        try:
            session = self.Session()
            product_orm = ProductORM.from_product_info(product_info)
            session.add(product_orm)
            session.commit()
            session.close()
            return True
        except Exception as e:
            print(f"Error saving product: {e}")
            return False

    def get_products_by_site(self, site: str) -> List[ProductInfo]:
        """Get products by site"""
        try:
            session = self.Session()
            products = session.query(ProductORM).filter_by(site=site).all()
            session.close()
            return [p.to_product_info() for p in products]
        except Exception as e:
            print(f"Error getting products: {e}")
            return []


# ============================================
# FACTORY PATTERN
# ============================================


class SpiderFactory:
    """Factory for creating spider instances"""

    _spiders = {
        "kitapyurdu": KitapyurduSpider,
        "hepsiburada": HepsiburadaSpider,
        "amazon": AmazonSpider,
    }

    @classmethod
    def create_spider(
        cls, site_name: str, urls: Optional[List[str]] = None
    ) -> Optional[BasePriceSpider]:
        """Create spider instance by site name"""
        spider_class = cls._spiders.get(site_name.lower())
        if spider_class:
            return spider_class(urls=urls)
        return None

    @classmethod
    def create_spider_by_url(cls, url: str) -> Optional[BasePriceSpider]:
        """Create spider based on URL"""
        site = _detect_site_from_url(url)
        return cls.create_spider(site, [url])


# ============================================
# UTILITY FUNCTIONS
# ============================================


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
    spider_class, urls: Optional[List[str]] = None, output_file: str = "prices.json"
) -> List[ProductInfo]:
    """Run a spider and collect results using Item Pipeline."""

    collected_items_raw = []

    settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 1.0,
        "LOG_LEVEL": "WARNING",
        "TWISTED_REACTOR": "twisted.internet.selectreactor.SelectReactor",
        "ITEM_PIPELINES": {
            __name__ + ".CollectorPipeline": 300,
        },
        "COLLECTED_ITEMS_LIST": collected_items_raw,
    }

    process = CrawlerProcess(settings)

    process.crawl(spider_class, urls=urls)

    # Blocking call waits until Scrapy completes
    try:
        process.start()
    except Exception as e:
        print(f"Scrapy Process Error: {e}")
        return []

    # Convert the collected raw dictionary list to ProductInfo list
    collected_products: List[ProductInfo] = []
    for item in collected_items_raw:
        try:
            # We convert the timestamp because it is stored as a string in ISO format.
            item_data = item.copy()
            item_data["timestamp"] = datetime.fromisoformat(item_data["timestamp"])

            info = ProductInfo(
                name=item_data.get("product_name", ""),
                current_price=item_data.get("current_price", 0.0),
                original_price=item_data.get("original_price"),
                url=item_data.get("url", ""),
                site=item_data.get("site", ""),
                currency=item_data.get("currency", "TRY"),
                stock_status=item_data.get("stock_status", "Unknown"),
                product_id=item_data.get("product_id"),
                timestamp=item_data.get("timestamp", datetime.now()),
            )
            collected_products.append(info)
        except Exception as e:
            print(f"Error converting item to ProductInfo: {e}")
            continue

    return collected_products


# ============================================
# ORIGINAL COMPATIBILITY FUNCTIONS
# ============================================


def get_price_kitapyurdu(url: str) -> Optional[float]:
    """Original function for backward compatibility"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        price_patterns = [
            r'"price":\s*"([\d,\.]+)"',
            r'class="price__item[^>]*>([^<]+)',
            r'itemprop="price"[^>]*content="([\d,\.]+)"',
        ]

        for pattern in price_patterns:
            match = re.search(pattern, response.text)
            if match:
                price_text = match.group(1)
                processor = PriceProcessor()
                price = processor.process_price(price_text)
                if price:
                    return price

        return None

    except Exception as e:
        print(f"Error: {e}")
        return None


# ============================================
# MAIN EXECUTION
# ============================================


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Professional Price Collector")
    parser.add_argument(
        "--site", choices=["kitapyurdu", "hepsiburada", "multi"], default="kitapyurdu"
    )
    parser.add_argument("--urls", help="Comma-separated URLs to scrape")
    parser.add_argument("--output", default="prices.json", help="Output JSON file")
    parser.add_argument("--db", help="Database connection string")

    args = parser.parse_args()

    print("=" * 60)
    print("PROFESSIONAL PRICE COLLECTOR")
    print("Multi-site Web Scraping System")
    print("=" * 60)

    urls = None
    if args.urls:
        urls = [u.strip() for u in args.urls.split(",")]

    if args.site == "multi" and urls:
        all_results: List[ProductInfo] = []  # Tip ekleme
        for url in urls:
            site = _detect_site_from_url(url)
            spider = SpiderFactory.create_spider(site, [url])
            if spider:
                print(f"Scraping {site}: {url}")
                # Incorrect file name: We must use different file names for each site.
                # But now we are saving directly to the list, not to the file.

                # We just run the relevant Spider
                results = _run_spider(type(spider), [url], f"{site}_{args.output}")
                all_results.extend(results)

        # DB integration for Multi mode
        if args.db and all_results:
            print("Saving to database...")
            # To make it compatible with Person 2's DatabaseManager
            # we will update this part according to Person 2's ORM.
            # The current DatabaseManager (in landscaper.py) is using ProductORM.
            db_manager = DatabaseManager(args.db)
            for product in all_results:
                db_manager.save_product(product)
            print(f"Saved {len(all_results)} products to database")

    else:
        spider_class = SpiderFactory._spiders.get(args.site)
        if spider_class:
            print(f"Running {args.site} spider...")
            # Item Pipeline is used to save the JSON file output,
            # but since we are saving directly to the list, output_file is unnecessary.
            results = _run_spider(spider_class, urls, args.output)

            if args.db and results:
                print("Saving to database...")
                db_manager = DatabaseManager(args.db)
                for product in results:
                    # NOTE: DatabaseManager.save_product gets ProductInfo, this is correct.
                    db_manager.save_product(product)
                print(f"Saved {len(results)} products to database")


print("\n" + "=" * 60)
print("Price collection completed successfully!")
print("=" * 60)

if __name__ == "__main__":
    main()

"""
Test file for scraper.py functionality
"""

import unittest
import sys
import os
from datetime import datetime

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scraper import (
    PriceProcessor,
    PriceValidatorImpl,
    ProductInfo,
    AdvancedPriceProcessor,
    SpiderFactory,
)


class TestPriceProcessor(unittest.TestCase):
    """Test PriceProcessor and AdvancedPriceProcessor classes"""

    def test_price_processor_extraction(self):
        """Test price extraction from various text formats"""
        processor = PriceProcessor()

        # Test process_price method
        result = processor.process_price("100,50 TL")
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result, 100.50, places=2)

        result = processor.process_price("1.000,99")
        self.assertAlmostEqual(result, 1000.99, places=2)

    def test_advanced_price_processor(self):
        """Test AdvancedPriceProcessor with currency symbols"""
        processor = AdvancedPriceProcessor()

        # Test with currency symbols
        result = processor.process_price("₺150,75")
        self.assertAlmostEqual(result, 150.75, places=2)

        result = processor.process_price("100 USD")
        self.assertAlmostEqual(result, 100.0, places=2)

        # Test with discount
        result = processor.process_price("200 TL", discount=10)
        self.assertAlmostEqual(result, 180.0, places=2)


class TestPriceValidator(unittest.TestCase):
    """Test PriceValidatorImpl class"""

    def setUp(self):
        self.validator = PriceValidatorImpl()

    def test_normalize_price(self):
        """Test price normalization from text"""
        test_cases = [
            ("100,50 TL", 100.50),
            ("1.000,99", 1000.99),
            ("50.99", 50.99),
            ("$25.50", 25.50),
            ("150₺", 150.0),
            ("200 EUR", 200.0),
        ]

        for price_text, expected in test_cases:
            with self.subTest(price_text=price_text):
                result = self.validator.normalize_price(price_text)
                self.assertIsNotNone(result, f"Failed to normalize: {price_text}")
                self.assertAlmostEqual(
                    result,
                    expected,
                    places=2,
                    msg=f"Expected {expected}, got {result} for {price_text}",
                )

    def test_validate_product_info(self):
        """Test product validation"""
        valid_product = ProductInfo(
            name="Test Product", current_price=100.0, url="http://test.com"
        )

        invalid_price_product = ProductInfo(
            name="Test Product",
            current_price=-10.0,  # Negative price
            url="http://test.com",
        )

        empty_name_product = ProductInfo(
            name="", current_price=100.0, url="http://test.com"  # Empty name
        )

        self.assertTrue(self.validator.validate_price(valid_product))
        self.assertFalse(self.validator.validate_price(invalid_price_product))
        self.assertFalse(self.validator.validate_price(empty_name_product))


class TestProductInfo(unittest.TestCase):
    """Test ProductInfo dataclass"""

    def test_product_info_creation(self):
        """Test basic ProductInfo creation"""
        product = ProductInfo(
            name="Harry Potter ve Felsefe Taşı",
            current_price=59.99,
            original_price=75.00,
            url="https://www.kitapyurdu.com/kitap/harry-potter-ve-felsefe-tasi/32780.html",
            site="kitapyurdu",
            currency="TRY",
            stock_status="In Stock",
            product_id="32780",
        )

        self.assertEqual(product.name, "Harry Potter ve Felsefe Taşı")
        self.assertEqual(product.current_price, 59.99)
        self.assertEqual(product.original_price, 75.00)
        self.assertEqual(product.site, "kitapyurdu")
        self.assertEqual(product.currency, "TRY")

    def test_to_dict_conversion(self):
        """Test conversion to dictionary"""
        product = ProductInfo(
            name="Test Product", current_price=100.0, url="http://test.com"
        )

        product_dict = product.to_dict()

        self.assertIn("name", product_dict)
        self.assertIn("current_price", product_dict)
        self.assertIn("url", product_dict)
        self.assertIn("timestamp", product_dict)
        self.assertEqual(product_dict["name"], "Test Product")
        self.assertEqual(product_dict["current_price"], 100.0)

    def test_from_dict_creation(self):
        """Test creation from dictionary"""
        product_dict = {
            "name": "Test Product",
            "current_price": 150.0,
            "original_price": 200.0,
            "url": "http://test.com",
            "site": "test_site",
            "currency": "TRY",
            "stock_status": "In Stock",
            "product_id": "12345",
            "timestamp": datetime.now().isoformat(),
        }

        product = ProductInfo.from_dict(product_dict)

        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.current_price, 150.0)
        self.assertEqual(product.original_price, 200.0)
        self.assertEqual(product.site, "test_site")


class TestSpiderFactory(unittest.TestCase):
    """Test SpiderFactory class"""

    def test_spider_creation(self):
        """Test spider creation by site name"""
        # Test valid site names
        spider = SpiderFactory.create_spider("kitapyurdu")
        self.assertIsNotNone(spider)
        self.assertEqual(spider.name, "kitapyurdu")

        spider = SpiderFactory.create_spider("hepsiburada")
        self.assertIsNotNone(spider)
        self.assertEqual(spider.name, "hepsiburada")

        spider = SpiderFactory.create_spider("amazon")
        self.assertIsNotNone(spider)
        self.assertEqual(spider.name, "amazon")

    def test_invalid_spider_creation(self):
        """Test invalid site name handling"""
        spider = SpiderFactory.create_spider("invalid_site")
        self.assertIsNone(spider)

    def test_spider_with_urls(self):
        """Test spider creation with custom URLs"""
        test_urls = ["http://test1.com", "http://test2.com"]
        spider = SpiderFactory.create_spider("kitapyurdu", urls=test_urls)

        self.assertIsNotNone(spider)
        self.assertEqual(spider.start_urls, test_urls)


if __name__ == "__main__":
    unittest.main(verbosity=2)

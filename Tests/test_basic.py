# tests/test_basic.py
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath("."))

from scraper import PriceProcessor, ProductInfo


class TestPriceProcessor(unittest.TestCase):
    def test_price_normalization(self):
        """Test various price formats."""
        processor = PriceProcessor()

        test_cases = [
            ("100,50 TL", 100.50),
            ("1.000,99", 1000.99),
            ("50.99", 50.99),
            ("$25.50", 25.50),
        ]

        for price_text, expected in test_cases:
            with self.subTest(price_text=price_text):
                result = processor.normalize_price(price_text)
                self.assertAlmostEqual(result, expected, places=2)


class TestProductInfo(unittest.TestCase):
    def test_dataclass_creation(self):
        """Test ProductInfo dataclass."""
        product = ProductInfo(
            name="Test Product",
            current_price=99.99,
            url="http://test.com",
            site="test_site",
        )

        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.current_price, 99.99)
        self.assertEqual(product.site, "test_site")


if __name__ == "__main__":
    unittest.main()

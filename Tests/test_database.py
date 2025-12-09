"""
Test file for data_manager.py functionality
"""

import unittest
import sys
import os
from datetime import datetime, timezone
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_manager import ProductInfo, PriceDataManager, Product, PriceHistory, Base


class TestDataManagerSQLite(unittest.TestCase):
    """Test PriceDataManager with SQLite"""

    def setUp(self):
        # Create a temporary database for testing
        self.test_db_path = tempfile.mktemp(suffix=".db")
        self.db_manager = PriceDataManager(
            database_type="SQLite", database_name=self.test_db_path.replace(".db", "")
        )

    def tearDown(self):
        # 1. Eğer bir veritabanı oturumu hala açıksa kapatın
        if hasattr(self, "db_manager") and hasattr(self.db_manager, "SessionLocal"):
            # Çalışan oturumları kapatmayı deneyin. Bu SQLAlchemy'nin çalışma şekline bağlıdır.
            pass  # Eğer get_db_session() with ile kullanılıyorsa genelde gerekmez

        # 2. Motoru yok edin
        if hasattr(self.db_manager, "engine"):
            self.db_manager.engine.dispose()

        # 3. Dosyayı silmeyi tekrar deneyin.
        if os.path.exists(self.test_db_path):
            import time

            time.sleep(
                0.05
            )  # Küçük bir bekleme süresi, dosya kilidinin serbest kalmasına yardımcı olabilir
            try:
                os.remove(self.test_db_path)
            except Exception as e:
                print(f"Uyarı: Dosya silinemedi: {e}")

    def test_save_price_data(self):
        """Test saving price data to database"""
        test_data = {
            "product_name": "Test Product",
            "current_price": 99.99,
            "original_price": 129.99,
            "url": "https://test.com/product/123",
            "site": "test_site",
            "currency": "TRY",
            "stock_status": "In Stock",
            "product_id": "TEST123",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "category": "Electronics",
            "image_url": "https://test.com/image.jpg",
        }

        # Save data
        result = self.db_manager.save_price_data(test_data)
        self.assertTrue(result, "Failed to save price data")

    def test_database_tables_created(self):
        """Test if database tables are created properly"""
        with self.db_manager.get_db_session() as db:
            # Check if tables exist by querying them
            products = db.query(Product).all()
            price_history = db.query(PriceHistory).all()

            # Tables should be accessible (empty at first)
            self.assertIsNotNone(products)
            self.assertIsNotNone(price_history)

    def test_product_orm(self):
        """Test Product ORM model (ve created_at otomatik doldurma)"""
        product = Product(
            product_id="TEST456",
            name="Test Product ORM",
            url="https://test.com/orm",
            site="test_site",
            category="Books",
            image_url="https://test.com/orm.jpg",
        )

        self.assertEqual(product.product_id, "TEST456")
        self.assertEqual(product.name, "Test Product ORM")

        # Yeni bir session açın
        with self.db_manager.get_db_session() as db:
            db.add(product)
            db.commit()  # Kaydetme (created_at'in atanması için zorunlu)

            # Objenin veritabanından yeniden yüklenmesi (bu, created_at'i kesinleştirir)
            reloaded_product = db.query(Product).filter_by(product_id="TEST456").first()

            # created_at'in boş olmadığını kontrol et
            self.assertIsNotNone(reloaded_product.created_at)


class TestProductInfoIntegration(unittest.TestCase):
    """Test ProductInfo integration with database"""

    def test_product_info_to_dict_for_db(self):
        """Test ProductInfo conversion to dict for database"""
        product_info = ProductInfo(
            name="Integration Test Product",
            current_price=250.50,
            original_price=300.00,
            url="https://integration-test.com",
            site="integration_site",
            currency="USD",
            stock_status="Limited Stock",
            product_id="INTEG123",
            category="Home",
            image_url="https://integration-test.com/image.jpg",
        )

        data_dict = product_info.to_dict()

        # Check required fields for database
        self.assertIn("product_name", data_dict)
        self.assertIn("current_price", data_dict)
        self.assertIn("url", data_dict)
        self.assertIn("timestamp", data_dict)

        # Check values
        self.assertEqual(data_dict["product_name"], "Integration Test Product")
        self.assertEqual(data_dict["current_price"], 250.50)
        self.assertEqual(data_dict["site"], "integration_site")
        self.assertEqual(data_dict["currency"], "USD")


if __name__ == "__main__":
    unittest.main(verbosity=2)

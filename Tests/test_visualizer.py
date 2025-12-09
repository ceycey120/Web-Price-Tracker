"""
Test file for visualizer.py functionality
"""

import unittest
import sys
import os
import json
import pandas as pd
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from visualizer import (
    PriceVisualizer,
    PriceChartVisualizer,
    PriceTableVisualizer,
    AnalysisDataLoader,
    ChartConfig,
    TableConfig,
)


class TestChartVisualizer(unittest.TestCase):
    """Test PriceChartVisualizer class"""

    def setUp(self):
        self.visualizer = PriceChartVisualizer()

        # Create sample data
        self.sample_df = pd.DataFrame(
            {
                "product_name": ["Product A", "Product A", "Product B", "Product B"],
                "product_id": ["A001", "A001", "B001", "B001"],
                "site": ["Site1", "Site1", "Site2", "Site2"],
                "current_price": [100.0, 105.0, 200.0, 195.0],
                "timestamp": [
                    datetime.now() - timedelta(days=3),
                    datetime.now() - timedelta(days=2),
                    datetime.now() - timedelta(days=3),
                    datetime.now() - timedelta(days=2),
                ],
            }
        )

    def test_price_history_chart_creation(self):
        """Test price history chart creation"""
        fig = self.visualizer.create_price_history_chart(self.sample_df, "Product A")

        self.assertIsNotNone(fig)
        # Check if figure has data
        self.assertGreater(len(fig.data), 0)

    def test_comparison_chart_creation(self):
        """Test comparison chart creation"""
        fig = self.visualizer.create_comparison_chart(
            self.sample_df, ["Product A", "Product B"]
        )

        self.assertIsNotNone(fig)

    def test_price_distribution_chart(self):
        """Test price distribution chart"""
        fig = self.visualizer.create_price_distribution_chart(self.sample_df)

        self.assertIsNotNone(fig)
        self.assertEqual(fig.data[0].type, "histogram")


class TestTableVisualizer(unittest.TestCase):
    """Test PriceTableVisualizer class"""

    def setUp(self):
        self.visualizer = PriceTableVisualizer()

        # Sample analysis data
        self.sample_analysis = {
            "product_name": "Test Product",
            "site": "test_site",
            "current_price": 99.99,
            "previous_price": 109.99,
            "price_change_percent": -9.09,
            "average_price": 104.99,
            "minimum_price": 89.99,
            "maximum_price": 119.99,
            "trend_direction": "down",
            "alert_level": "good_deal",
            "recommendation": "Good time to buy",
            "confidence_score": 85.5,
        }

    def test_analysis_table_creation(self):
        """Test analysis table creation"""
        table = self.visualizer.create_analysis_table(self.sample_analysis)

        self.assertIsInstance(table, str)
        self.assertGreater(len(table), 0)

        # Check if important information is in the table
        self.assertIn("Test Product", table)
        self.assertIn("99.99", table)
        self.assertIn("good_deal", table)

    def test_price_history_table(self):
        """Test price history table creation"""
        # Create sample DataFrame
        df = pd.DataFrame(
            {
                "product_name": ["Product A", "Product A"],
                "site": ["Site1", "Site1"],
                "current_price": [100.0, 105.0],
                "timestamp": [datetime.now(), datetime.now()],
            }
        )

        table = self.visualizer.create_price_history_table(df, "Product A")

        self.assertIsInstance(table, str)
        self.assertGreater(len(table), 0)
        self.assertIn("Product A", table)
        self.assertIn("100.0", table)


class TestDataLoader(unittest.TestCase):
    """Test AnalysisDataLoader class"""

    def test_chart_config_dataclass(self):
        """Test ChartConfig dataclass"""
        config = ChartConfig(
            title="Test Chart", width=800, height=600, theme="plotly_dark"
        )

        self.assertEqual(config.title, "Test Chart")
        self.assertEqual(config.width, 800)
        self.assertEqual(config.height, 600)
        self.assertEqual(config.theme, "plotly_dark")
        self.assertIsNotNone(config.colors)

    def test_table_config_dataclass(self):
        """Test TableConfig dataclass"""
        config = TableConfig(
            headers=["Name", "Price", "Date"],
            format="github",
            show_index=True,
            float_format=".3f",
        )

        self.assertEqual(config.headers, ["Name", "Price", "Date"])
        self.assertEqual(config.format, "github")
        self.assertTrue(config.show_index)
        self.assertEqual(config.float_format, ".3f")


class TestMainVisualizer(unittest.TestCase):
    """Test main PriceVisualizer class"""

    def test_visualizer_initialization(self):
        """Test PriceVisualizer initialization"""
        # This test checks if visualizer can be initialized without errors
        try:
            visualizer = PriceVisualizer()
            # If we get here, initialization succeeded
            self.assertIsNotNone(visualizer)
            self.assertIsNotNone(visualizer.data_loader)
            self.assertIsNotNone(visualizer.chart_viz)
            self.assertIsNotNone(visualizer.table_viz)
        except Exception as e:
            self.fail(f"Visualizer initialization failed: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

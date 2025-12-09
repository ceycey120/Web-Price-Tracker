"""
Test file for analyzer.py functionality
"""

import unittest
import sys
import os
import json
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyzer import (
    PriceAnalyzer,
    RealDatabaseAdapter,
    PriceAnalysis,
    TrendDirection,
    AlertLevel,
    MovingAverageStrategy,
    PercentageChangeStrategy,
    VolatilityStrategy,
)


class TestAnalysisStrategies(unittest.TestCase):
    """Test analysis strategy classes"""

    def test_moving_average_strategy(self):
        """Test MovingAverageStrategy"""
        strategy = MovingAverageStrategy(short_window=3, long_window=7)

        # Upward trend (recent prices higher)
        prices_up = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118]
        trend, confidence = strategy.analyze(prices_up)
        self.assertEqual(trend, TrendDirection.UP)
        self.assertGreater(confidence, 0.5)

        # Downward trend
        prices_down = [120, 118, 116, 114, 112, 110, 108, 106, 104, 102]
        trend, confidence = strategy.analyze(prices_down)
        self.assertEqual(trend, TrendDirection.DOWN)

    def test_percentage_change_strategy(self):
        """Test PercentageChangeStrategy"""
        strategy = PercentageChangeStrategy(threshold_percent=5.0)

        # Significant increase
        prices_increase = [100, 100, 100, 100, 100, 110]  # +10%
        trend, confidence = strategy.analyze(prices_increase)
        self.assertEqual(trend, TrendDirection.UP)

        # Significant decrease
        prices_decrease = [100, 100, 100, 100, 100, 90]  # -10%
        trend, confidence = strategy.analyze(prices_decrease)
        self.assertEqual(trend, TrendDirection.DOWN)

        # Stable (within threshold)
        prices_stable = [100, 100, 100, 100, 100, 102]  # +2%
        trend, confidence = strategy.analyze(prices_stable)
        self.assertEqual(trend, TrendDirection.STABLE)

    def test_volatility_strategy(self):
        """Test VolatilityStrategy"""
        strategy = VolatilityStrategy(volatility_threshold=0.05)

        # Volatile prices
        prices_volatile = [100, 110, 90, 105, 95, 115, 85]
        trend, confidence = strategy.analyze(prices_volatile)
        self.assertEqual(trend, TrendDirection.VOLATILE)

        # Stable prices
        prices_stable = [100, 101, 99, 100, 101, 99, 100]
        trend, confidence = strategy.analyze(prices_stable)
        self.assertEqual(trend, TrendDirection.STABLE)


class TestPriceAnalysisDataclass(unittest.TestCase):
    """Test PriceAnalysis dataclass"""

    def test_price_analysis_creation(self):
        """Test PriceAnalysis creation"""
        analysis = PriceAnalysis(
            product_name="Test Product",
            product_id="TEST123",
            url="http://test.com",
            site="test_site",
            current_price=150.0,
            currency="TRY",
            previous_price=200.0,
            average_price=175.0,
            minimum_price=100.0,
            maximum_price=250.0,
            price_change_percent=-25.0,
            price_change_amount=-50.0,
            trend_direction=TrendDirection.DOWN,
            alert_level=AlertLevel.CRITICAL_DROP,
            recommendation="Buy now!",
            confidence_score=85.5,
            analysis_date=datetime.now(),
            data_points_count=30,
        )

        self.assertEqual(analysis.product_name, "Test Product")
        self.assertEqual(analysis.current_price, 150.0)
        self.assertEqual(analysis.price_change_percent, -25.0)
        self.assertEqual(analysis.trend_direction, TrendDirection.DOWN)
        self.assertEqual(analysis.alert_level, AlertLevel.CRITICAL_DROP)
        self.assertGreater(analysis.confidence_score, 0)

    def test_to_dict_conversion(self):
        """Test conversion to dictionary"""
        analysis = PriceAnalysis(
            product_name="Test",
            product_id="TEST",
            url="http://test.com",
            site="test",
            current_price=100.0,
            currency="TRY",
            previous_price=100.0,
            average_price=100.0,
            minimum_price=100.0,
            maximum_price=100.0,
            price_change_percent=0.0,
            price_change_amount=0.0,
            trend_direction=TrendDirection.STABLE,
            alert_level=AlertLevel.FAIR_PRICE,
            recommendation="Test",
            confidence_score=50.0,
            analysis_date=datetime.now(),
            data_points_count=10,
        )

        analysis_dict = analysis.to_dict()

        # Check all required fields
        required_fields = [
            "product_name",
            "product_id",
            "url",
            "site",
            "current_price",
            "currency",
            "previous_price",
            "average_price",
            "minimum_price",
            "maximum_price",
            "price_change_percent",
            "price_change_amount",
            "trend_direction",
            "alert_level",
            "recommendation",
            "confidence_score",
            "analysis_date",
            "data_points_count",
        ]

        for field in required_fields:
            self.assertIn(field, analysis_dict)

        # Check JSON serialization
        json_str = json.dumps(analysis_dict)
        self.assertIsInstance(json_str, str)


class TestAlertLevelDetermination(unittest.TestCase):
    """Test alert level determination logic"""

    def test_critical_drop(self):
        """Test critical drop detection"""
        analyzer = PriceAnalyzer(None)

        # >20% drop should be CRITICAL_DROP
        alert_level = analyzer._determine_alert_level(
            change_percent=-25.0,
            current_price=75.0,
            average_price=100.0,
            minimum_price=70.0,
            maximum_price=150.0,
        )
        self.assertEqual(alert_level, AlertLevel.CRITICAL_DROP)

    def test_good_deal(self):
        """Test good deal detection"""
        analyzer = PriceAnalyzer(None)

        # >10% drop should be GOOD_DEAL
        alert_level = analyzer._determine_alert_level(
            change_percent=-15.0,
            current_price=85.0,
            average_price=100.0,
            minimum_price=80.0,
            maximum_price=120.0,
        )
        self.assertEqual(alert_level, AlertLevel.GOOD_DEAL)

    def test_fair_price(self):
        """Test fair price detection"""
        analyzer = PriceAnalyzer(None)

        # Within ±5% change and close to average
        alert_level = analyzer._determine_alert_level(
            change_percent=2.0,
            current_price=102.0,
            average_price=100.0,
            minimum_price=90.0,
            maximum_price=110.0,
        )
        self.assertEqual(alert_level, AlertLevel.FAIR_PRICE)


if __name__ == "__main__":
    unittest.main(verbosity=2)

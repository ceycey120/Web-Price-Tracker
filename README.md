# 🚀 Web Price Tracker: Advanced Price Monitoring and Analysis System

**Project Name:** Web Price Tracker

**Version:** 1.0.0

---

# 📊 Project Overview

This system is a multi-module application designed to asynchronously **collect price data** from specified e-commerce platforms, **chronologically store** it in a central **SQLAlchemy/SQLite** database, and execute advanced financial analysis on the collected data.

The system is built on core OOP principles and consists of four main modules:

- **Scraper Module** - Data Collection
- **DataManager Module** - Data Management
- **Analyzer Module** - Business Logic and Analysis
- **Visualizer Module** - Visualization

---

# 🎯 Code Complexity and Bonus Point Criteria

Our project utilizes advanced techniques that exceed minimum requirements and aim for maximum bonus points:

### A. Advanced OOP Implementations

- **Abstract Class Usage:** Base interfaces for price scraping (`BasePriceSpider`) and price analysis (`AnalysisStrategy`) are defined using **Abstract Classes**, derived from Python's `abc.ABC` module.
- **Dataclasses and Full Type Checking:** Central data structures like `ProductInfo` and `PriceAnalysis` are implemented as **Python Dataclasses**, and the entire codebase adheres to the Full Type Checking standard using **Type Hints**.
- **Strategy Pattern:** The **Strategy Pattern** is used to make analysis algorithms flexible and interchangeable.

### B. Technology Choice and Performance

- **Data Collection:** Instead of simple requests or BeautifulSoup, **Scrapy** is preferred for its asynchronous and highly configurable nature.
- **Database:** A robust ORM layer (**SQLAlchemy**) is used to manage the database schema via Python code.

---

# 🧩 Detailed Technology Distribution by Module

The strength of the project architecture comes from using modern libraries for the right purpose in each module.

### 3.1 Scraper Module (Data Collection)

| Technology / Class   | Role and Function                                                                                                                                       |
| :------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Scrapy Framework** | High-performance, event-driven data collection engine. Its asynchronous structure allows for simultaneous scraping of multiple sites.                   |
| **Custom Spiders**   | Contains site-specific scraping logic (e.g., `KitapyurduSpider`). Inherits from `BasePriceSpider`.                                                      |
| **PriceProcessor**   | Converts raw price strings (e.g., "1.000,99 TL"), which contain currency and decimal separators, into a standard numerical (float) format for analysis. |

### 3.2 DataManager Module (Data Management)

| Technology / Class                     | Role and Function                                                                                                                          |
| :------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------- |
| **SQLAlchemy ORM**                     | Bridge layer that manages database operations using object-oriented Python classes. Reduces SQL injection risks and speeds up development. |
| **SQLite3**                            | Local and lightweight persistent data storage solution for the development environment.                                                    |
| **Models** (`Product`, `PriceHistory`) | Data schemas managed by the ORM. Represents fields for price, date, and product information.                                               |

### 3.3 Analyzer Module (Analysis and Business Logic)

| Technology / Class   | Role and Function                                                                                                                                                                   |
| :------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **pandas**           | Converts collected price history series (`PriceHistory` data) into a **DataFrame** structure, enabling fast and efficient time-series analysis (e.g., Moving Average calculations). |
| **NumPy**            | Used for fundamental mathematical and statistical calculations, such as Standard Deviation. Required particularly for the Volatility Strategy.                                      |
| **AnalysisStrategy** | Implements the Strategy Pattern interface. Produces outputs like trend direction and alert level (`AlertLevel`).                                                                    |

### 3.4 Visualizer Module (Visualization)

| Technology / Class       | Role and Function                                                                                                                         |
| :----------------------- | :---------------------------------------------------------------------------------------------------------------------------------------- |
| **plotly** (Recommended) | Creates **interactive, dynamic charts** (Moving Average charts, candlestick charts, etc.) using the price history data from the database. |
| **pandas**               | Used for filtering and preparing data before visualization.                                                                               |

---

# 🧠 Analysis Strategies (Analyzer Module Detail)

The Analyzer module is designed using the **Strategy Pattern**. Some of the analysis strategies and their purposes:

### 1. Moving Average Strategy (`MovingAverageStrategy`)

Compares the short-term (3-day) average with the long-term (7-day) average to determine the general price trend direction (**UP** or **DOWN**).

### 2. Volatility Strategy (`VolatilityStrategy`)

Calculates the percentage fluctuation by ratioing the **Standard Deviation** of the price history to the average price.

### 3. Percentage Change Strategy (`PercentageChangeStrategy`)

Calculates the percentage change of the current price relative to the historical average. This is the core metric for determining alert levels like `AlertLevel.CRITICAL_DROP`.

---

# 🛡️ Code Robustness and Test Coverage

Targeted Code Robustness (Criterion 4) is proven by a comprehensive test suite.

### A. Test Status

- **Test Framework:** `pytest`
- **Total Tests:** 32 (Full functional coverage)
- **Pylint Score:** **8.58 / 10** (High-Quality Approval)
- **Test Status:** All tests passed successfully ✅

### B. Test Coverage

- **Integration Tests:** SQLAlchemy ORM data integration
- **Unit Tests:** Separate tests for each module
- **Edge Case Tests:** Negative values, missing data, special characters
- **Performance Tests:** Analysis performance on large datasets

### C. Running Tests

```bash
python -m pytest Tests/ -v
```

# ⚙️ Setup and Run Guide

- **Requirements**

Python 3.9+

pip (Python package installer)

- **Step 1: Installation**
  Bash

```
# Install dependencies
pip install -r requirements.txt
```

- **Step 2: Data Collection (Scraping)**
  Bash

```
# Creates the database and collects price data
python scraper.py
```

- **Step 3: Analysis and Reporting**
  Bash

```
# Performs analysis on the collected data and generates reports
python analyzer.py
```

- **Step 4: Visualization (Optional)**
  Bash

```
# Creates price charts
python visualizer.py
```

# 📁 Project Structure

Web-Price-Tracker/

├── scraper.py # Main scraping script

├── spiders/ # Scrapy spiders

│ ├── **init**.py

│ ├── base_spider.py # BasePriceSpider

│ ├── kitapyurdu_spider.py

│ └── amazon_spider.py

├── price_processor.py # Price processing and normalization

├── models.py # SQLAlchemy data models

├── data_manager.py # Database operations

├── analyzer.py # Analysis strategies

├── visualizer.py # Visualization tools

├── config.py # Configuration settings

├── utils/ # Helper functions

│ ├── **init**.py

│ └── helpers.py

├── Tests/ # Test files

│ ├── test_scraper.py

│ ├── test_models.py

│ ├── test_analyzer.py

│ └── test_integration.py

├── requirements.txt # Python dependencies

├── database.db # SQLite database (will be created)

├── logs/ # Log files

└── README.md # This file

- # **🔧 Features**

- ✅ Multi-e-commerce site support

- ✅ Asynchronous data collection

- ✅ Data management with SQLAlchemy ORM

- ✅ Multiple analysis strategies

- ✅ Full type checking (Type Hints)

- ✅ Comprehensive test coverage

- ✅ High code quality (Pylint 8.58/10)

- ✅ Flexible and extensible architecture
- ✅ Detailed logging system

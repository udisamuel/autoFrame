# Automation Testing Framework

![Logo](autoFrame_logo_compressed.jpg)

A comprehensive and modular Python-based testing framework for automating API, UI, database, and AWS integration tests, with robust reporting capabilities.

## 🧰 Overview

This automation framework provides a unified approach to testing various components of your application stack, including:
- API testing with request validation and response assertions
- UI testing using Playwright for browser automation
- Database testing with PostgreSQL and ClickHouse support
- AWS services integration testing
- Comprehensive reporting using Allure

## 🌟 Features

- **Modular Design**: Easily extendable for various testing needs
- **Cross-platform**: Works on any OS that supports Python
- **Reliable Reporting**: Detailed reports with Allure, including screenshots and logs
- **Environment-agnostic**: Use configuration files and environment variables for flexible deployment
- **Comprehensive Helpers**:
  - API testing with request and response validation
  - Database interactions with PostgreSQL and ClickHouse
  - AWS service interactions with S3 and more
  - Web UI automation with Playwright

## 📋 Requirements

- Python 3.11+
- Dependencies as listed in `requirements.txt`

## 🚀 Installation

1. Clone the repository
```bash
git clone <repository-url>
cd automation_framework
```

2. Create and activate a virtual environment
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers
```bash
playwright install
```

5. Install Allure command-line tool (optional, for report viewing)
```bash
# macOS
brew install allure

# Ubuntu
sudo apt-add-repository ppa:qameta/allure
sudo apt-get update
sudo apt-get install allure

# Windows
scoop install allure
```

## ⚙️ Configuration

1. Create a `.env` file from the provided example:
```bash
cp .env.example .env
```

2. Update the `.env` file with your specific configuration values

Configuration options include:
- Browser settings (type, headless mode)
- API endpoints
- Database connection details
- AWS credentials and region
- Timeouts and other test parameters

## 🔬 Running Tests

### Running all tests
```bash
pytest
```

### Running specific test types
```bash
# Run API tests
pytest -m api

# Run database tests
pytest -m database

# Run AWS tests
pytest -m aws

# Run UI tests
pytest -m ui
```

### Running tests with specific markers
```bash
# Run integration tests
pytest -m integration

# Run regression tests
pytest -m regression
```

### Running tests in parallel with pytest-xdist
```bash
# Run tests using all available CPU cores
pytest -n auto

# Run tests with a specific number of workers
pytest -n 4

# Run tests in parallel with specific markers
pytest -n auto -m integration

# Using the run_tests.sh script (automatically uses optimal number of processes)
./run_tests.sh

# Using the run_tests.sh script with specific options
./run_tests.sh -m integration
```

### Generate and view Allure reports
```bash
# Tests automatically generate Allure results
pytest

# Generate and open the report
allure serve reports/allure-results
```

## 📚 Documentation

- [Pytest-xdist Usage Guide](docs/pytest_xdist_usage.md): Quick reference for parallel test execution
- [Pytest-xdist Best Practices](docs/pytest_xdist_best_practices.md): Comprehensive guide to test isolation

## 📁 Project Structure

```
automation_framework/
├── config/                     # Configuration management
│   ├── __init__.py
│   └── config.py               # Central configuration class
├── data/                       # Test data files
├── pages/                      # Page Object Models for UI testing
│   ├── __init__.py
│   ├── base_page.py            # Base page class with common methods
│   └── main_page/              # Example page implementation
├── reports/                    # Test reports and artifacts
│   ├── allure-results/         # Allure report data
│   ├── allure-report/          # Generated Allure report
│   └── screenshots/            # Test failure screenshots
├── tests/                      # Test cases
│   ├── __init__.py
│   ├── conftest.py             # Test fixtures and configuration
│   ├── test_api_sample.py      # API test examples
│   ├── test_aws_sample.py      # AWS integration test examples
│   ├── test_db_sample.py       # Database test examples
│   └── test_sample.py          # General test examples
├── utils/                      # Helper utilities
│   ├── __init__.py
│   ├── api_helper.py           # API testing utilities
│   ├── aws_helper.py           # AWS service interactions
│   ├── db_helper.py            # Database interactions
│   └── playwright_wrapper.py   # UI automation utilities
├── .env.example                # Environment variable template
├── .gitignore                  # Git ignore file
├── pytest.ini                  # Pytest configuration
├── README.md                   # Project documentation
├── requirements.txt            # Python dependencies
├── run_tests.sh                # Test execution script
└── setup.py                    # Package setup script
```

## 🧩 Framework Components

### API Testing
The `APIHelper` and `APIAssert` classes provide utilities for API testing, including:
- Request management with logging and timeout handling
- Response validation and assertions
- Header and body content validation
- Performance monitoring

### Database Testing
Database helpers support both PostgreSQL and ClickHouse:
- Query execution with parameter binding
- Result validation
- Schema inspection
- Database assertions with `DBAssert`

### AWS Testing
AWS integration testing utilities include:
- Session and credential management
- S3 operations (list, create, delete buckets and objects)
- Support for other AWS services via the base `AWSHelper` class

### UI Testing
UI automation with Playwright:
- Page object model support
- Element interaction (click, fill, select)
- Navigation and waiting utilities
- Screenshot capture

## 🔧 Extending the Framework

### Adding New Page Objects
1. Create a new class extending `BasePage`
2. Implement page-specific locators and methods
3. Use the `PlaywrightWrapper` methods for interactions

### Creating New Test Types
1. Create a new helper class in the `utils` directory
2. Add appropriate fixtures in `conftest.py`
3. Create test cases using pytest and the new helper

## 🙏 Acknowledgements

- [Pytest](https://docs.pytest.org/)
- [Playwright](https://playwright.dev/)
- [Allure Framework](https://allurereport.org/)
- [Requests](https://requests.readthedocs.io/)

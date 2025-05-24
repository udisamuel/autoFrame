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
- **AI-Powered Testing**: Leverage artificial intelligence for test data generation, test case creation, and test result analysis
- **Jira Integration**: Automatically create Jira tickets for failed tests with screenshots and AI analysis
- **Comprehensive Helpers**:
  - API testing with request and response validation
  - Database interactions with PostgreSQL and ClickHouse
  - AWS service interactions with S3 and more
  - Web UI automation with Playwright
  - Performance timing utilities for measuring execution times

## 📋 Requirements

- Python 3.11+
- Dependencies as listed in `requirements.txt`
- OpenAI API key (for AI capabilities)

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
- AI configuration (OpenAI API key, feature toggles)
- Jira integration (base URL, credentials, project settings)
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

### Using AI capabilities
```bash
# Generate test data with AI
./ai_cli.py generate-data --type user --count 5 --output data/users.json

# Generate test cases with AI
./ai_cli.py generate-test --type api --endpoint /users --method GET

# Analyze test failures with AI
./ai_cli.py analyze-failure --test-name test_login --error "AssertionError"
```

## 📚 Documentation

- [Pytest-xdist Usage Guide](docs/pytest_xdist_usage.md): Quick reference for parallel test execution
- [Pytest-xdist Best Practices](docs/pytest_xdist_best_practices.md): Comprehensive guide to test isolation
- [AI Capabilities](docs/ai_capabilities.md): Detailed guide on using AI features for testing
- [Jira Integration](docs/jira_integration.md): Automatically create Jira tickets for failed tests

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
│   ├── test_sample.py          # General test examples
│   ├── test_api_with_ai.py     # AI-assisted API test examples
│   └── test_ui_with_ai.py      # AI-assisted UI test examples
├── utils/                      # Helper utilities
│   ├── __init__.py
│   ├── api_helper.py           # API testing utilities
│   ├── aws_helper.py           # AWS service interactions
│   ├── db_helper.py            # Database interactions
│   ├── playwright_wrapper.py   # UI automation utilities
│   ├── timer.py                # Performance timing utilities
│   ├── ai_data_generator.py    # AI test data generation
│   ├── ai_test_generator.py    # AI test case generation
│   └── ai_test_analyzer.py     # AI test result analysis
├── .env.example                # Environment variable template
├── .gitignore                  # Git ignore file
├── pytest.ini                  # Pytest configuration
├── README.md                   # Project documentation
├── requirements.txt            # Python dependencies
├── run_tests.sh                # Test execution script
└── setup.py                    # Package setup script
```

## 🧩 Framework Components

### AI Capabilities
The framework integrates AI-powered capabilities to enhance testing workflows:
- **Enhanced Test Data Generation**: Create realistic test data using AI with `AIDataGenerator`
- **AI-powered Test Case Generation**: Automatically generate test cases for API, UI, and database testing with `AITestGenerator`
- **Intelligent Test Result Analysis**: Analyze test failures to identify root causes and suggest fixes with `AITestAnalyzer`
- Access these capabilities via Python API or command-line interface (`ai_cli.py`)
- See the [AI Capabilities Documentation](docs/ai_capabilities.md) for detailed usage instructions

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

### Performance Timing
The `Timer` class provides a convenient way to measure and report execution times:
- Context manager for easy timing of code blocks
- Integration with Allure reporting
- Statistics collection for performance analysis
- Named timers for tracking multiple operations

#### Timer Examples

**Basic Usage:**
```python
from utils.timer import Timer

# Simple timing of a code block
with Timer("Database Query"):
    # Your code to be timed here
    results = db.execute_complex_query()

# The elapsed time will be logged and added to Allure report
```

**Statistics Collection:**
```python
from utils.timer import Timer
import time

# Time multiple operations and collect statistics
for i in range(10):
    with Timer("API Call", store_stats=True):
        # Simulate API call
        time.sleep(0.1)
        
# Get statistics for all timers
stats = Timer.get_stats()
print(f"API Call Statistics: {stats['API Call']}")

# Add statistics to Allure report
Timer.add_stats_to_allure()
```

**Nested Timers:**
```python
from utils.timer import Timer

# Measure overall test execution
with Timer("Total Test Time"):
    # Some setup code
    setup_data = prepare_test_data()
    
    # Measure specific operations within the test
    with Timer("API Request"):
        response = api.post("/endpoint", json_data=payload)
    
    with Timer("Database Verification"):
        db_result = db.verify_data_was_saved()
        
    # Additional steps...
```

**Custom Logging:**
```python
from utils.timer import Timer
import logging

# Create a custom logger
logger = logging.getLogger("performance_tests")
logger.setLevel(logging.DEBUG)

# Use the custom logger with the timer
with Timer("Performance Critical Operation", log_level=logging.DEBUG, logger=logger):
    # Critical operation to be timed with custom logging
    result = perform_critical_operation()
```

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
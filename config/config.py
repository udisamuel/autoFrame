import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the test framework."""
    
    # Browser configurations
    BROWSER = os.getenv('BROWSER', 'chromium')
    HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
    SLOW_MO = int(os.getenv('SLOW_MO', '0'))  # Slow down execution for debugging
    
    # Application configurations
    BASE_URL = os.getenv('BASE_URL', 'https://google.com')
    
    # Timeouts
    DEFAULT_TIMEOUT = int(os.getenv('DEFAULT_TIMEOUT', '30000'))  # milliseconds
    
    # Test data
    TEST_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    
    # Reporting
    SCREENSHOTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports', 'screenshots')
    REPORTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
    ALLURE_RESULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports', 'allure-results')
    
    # Database configurations
    # PostgreSQL
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
    
    # ClickHouse
    CLICKHOUSE_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
    CLICKHOUSE_PORT = int(os.getenv('CLICKHOUSE_PORT', '8123'))
    CLICKHOUSE_DB = os.getenv('CLICKHOUSE_DB', 'default')
    CLICKHOUSE_USER = os.getenv('CLICKHOUSE_USER', 'default')
    CLICKHOUSE_PASSWORD = os.getenv('CLICKHOUSE_PASSWORD', '')
    
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN', '')
    AWS_ENDPOINT_URL = os.getenv('AWS_ENDPOINT_URL', '')
    
    # Ensure directories exist
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist."""
        os.makedirs(cls.SCREENSHOTS_PATH, exist_ok=True)
        os.makedirs(cls.REPORTS_PATH, exist_ok=True)
        os.makedirs(cls.ALLURE_RESULTS_PATH, exist_ok=True)
        # Create test data directory if it doesn't exist
        os.makedirs(cls.TEST_DATA_PATH, exist_ok=True)
        
# Create directories at import time
Config.create_directories()

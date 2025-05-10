"""
Environment configurations for Locust performance tests.

This file contains configurations for different environments (development,
staging, production) and test scenarios. Import the appropriate configuration
in your Locust test file.

Usage example:
    from configs.environments import DEV_CONFIG
    
    class MyUser(HttpUser):
        host = DEV_CONFIG["BASE_URL"]
"""

# Development environment (local testing)
DEV_CONFIG = {
    # Base URLs
    "BASE_URL": "http://localhost:8000",
    "API_URL": "http://localhost:8000/api",
    
    # Test parameters
    "MAX_USERS": 50,
    "SPAWN_RATE": 5,  # users per second
    "RUN_TIME": "3m",  # 3 minutes
    
    # Thresholds for success/failure
    "RESPONSE_TIME_PERCENTILE_95": 500,  # ms
    "FAILURE_RATE_THRESHOLD": 5,  # percent
    
    # Test user credentials
    "TEST_USERS": [
        {"username": "testuser1", "password": "password1"},
        {"username": "testuser2", "password": "password2"},
        {"username": "testuser3", "password": "password3"},
    ],
    
    # Test data
    "PRODUCT_IDS": list(range(1001, 1050)),  # Test product IDs
    "SEARCH_TERMS": ["test", "product", "example"],
    
    # Report paths
    "HTML_REPORT_PATH": "../reports/dev_report.html",
    "CSV_REPORT_PATH": "../reports/dev_report"
}

# Staging environment
STAGING_CONFIG = {
    # Base URLs
    "BASE_URL": "https://staging.example.com",
    "API_URL": "https://api.staging.example.com",
    
    # Test parameters
    "MAX_USERS": 100,
    "SPAWN_RATE": 10,
    "RUN_TIME": "5m",
    
    # Thresholds
    "RESPONSE_TIME_PERCENTILE_95": 800,  # ms
    "FAILURE_RATE_THRESHOLD": 2,  # percent
    
    # Test user credentials
    "TEST_USERS": [
        {"username": "stg_user1", "password": "stg_password1"},
        {"username": "stg_user2", "password": "stg_password2"},
    ],
    
    # Test data
    "PRODUCT_IDS": list(range(2001, 2100)),
    "SEARCH_TERMS": ["staging", "test", "product", "example"],
    
    # Report paths
    "HTML_REPORT_PATH": "../reports/staging_report.html",
    "CSV_REPORT_PATH": "../reports/staging_report"
}

# Production environment (used for load testing against production-like environment)
PROD_CONFIG = {
    # Base URLs
    "BASE_URL": "https://example.com",
    "API_URL": "https://api.example.com",
    
    # Test parameters - more conservative for production
    "MAX_USERS": 500,
    "SPAWN_RATE": 20,
    "RUN_TIME": "10m",
    
    # Thresholds 
    "RESPONSE_TIME_PERCENTILE_95": 300,  # ms
    "FAILURE_RATE_THRESHOLD": 1,  # percent
    
    # Test user credentials - use dedicated test accounts in production
    "TEST_USERS": [
        {"username": "loadtest_user1", "password": "prod_password1"},
        {"username": "loadtest_user2", "password": "prod_password2"},
    ],
    
    # Test data - use real product IDs from production
    "PRODUCT_IDS": list(range(5001, 5100)),
    "SEARCH_TERMS": ["popular", "trending", "bestseller", "new"],
    
    # Report paths
    "HTML_REPORT_PATH": "../reports/prod_report.html",
    "CSV_REPORT_PATH": "../reports/prod_report"
}

# Test scenario configurations
SCENARIOS = {
    # Light load scenario
    "LIGHT_LOAD": {
        "USERS": 50,
        "SPAWN_RATE": 5,
        "RUN_TIME": "2m"
    },
    
    # Medium load scenario
    "MEDIUM_LOAD": {
        "USERS": 200,
        "SPAWN_RATE": 10,
        "RUN_TIME": "5m"
    },
    
    # Heavy load scenario
    "HEAVY_LOAD": {
        "USERS": 500,
        "SPAWN_RATE": 20,
        "RUN_TIME": "10m"
    },
    
    # Spike test scenario
    "SPIKE_TEST": {
        "USERS": 1000,
        "SPAWN_RATE": 100,  # Rapid user increase
        "RUN_TIME": "3m"
    },
    
    # Endurance test scenario
    "ENDURANCE_TEST": {
        "USERS": 200,
        "SPAWN_RATE": 5,
        "RUN_TIME": "60m"  # Long-running test
    }
}

# Function to get combined config for environment and scenario
def get_config(environment="DEV", scenario="MEDIUM_LOAD"):
    """
    Get a combined configuration for the specified environment and test scenario.
    
    Args:
        environment: One of "DEV", "STAGING", or "PROD"
        scenario: One of "LIGHT_LOAD", "MEDIUM_LOAD", "HEAVY_LOAD", "SPIKE_TEST", "ENDURANCE_TEST"
        
    Returns:
        A dictionary with combined configuration
    """
    # Select the base environment config
    if environment == "DEV":
        base_config = DEV_CONFIG.copy()
    elif environment == "STAGING":
        base_config = STAGING_CONFIG.copy()
    elif environment == "PROD":
        base_config = PROD_CONFIG.copy()
    else:
        raise ValueError(f"Unknown environment: {environment}")
    
    # Apply scenario settings
    if scenario in SCENARIOS:
        scenario_config = SCENARIOS[scenario]
        base_config["MAX_USERS"] = scenario_config["USERS"]
        base_config["SPAWN_RATE"] = scenario_config["SPAWN_RATE"]
        base_config["RUN_TIME"] = scenario_config["RUN_TIME"]
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
    
    return base_config

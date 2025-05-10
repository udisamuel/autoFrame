# Default configuration for Locust performance tests

# Base URL for tests
BASE_URL = "https://example.com"

# Test runtime settings
MAX_USERS = 100
SPAWN_RATE = 10  # users per second
RUN_TIME = "5m"  # 5 minutes

# Thresholds for test success/failure
RESPONSE_TIME_PERCENTILE_95 = 500  # ms
FAILURE_RATE_THRESHOLD = 1  # percent

# Paths for reports
HTML_REPORT_PATH = "../reports/report.html"
CSV_REPORT_PATH = "../reports/report_stats.csv"

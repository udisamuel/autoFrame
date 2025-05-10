# AI Capabilities for autoFrame

This README explains the AI capabilities that have been added to autoFrame testing framework.

## Overview

Three main AI capabilities have been integrated into the framework:

1. **Enhanced Test Data Generation** - Generate realistic test data using AI
2. **AI-powered Test Case Generation** - Automatically create test cases for API, UI, and DB testing
3. **Intelligent Test Result Analysis** - Analyze test failures to identify root causes and suggest fixes

## Important Note on Dependencies

The AI capabilities are designed to work with or without the OpenAI package:

- When OpenAI is available, the framework uses AI to provide enhanced capabilities
- When OpenAI is not available, the framework falls back to built-in methods for generating test data, test cases, and analysis
- This graceful degradation ensures the framework remains functional in all environments

## 1. Enhanced Test Data Generation

The `AIDataGenerator` class provides methods for generating realistic test data:

```python
from utils.ai_data_generator import AIDataGenerator

# Initialize the generator
generator = AIDataGenerator()

# Generate a user profile
user_data = generator.generate_user_profile(constraints={"country": "US", "age_min": 21})

# Generate API payloads
api_payload = generator.generate_api_payload(
    endpoint="/users", 
    method="POST",
    schema={"name": "string", "email": "string", "age": "integer"}
)

# Generate form data
form_data = generator.generate_form_data(
    form_name="registration",
    fields=["username", "email", "password", "address"]
)

# Generate a data set
data_set = generator.generate_test_data_set(
    data_type="products",
    count=5,
    constraints={"category": "electronics"}
)
```

## 2. AI-powered Test Case Generation

The `AITestGenerator` class helps create test cases for different testing types:

```python
from utils.ai_test_generator import AITestGenerator

# Initialize the generator
generator = AITestGenerator()

# Generate an API test
api_test_code = generator.generate_api_test(
    endpoint="/users",
    http_method="GET",
    description="Test retrieving a list of users"
)

# Generate a UI test
ui_test_code = generator.generate_ui_test(
    page_name="LoginPage",
    test_description="Verify user login with valid credentials",
    steps=["Navigate to login page", "Enter username", "Enter password", "Click login button", "Verify redirect to dashboard"]
)

# Generate a database test
db_test_code = generator.generate_db_test(
    db_type="postgres",
    query="SELECT * FROM users WHERE email LIKE '%@example.com'",
    test_description="Verify retrieval of users with example.com domain"
)

# Save the generated test to a file
file_path = generator.save_test_to_file(api_test_code, "test_get_users.py", "tests")
```

## 3. Intelligent Test Result Analysis

The `AITestAnalyzer` class helps analyze test failures and suggest improvements:

```python
from utils.ai_test_analyzer import AITestAnalyzer

# Initialize the analyzer
analyzer = AITestAnalyzer()

# Analyze a test failure
analysis = analyzer.analyze_test_failure(
    test_name="test_login_with_valid_credentials",
    error_message="AssertionError: Expected redirect to '/dashboard', got '/home'",
    test_code="def test_login_with_valid_credentials(): ...",
    screenshot_path="reports/screenshots/failure.png",
    response_data=None
)

# The analysis contains insights about the failure
print(f"Root cause: {analysis['root_cause']}")
print("Suggested fixes:")
for fix in analysis["suggested_fixes"]:
    print(f"- {fix}")

# Get suggestions for improving a test
improvements = analyzer.suggest_test_improvements(test_code)
```

## Using AI Capabilities in Your Tests

The AI capabilities are integrated with the existing pytest infrastructure through fixtures:

```python
import pytest
import allure
from utils.api_helper import APIHelper, APIAssert

@allure.feature("API Testing with AI")
@pytest.mark.api
def test_create_user_with_ai_data(api, ai_data_generator):
    """Test creating a user with AI-generated data."""
    
    # Skip test if AI data generator is not available
    if ai_data_generator is None:
        pytest.skip("AI data generation is not enabled")
    
    # Generate user data with constraints
    user_data = ai_data_generator.generate_user_profile({
        "country": "US",
        "age_min": 21,
        "age_max": 65
    })
    
    # Use the generated data in the test
    response = api.post("/users", json_data=user_data)
    
    # Regular assertions
    APIAssert.status_code(response, 201)
    APIAssert.json_has_key(response, "id")
```

## Command-line Interface

The framework includes a command-line interface for AI capabilities:

```bash
# Generate test data
./ai_cli.py generate-data --type user --count 5 --output data/users.json
./ai_cli.py generate-data --type api --endpoint /users --method POST

# Generate test cases
./ai_cli.py generate-test --type api --endpoint /users --method GET --description "Test retrieving users"
./ai_cli.py generate-test --type ui --page-name LoginPage --steps "Navigate to login,Enter credentials,Click login,Verify dashboard" --description "Test login"

# Analyze test files
./ai_cli.py analyze-test --file tests/test_login.py

# Analyze test failures
./ai_cli.py analyze-failure --test-name test_login --error "AssertionError: Expected True, got False" --test-file tests/test_login.py
```

## Configuration

AI capabilities are configured in your `.env` file:

```
# AI Configuration
OPENAI_API_KEY=your_api_key_here
AI_FEATURES_ENABLED=true
AI_DATA_GENERATION_ENABLED=true
AI_TEST_ANALYSIS_ENABLED=true
AI_TEST_GENERATION_ENABLED=true
```

## Requirements

The AI capabilities work with or without the following optional dependency:

- `openai>=0.27.0; python_version >= "3.8"`

If the OpenAI package is not available, the framework will use built-in fallback methods.

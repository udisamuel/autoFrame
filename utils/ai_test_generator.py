import openai
from typing import List, Dict, Any, Optional
import os
import re
import logging
from config.config import Config

logger = logging.getLogger(__name__)

class AITestGenerator:
    """Helper class for generating test cases using AI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with optional API key, otherwise use from config."""
        self.api_key = api_key or Config.OPENAI_API_KEY
        openai.api_key = self.api_key
    
    def generate_api_test(self, 
                         endpoint: str,
                         http_method: str,
                         description: str,
                         response_schema: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a pytest test case for an API endpoint.
        
        Args:
            endpoint: The API endpoint
            http_method: HTTP method (GET, POST, PUT, DELETE, etc.)
            description: Description of the test
            response_schema: Optional schema for the expected response
            
        Returns:
            String containing the generated test function code
        """
        schema_text = ""
        if response_schema:
            import json
            schema_text = "The response should conform to this schema: " + json.dumps(response_schema)
        
        prompt = f"""
        Create a pytest test function that tests a {http_method} request to the endpoint '{endpoint}'.
        Test description: {description}
        {schema_text}
        
        Use the APIHelper and APIAssert classes from the framework.
        Include appropriate assertions for status code, response body and response time.
        Use the pytest.mark.api decorator.
        Follow this format for the test function:
        
        ```python
        @allure.story("...")
        @allure.description("...")
        @pytest.mark.api
        def test_{http_method.lower()}_{endpoint.replace('/', '_').strip('_')}(api):
            # Setup
            ...
            
            # Execute
            ...
            
            # Assert
            ...
        ```
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a test automation expert that generates Python code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # Extract the Python code from the response
            content = response.choices[0].message.content
            code_match = re.search(r'```python\s*([\s\S]*?)\s*```', content)
            if code_match:
                code = code_match.group(1)
            else:
                code = content
                
            return code
        except Exception as e:
            logger.error(f"Error generating API test: {e}")
            # Return a simple template if the API call fails
            return f"""
@allure.story("API Testing")
@allure.description("{description}")
@pytest.mark.api
def test_{http_method.lower()}_{endpoint.replace('/', '_').strip('_')}(api):
    # This is a placeholder test generated when AI generation failed
    # TODO: Implement the actual test
    
    # Setup
    endpoint = "{endpoint}"
    
    # Execute
    response = api.{http_method.lower()}(endpoint)
    
    # Assert
    APIAssert.status_code(response, 200)  # Replace with expected status code
    APIAssert.response_time(response, 5.0)  # 5 seconds max
"""
    
    def generate_ui_test(self,
                         page_name: str,
                         test_description: str,
                         steps: List[str]) -> str:
        """
        Generate a pytest test case for UI automation.
        
        Args:
            page_name: Name of the page being tested
            test_description: Description of the test
            steps: List of test steps in plain language
            
        Returns:
            String containing the generated test function code
        """
        steps_text = "\n".join([f"- {step}" for step in steps])
        
        prompt = f"""
        Create a pytest test function that tests the UI functionality of the '{page_name}' page.
        Test description: {test_description}
        
        The test should implement these steps:
        {steps_text}
        
        Use the BasePage class and PlaywrightWrapper from the framework.
        Include appropriate assertions for each step.
        Use the pytest.mark.ui decorator.
        Follow this format for the test function:
        
        ```python
        @allure.story("...")
        @allure.description("...")
        @pytest.mark.ui
        def test_{page_name.lower()}_some_descriptive_name(_setup):
            # Setup
            page = _setup
            page_object = {page_name}Page(page)
            
            # Execute test steps with assertions
            ...
        ```
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a test automation expert that generates Python code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # Extract the Python code from the response
            content = response.choices[0].message.content
            code_match = re.search(r'```python\s*([\s\S]*?)\s*```', content)
            if code_match:
                code = code_match.group(1)
            else:
                code = content
                
            return code
        except Exception as e:
            logger.error(f"Error generating UI test: {e}")
            # Return a simple template if the API call fails
            
            # Generate a function name from the description
            desc_words = test_description.lower().split()
            func_name = "_".join(desc_words[:3]) if len(desc_words) > 2 else "_".join(desc_words)
            func_name = re.sub(r'[^a-z0-9_]', '', func_name)
            
            return f"""
@allure.story("UI Testing - {page_name}")
@allure.description("{test_description}")
@pytest.mark.ui
def test_{page_name.lower()}_{func_name}(_setup):
    # This is a placeholder test generated when AI generation failed
    # TODO: Implement the actual test
    
    # Setup
    page = _setup
    page_object = {page_name}Page(page)
    
    # Test steps
    # Implement the following steps:
    {steps_text}
"""
    
    def generate_db_test(self,
                        db_type: str,
                        query: str,
                        test_description: str) -> str:
        """
        Generate a pytest test case for database testing.
        
        Args:
            db_type: Type of database ("postgres", "clickhouse", etc.)
            query: The SQL query being tested
            test_description: Description of the test
            
        Returns:
            String containing the generated test function code
        """
        prompt = f"""
        Create a pytest test function that tests a database query on {db_type}.
        Test description: {test_description}
        Query: {query}
        
        Use the appropriate DB helper class from the framework.
        Include assertions for the query results.
        Use the pytest.mark.database decorator.
        Follow this format for the test function:
        
        ```python
        @allure.story("...")
        @allure.description("...")
        @pytest.mark.database
        def test_db_some_descriptive_name(db_connection):
            # Setup
            ...
            
            # Execute
            ...
            
            # Assert
            ...
        ```
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a test automation expert that generates Python code for database testing."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # Extract the Python code from the response
            content = response.choices[0].message.content
            code_match = re.search(r'```python\s*([\s\S]*?)\s*```', content)
            if code_match:
                code = code_match.group(1)
            else:
                code = content
                
            return code
        except Exception as e:
            logger.error(f"Error generating DB test: {e}")
            # Return a simple template if the API call fails
            return f"""
@allure.story("Database Testing - {db_type}")
@allure.description("{test_description}")
@pytest.mark.database
def test_db_{db_type.lower()}_query(db_connection):
    # This is a placeholder test generated when AI generation failed
    # TODO: Implement the actual test
    
    # Setup
    query = "{query}"
    
    # Execute
    result = db_connection.execute_query(query)
    
    # Assert
    assert result is not None, "Query should return a result"
"""
    
    def save_test_to_file(self, code: str, file_name: str, directory: str = "tests") -> str:
        """
        Save the generated test code to a file.
        
        Args:
            code: The generated test code
            file_name: Name of the file to save to
            directory: Directory to save the file in
            
        Returns:
            Path to the saved file
        """
        # Ensure the directory exists
        os.makedirs(directory, exist_ok=True)
        
        # Add imports if they're not already in the code
        imports = """
import pytest
import allure
from utils.api_helper import APIHelper, APIAssert
"""
        
        if "BasePage" in code and "import" not in code.split("\n")[0:5]:
            imports += "from pages.base_page import BasePage\n"
            
        # Only add imports if they're not already in the code
        if "import" not in code.split("\n")[0:5]:
            code = imports + code
        
        file_path = os.path.join(directory, file_name)
        with open(file_path, "w") as f:
            f.write(code)
            
        return file_path

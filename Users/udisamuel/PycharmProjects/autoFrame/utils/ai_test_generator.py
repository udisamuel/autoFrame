import logging
from typing import List, Dict, Any, Optional
import os
import re
from config.config import Config

logger = logging.getLogger(__name__)

# Check if OpenAI is available
OPENAI_AVAILABLE = False
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI package not found. AI test generation will use templates.")

class AITestGenerator:
    """Helper class for generating test cases using AI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with optional API key, otherwise use from config."""
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.openai_available = OPENAI_AVAILABLE
        
        if self.openai_available:
            try:
                openai.api_key = self.api_key
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.openai_available = False
    
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
        if self.openai_available and self.api_key:
            try:
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
                # Fall through to the fallback method
        
        # Fallback to template
        return self._generate_api_test_template(endpoint, http_method, description, response_schema)
    
    def _generate_api_test_template(self, endpoint: str, http_method: str, description: str, 
                                  response_schema: Optional[Dict[str, Any]] = None) -> str:
        """Generate an API test from template when AI is not available."""
        # Create a function name from the endpoint
        endpoint_name = endpoint.replace('/', '_').strip('_')
        if not endpoint_name:
            endpoint_name = "root"
        
        # Determine expected status code based on HTTP method
        if http_method.upper() == "GET":
            expected_status = 200
        elif http_method.upper() == "POST":
            expected_status = 201
        elif http_method.upper() in ["PUT", "PATCH"]:
            expected_status = 200
        elif http_method.upper() == "DELETE":
            expected_status = 204
        else:
            expected_status = 200
        
        # Generate test code
        code = f"""
import pytest
import allure
from utils.api_helper import APIHelper, APIAssert

@allure.story("API Testing")
@allure.description("{description}")
@pytest.mark.api
def test_{http_method.lower()}_{endpoint_name}(api):
    # Setup
    endpoint = "{endpoint}"
    
    # Execute
    response = api.{http_method.lower()}(endpoint)
    
    # Assert
    APIAssert.status_code(response, {expected_status})
    APIAssert.json_body(response)  # Validate response is valid JSON
    APIAssert.response_time(response, 5.0)  # 5 seconds max
"""
        
        # Add schema validation if provided
        if response_schema:
            code += """
    # Validate response schema
    expected_structure = {
"""
            for key, value in response_schema.items():
                if isinstance(value, str):
                    type_str = value.lower()
                    if type_str == "string":
                        code += f"        '{key}': str,\n"
                    elif type_str in ["number", "integer", "int"]:
                        code += f"        '{key}': int,\n"
                    elif type_str in ["float", "double"]:
                        code += f"        '{key}': float,\n"
                    elif type_str in ["boolean", "bool"]:
                        code += f"        '{key}': bool,\n"
                    else:
                        code += f"        '{key}': None,  # Check existence only\n"
                else:
                    code += f"        '{key}': None,  # Check existence only\n"
                    
            code += """    }
    APIAssert.json_has_structure(response, expected_structure)
"""
        
        return code
    
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
        if self.openai_available and self.api_key:
            try:
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
                # Fall through to the fallback method
        
        # Fallback to template
        return self._generate_ui_test_template(page_name, test_description, steps)
    
    def _generate_ui_test_template(self, page_name: str, test_description: str, steps: List[str]) -> str:
        """Generate a UI test from template when AI is not available."""
        # Create a function name from the description
        import re
        func_name = re.sub(r'[^a-zA-Z0-9_]', ' ', test_description.lower())
        func_name = '_'.join(func_name.split()[:3])  # Take first 3 words
        if not func_name:
            func_name = "test_function"
        
        # Generate test code
        code = f"""
import pytest
import allure
from pages.base_page import BasePage

class {page_name}Page(BasePage):
    # TODO: Add page-specific locators and methods
    pass

@allure.story("UI Testing")
@allure.description("{test_description}")
@pytest.mark.ui
def test_{page_name.lower()}_{func_name}(_setup):
    # Setup
    page = _setup
    page_object = {page_name}Page(page)
    
"""
        
        # Add steps
        for i, step in enumerate(steps):
            step_clean = step.strip()
            if "navigate" in step_clean.lower():
                code += f"    # Step {i+1}: {step_clean}\n"
                code += f"    page_object.navigate_to('/')\n\n"
            elif any(action in step_clean.lower() for action in ["click", "press", "select", "choose"]):
                code += f"    # Step {i+1}: {step_clean}\n"
                code += f"    page_object.click('#selector')  # TODO: Update selector\n\n"
            elif any(action in step_clean.lower() for action in ["type", "enter", "fill", "input"]):
                code += f"    # Step {i+1}: {step_clean}\n"
                code += f"    page_object.fill('#input_selector', 'test value')  # TODO: Update selector and value\n\n"
            elif any(action in step_clean.lower() for action in ["verify", "assert", "check", "validate"]):
                code += f"    # Step {i+1}: {step_clean}\n"
                code += f"    assert page_object.is_element_visible('#result_selector'), 'Element should be visible'  # TODO: Update selector\n\n"
            elif any(action in step_clean.lower() for action in ["wait", "pause"]):
                code += f"    # Step {i+1}: {step_clean}\n"
                code += f"    page_object.wait_for_selector('#element_selector')  # TODO: Update selector\n\n"
            else:
                code += f"    # Step {i+1}: {step_clean}\n"
                code += f"    # TODO: Implement this step\n\n"
        
        # Add screenshot
        code += f"    # Take a screenshot at the end of the test\n"
        code += f"    page_object.take_screenshot('{page_name.lower()}_{func_name}')\n"
        
        return code
    
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
        if self.openai_available and self.api_key:
            try:
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
                # Fall through to the fallback method
        
        # Fallback to template
        return self._generate_db_test_template(db_type, query, test_description)
    
    def _generate_db_test_template(self, db_type: str, query: str, test_description: str) -> str:
        """Generate a DB test from template when AI is not available."""
        # Determine the DB fixture name based on type
        if db_type.lower() == "postgres":
            fixture_name = "postgres_connection"
        elif db_type.lower() == "clickhouse":
            fixture_name = "clickhouse_connection"
        else:
            fixture_name = "db_connection"
        
        # Generate a name from the query
        query_type = "select" if query.strip().lower().startswith("select") else "query"
        
        # Generate test code
        code = f"""
import pytest
import allure
from utils.db_helper import DBAssert

@allure.story("Database Testing")
@allure.description("{test_description}")
@pytest.mark.database
def test_db_{db_type.lower()}_{query_type}({fixture_name}):
    # Setup
    query = \"\"\"{query}\"\"\"
    
    # Execute
    result = {fixture_name}.execute_query(query)
    
    # Assert
    assert result is not None, "Query should return a result"
    
    # Log the result for debugging
    allure.attach(
        str(result),
        name="Query Result",
        attachment_type=allure.attachment_type.TEXT
    )
    
    # TODO: Add more specific assertions based on expected results
    # Examples:
    # assert len(result) > 0, "Query should return at least one row"
    # assert "column_name" in result[0], "Result should contain the expected column"
    # assert result[0]["column_name"] == expected_value, "Column value should match expected value"
"""
        
        return code
    
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

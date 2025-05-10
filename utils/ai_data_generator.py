import openai
from typing import Dict, Any, List, Optional
from config.config import Config
import json
import re
import logging

logger = logging.getLogger(__name__)

class AIDataGenerator:
    """Helper class for generating realistic test data using AI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with optional API key, otherwise use from config."""
        self.api_key = api_key or Config.OPENAI_API_KEY
        openai.api_key = self.api_key
    
    def generate_user_profile(self, constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a realistic user profile with optional constraints.
        
        Args:
            constraints: Optional dictionary of constraints (e.g., {"country": "US", "age_min": 21})
            
        Returns:
            Dictionary with user profile data
        """
        constraints_text = ""
        if constraints:
            constraints_text = "with these constraints: " + ", ".join([f"{k}: {v}" for k, v in constraints.items()])
        
        prompt = f"Generate a JSON object for a user profile {constraints_text}. Include name, email, age, address, and phone number fields."
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a test data generator that outputs only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            # Extract and parse the JSON response
            content = response.choices[0].message.content
            # Extract the JSON part from the response if needed
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content
                
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                # Fallback to a default profile if parsing fails
                return {
                    "name": "Test User",
                    "email": "test@example.com",
                    "age": 30,
                    "address": "123 Test St",
                    "phone": "555-123-4567"
                }
        except Exception as e:
            logger.error(f"Error generating user profile: {e}")
            return {
                "name": "Test User",
                "email": "test@example.com",
                "age": 30,
                "address": "123 Test St",
                "phone": "555-123-4567"
            }
    
    def generate_api_payload(self, endpoint: str, method: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate an API payload based on endpoint, method, and optional schema.
        
        Args:
            endpoint: The API endpoint
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            schema: Optional schema definition for the payload
            
        Returns:
            Dictionary with API payload data
        """
        schema_text = ""
        if schema:
            schema_text = "following this schema: " + json.dumps(schema)
        
        prompt = f"Generate a valid JSON payload for a {method} request to {endpoint} endpoint {schema_text}."
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a test data generator that outputs only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            # Extract and parse the JSON response
            content = response.choices[0].message.content
            # Extract the JSON part from the response
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content
                
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                # Fallback to empty object if parsing fails
                return {}
        except Exception as e:
            logger.error(f"Error generating API payload: {e}")
            return {}
    
    def generate_test_data_set(self, data_type: str, count: int = 5, constraints: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Generate a set of test data items.
        
        Args:
            data_type: Type of data to generate (e.g., "user", "product", "address")
            count: Number of items to generate
            constraints: Optional constraints to apply
            
        Returns:
            List of generated data items
        """
        constraints_text = ""
        if constraints:
            constraints_text = "with these constraints: " + ", ".join([f"{k}: {v}" for k, v in constraints.items()])
        
        prompt = f"Generate a JSON array containing {count} {data_type} objects {constraints_text}. Each object should have appropriate fields for a {data_type}."
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a test data generator that outputs only valid JSON arrays."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            # Extract and parse the JSON response
            content = response.choices[0].message.content
            # Extract the JSON part from the response
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content
                
            try:
                result = json.loads(json_str)
                if isinstance(result, list):
                    return result
                elif isinstance(result, dict):
                    return [result]  # Convert single object to list
                else:
                    logger.error(f"Unexpected response format: {type(result)}")
                    return []
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return []
        except Exception as e:
            logger.error(f"Error generating test data set: {e}")
            return []
    
    def generate_form_data(self, form_name: str, fields: List[str]) -> Dict[str, Any]:
        """
        Generate form data based on form name and field list.
        
        Args:
            form_name: Name of the form (e.g., "registration", "payment")
            fields: List of field names
            
        Returns:
            Dictionary with form field values
        """
        fields_text = ", ".join(fields)
        
        prompt = f"Generate valid form data for a {form_name} form with these fields: {fields_text}. Return as JSON with the field names as keys."
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a test data generator that outputs only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            # Extract and parse the JSON response
            content = response.choices[0].message.content
            # Extract the JSON part from the response
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content
                
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                # Fallback to empty object with field placeholders
                return {field: f"test_{field}" for field in fields}
        except Exception as e:
            logger.error(f"Error generating form data: {e}")
            return {field: f"test_{field}" for field in fields}

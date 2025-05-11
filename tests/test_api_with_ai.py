import pytest
import allure
from utils.api_helper import APIHelper, APIAssert

@allure.feature("API Testing with AI")
@pytest.mark.api
class TestAPIWithAI:
    """
    Sample API test class demonstrating AI integration with the API helper.
    """
    
    @pytest.fixture
    def api(self):
        """
        Fixture to provide an instance of the API helper.
        """
        # Initialize API helper with a sample API base URL
        return APIHelper("https://jsonplaceholder.typicode.com")
    
    @allure.story("AI-Generated API Payload")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test creating a post with AI-generated data")
    def test_create_post_with_ai_data(self, api, ai_data_generator):
        """Test creating a post with AI-generated data."""
        
        # Skip test if AI data generator is not available
        if ai_data_generator is None:
            pytest.skip("AI data generation is not enabled")
        
        try:
            # Generate a post payload using the AI
            payload = ai_data_generator.generate_api_payload(
                endpoint="/posts", 
                method="POST",
                schema={
                    "title": "string",
                    "body": "string",
                    "userId": "integer"
                }
            )
            
            # Log the generated payload for debugging
            allure.attach(
                str(payload),
                name="AI-Generated Payload",
                attachment_type=allure.attachment_type.TEXT
            )
            
            # If payload is empty, log the error and provide a default payload
            if not payload:
                error_msg = "AI generated an empty payload. Using default payload instead."
                allure.attach(
                    error_msg,
                    name="AI Generation Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                print(error_msg)
                
                # Use a default payload instead
                payload = {
                    "title": "Default Title",
                    "body": "This is a default body text created when AI generation failed",
                    "userId": 1
                }
            
            # Ensure required fields are present
            assert "title" in payload, "Generated payload should contain a title"
            assert "body" in payload, "Generated payload should contain a body"
            assert "userId" in payload, "Generated payload should contain a userId"
            
            # Ensure userId is an integer (AI might generate it as a string)
            if isinstance(payload["userId"], str) and payload["userId"].isdigit():
                payload["userId"] = int(payload["userId"])
            
            # Send a POST request with the AI-generated payload
            response = api.post("/posts", json_data=payload)
            
            # Assert the response status code is 201 (Created)
            APIAssert.status_code(response, 201)
            
            # Assert the response has a valid JSON body
            json_data = APIAssert.json_body(response)
            
            # Assert specific values in the response match our payload
            APIAssert.json_key_equals(response, "title", payload["title"])
            APIAssert.json_key_equals(response, "body", payload["body"])
            APIAssert.json_key_equals(response, "userId", payload["userId"])
            
            # Assert an ID was assigned
            APIAssert.json_has_key(response, "id")
            
        except Exception as e:
            error_msg = f"Error in AI-generated API test: {str(e)}"
            allure.attach(
                error_msg,
                name="Test Error",
                attachment_type=allure.attachment_type.TEXT
            )
            print(error_msg)
            raise
    
    @allure.story("User Profile Data")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test retrieving user data with AI-generated constraints")
    def test_get_user_with_ai_constraints(self, api, ai_data_generator):
        """Test retrieving a user with AI-generated profile for validation."""
        
        # Skip test if AI data generator is not available
        if ai_data_generator is None:
            pytest.skip("AI data generation is not enabled")
        
        try:
            # First, get a random user from the API
            user_id = 1  # We'll use a known user ID for simplicity
            response = api.get(f"/users/{user_id}")
            
            # Assert the response status code is 200 (OK)
            APIAssert.status_code(response, 200)
            
            # Get the actual user data
            actual_user = APIAssert.json_body(response)
            
            # Generate an "expected" user profile with AI
            # Note: This is just to demonstrate using AI for test data generation
            # In a real scenario, you might use this to generate expected results
            expected_user = ai_data_generator.generate_user_profile({
                "id": user_id,
                "name_pattern": actual_user["name"][:5] + "*"  # Use part of the actual name as a pattern
            })
            
            # If expected_user is empty, log the error and provide a default profile
            if not expected_user:
                error_msg = "AI generated an empty user profile. Using default profile instead."
                allure.attach(
                    error_msg,
                    name="AI Generation Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                print(error_msg)
                
                # Use a default profile instead
                expected_user = {
                    "name": "Default User",
                    "email": "default@example.com",
                    "id": user_id
                }
            
            # Log both for comparison
            allure.attach(
                f"Actual User:\n{actual_user}\n\nAI-Generated Expected User:\n{expected_user}",
                name="User Comparison",
                attachment_type=allure.attachment_type.TEXT
            )
            
            # Here we're just demonstrating the concept - in a real test,
            # you might use the AI-generated data for more specific validations
            assert "name" in actual_user, "User should have a name"
            assert "email" in actual_user, "User should have an email"
            
        except Exception as e:
            error_msg = f"Error in AI-generated user test: {str(e)}"
            allure.attach(
                error_msg,
                name="Test Error",
                attachment_type=allure.attachment_type.TEXT
            )
            print(error_msg)
            raise

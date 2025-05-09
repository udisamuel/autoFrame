import pytest
import allure
from utils.api_helper import APIHelper, APIAssert

@allure.feature("API Testing")
@pytest.mark.api
class TestAPISample:
    """
    Sample API test class to demonstrate the usage of the API helper.
    """
    
    @pytest.fixture
    def api(self):
        """
        Fixture to provide an instance of the API helper.
        """
        # Initialize API helper with a sample API base URL
        return APIHelper("https://jsonplaceholder.typicode.com")
    
    @allure.story("GET Request")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test a simple GET request to an API endpoint")
    def test_get_request(self, api):
        """Test a simple GET request to retrieve a post."""
        # Send a GET request to retrieve a post with ID 1
        response = api.get("/posts/1")
        
        # Assert the response status code is 200
        APIAssert.status_code(response, 200)
        
        # Assert the response has a valid JSON body
        json_data = APIAssert.json_body(response)
        
        # Assert the JSON response has the expected structure
        APIAssert.json_has_structure(response, {
            "userId": int,
            "id": int,
            "title": str,
            "body": str
        })
        
        # Assert specific values in the response
        APIAssert.json_key_equals(response, "id", 1)
        
        # Additional assertions
        assert json_data["userId"] > 0, "Expected userId to be a positive integer"
        assert len(json_data["title"]) > 0, "Expected title to be non-empty"
    
    @allure.story("POST Request")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test a POST request to create a new resource")
    def test_post_request(self, api):
        """Test a POST request to create a new post."""
        # Prepare the request payload
        payload = {
            "title": "Test Post",
            "body": "This is a test post created by the API helper.",
            "userId": 1
        }
        
        # Send a POST request to create a new post
        response = api.post("/posts", json_data=payload)
        
        # Assert the response status code is 201 (Created)
        APIAssert.status_code(response, 201)
        
        # Assert the response has a valid JSON body
        json_data = APIAssert.json_body(response)
        
        # Assert the JSON response has the expected structure
        APIAssert.json_has_structure(response, {
            "id": int,
            "title": str,
            "body": str,
            "userId": int
        })
        
        # Assert specific values in the response
        APIAssert.json_key_equals(response, "title", "Test Post")
        APIAssert.json_key_equals(response, "body", "This is a test post created by the API helper.")
        APIAssert.json_key_equals(response, "userId", 1)
    
    @allure.story("PUT Request")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test a PUT request to update a resource")
    def test_put_request(self, api):
        """Test a PUT request to update a post."""
        # Prepare the request payload
        payload = {
            "id": 1,
            "title": "Updated Test Post",
            "body": "This post has been updated using the API helper.",
            "userId": 1
        }
        
        # Send a PUT request to update the post with ID 1
        response = api.put("/posts/1", json_data=payload)
        
        # Assert the response status code is 200 (OK)
        APIAssert.status_code(response, 200)
        
        # Assert the response has a valid JSON body
        json_data = APIAssert.json_body(response)
        
        # Assert the JSON response has the expected structure
        APIAssert.json_has_structure(response, {
            "id": int,
            "title": str,
            "body": str,
            "userId": int
        })
        
        # Assert specific values in the response
        APIAssert.json_key_equals(response, "title", "Updated Test Post")
        APIAssert.json_key_equals(response, "body", "This post has been updated using the API helper.")
        
    @allure.story("DELETE Request")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test a DELETE request to remove a resource")
    def test_delete_request(self, api):
        """Test a DELETE request to delete a post."""
        # Send a DELETE request to delete the post with ID 1
        response = api.delete("/posts/1")
        
        # Assert the response status code is 200 (OK)
        APIAssert.status_code(response, 200)
        
        # For this particular API, the response body is typically empty or {}
        # You can still perform assertions on the response if needed
        
    @allure.story("Query Parameters")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test using query parameters in API requests")
    def test_query_parameters(self, api):
        """Test using query parameters to filter results."""
        # Define query parameters
        params = {
            "userId": 1,
            "_limit": 3
        }
        
        # Send a GET request with query parameters
        response = api.get("/posts", params=params)
        
        # Assert the response status code is 200
        APIAssert.status_code(response, 200)
        
        # Assert the response has a valid JSON body
        json_data = APIAssert.json_body(response)
        
        # Assert we got the correct number of results (3 in this case)
        assert len(json_data) == 3, f"Expected 3 results, got {len(json_data)}"
        
        # Assert all posts belong to userId 1
        for post in json_data:
            assert post["userId"] == 1, f"Expected userId to be 1, got {post['userId']}"
            
    @allure.story("Response Headers")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test response headers in API requests")
    def test_response_headers(self, api):
        """Test assertions on response headers."""
        # Send a GET request
        response = api.get("/posts/1")
        
        # Assert the response status code is 200
        APIAssert.status_code(response, 200)
        
        # Assert that specific headers exist
        APIAssert.header_exists(response, "Content-Type")
        
        # Assert the value of the Content-Type header
        APIAssert.header_contains(response, "Content-Type", "application/json")
        
        # Assert the response time is reasonable
        APIAssert.response_time(response, 5.0)  # 5 seconds max

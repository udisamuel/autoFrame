"""
API Performance Testing Example

This file demonstrates how to load test a REST API using Locust.
It focuses on API-specific scenarios, authentication, and data handling.
"""

import json
import random
import time
from locust import HttpUser, task, between, events, tag
import logging

logger = logging.getLogger(__name__)

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logger.info("API Performance test is starting")

class APIUser(HttpUser):
    """
    User class for testing REST API endpoints.
    This simulates a client application making API calls.
    """
    # Random wait time between 1 and 3 seconds
    wait_time = between(1, 3)
    
    # Change this to your API base URL
    host = "https://api.example.com"
    
    # API version
    api_version = "v1"
    
    # Authentication token (will be populated during login)
    token = None
    
    def get_api_url(self, endpoint):
        """Helper method to build API URLs with the correct version"""
        return f"/{self.api_version}/{endpoint}"
    
    def on_start(self):
        """Authenticate at the start of each simulated user session"""
        # API authentication example
        response = self.client.post(
            self.get_api_url("auth/login"),
            json={
                "username": "testuser",
                "password": "password123"
            },
            name="API-Auth-Login"
        )
        
        if response.status_code == 200:
            # Extract token from response
            result = response.json()
            self.token = result.get("access_token")
            
            # Set authorization header for future requests
            self.client.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            })
            logger.debug("User authenticated successfully")
        else:
            logger.error(f"Authentication failed: {response.text}")
    
    @task
    @tag('read')
    def get_user_profile(self):
        """Get user profile data"""
        self.client.get(
            self.get_api_url("users/me"),
            name="API-GetUserProfile"
        )
    
    @task(3)
    @tag('read')
    def get_items(self):
        """Get a list of items with pagination parameters"""
        # Example of query parameters for pagination and filtering
        params = {
            "page": random.randint(1, 10),
            "limit": 20,
            "sort": random.choice(["name", "date", "price"]),
            "order": random.choice(["asc", "desc"])
        }
        
        with self.client.get(
            self.get_api_url("items"),
            params=params,
            name="API-GetItems",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                # Validate response structure
                data = response.json()
                if "items" not in data or "total" not in data:
                    response.failure("Response missing expected fields")
                    return
                
                # Extract item ID for use in other requests
                if data["items"]:
                    item_id = data["items"][0]["id"]
                    # Store for other tasks
                    self.item_id = item_id
            else:
                response.failure(f"Failed to get items: {response.status_code}")
    
    @task
    @tag('read')
    def get_item_details(self):
        """Get detailed information about a specific item"""
        # Use a fixed ID if no item_id from previous calls
        item_id = getattr(self, "item_id", "12345")
        
        self.client.get(
            self.get_api_url(f"items/{item_id}"),
            name="API-GetItemDetails"
        )
    
    @task
    @tag('search')
    def search_items(self):
        """Search for items using various criteria"""
        # List of possible search terms
        search_terms = ["smartphone", "laptop", "headphones", "camera", "watch"]
        
        # Randomize search parameters
        params = {
            "q": random.choice(search_terms),
            "min_price": random.choice([None, 50, 100, 200]),
            "max_price": random.choice([None, 500, 1000, 2000]),
            "category": random.choice([None, "electronics", "clothing", "books"])
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        self.client.get(
            self.get_api_url("search"),
            params=params,
            name="API-SearchItems"
        )
    
    @task
    @tag('write')
    def create_item(self):
        """Create a new item (POST request with JSON data)"""
        # Generate random item data
        item_data = {
            "name": f"Test Item {random.randint(1000, 9999)}",
            "description": "This is a test item created during load testing",
            "price": round(random.uniform(10.0, 1000.0), 2),
            "category": random.choice(["electronics", "clothing", "books"]),
            "tags": random.sample(["new", "sale", "limited", "featured"], k=2)
        }
        
        with self.client.post(
            self.get_api_url("items"),
            json=item_data,
            name="API-CreateItem",
            catch_response=True
        ) as response:
            if response.status_code == 201:
                # Save the created item ID for potential updates/deletions
                data = response.json()
                if "id" in data:
                    self.created_item_id = data["id"]
            else:
                response.failure(f"Failed to create item: {response.status_code}")
    
    @task
    @tag('write')
    def update_item(self):
        """Update an existing item (PUT/PATCH request)"""
        # Use a previously created item if available, otherwise use a default ID
        item_id = getattr(self, "created_item_id", "12345")
        
        # Data to update
        update_data = {
            "price": round(random.uniform(10.0, 1000.0), 2),
            "description": f"Updated description {int(time.time())}"
        }
        
        # Using PATCH to update only specific fields
        self.client.patch(
            self.get_api_url(f"items/{item_id}"),
            json=update_data,
            name="API-UpdateItem"
        )
    
    @task
    @tag('write')
    def delete_item(self):
        """Delete an item (DELETE request)"""
        # Use a previously created item if available, otherwise use a default ID
        item_id = getattr(self, "created_item_id", "12345")
        
        self.client.delete(
            self.get_api_url(f"items/{item_id}"),
            name="API-DeleteItem"
        )
    
    @task
    @tag('batch')
    def batch_operation(self):
        """Perform a batch operation (processing multiple items at once)"""
        # Example of bulk update operation
        batch_data = {
            "action": "price_update",
            "items": [
                {"id": "1001", "price": 99.99},
                {"id": "1002", "price": 149.99},
                {"id": "1003", "price": 199.99}
            ]
        }
        
        self.client.post(
            self.get_api_url("batch"),
            json=batch_data,
            name="API-BatchOperation"
        )
    
    @task
    @tag('error_handling')
    def test_error_handling(self):
        """Test API error handling by sending invalid requests"""
        # Invalid ID to test 404 response
        self.client.get(
            self.get_api_url("items/invalid_id_123456789"),
            name="API-ErrorHandling-404"
        )
        
        # Invalid data to test validation (400 response)
        self.client.post(
            self.get_api_url("items"),
            json={"invalid_data": True},  # Missing required fields
            name="API-ErrorHandling-400"
        )

# To run only specific tags:
# locust -f api_test_example.py --tags read

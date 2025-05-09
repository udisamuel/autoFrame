import pytest
import allure
from utils.api_helper import APIHelper, APIAssert
from utils.db_helper import PostgreSQLHelper, DBAssert

@allure.feature("API and Database Integration")
@pytest.mark.integration
class TestAPIDBIntegration:
    """
    Example test class demonstrating how to use API and database helpers together.
    This simulates a scenario where we verify that API operations correctly update the database.
    """
    
    @pytest.fixture
    def api(self):
        """Fixture to provide an API helper instance."""
        return APIHelper("https://jsonplaceholder.typicode.com")
    
    @pytest.fixture
    def db(self):
        """Fixture to provide a database helper instance."""
        with PostgreSQLHelper(
            host="localhost",
            port=5432,
            database="testdb",
            user="postgres",
            password="postgres"
        ) as postgres:
            # Setup - create test tables and data
            postgres.execute_query("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL
            )
            """, fetch=False)
            
            # Seed with initial data
            postgres.execute_query("""
            INSERT INTO posts (id, user_id, title, body) VALUES
            (1, 1, 'Initial Post', 'This is the initial post content')
            ON CONFLICT (id) DO NOTHING
            """, fetch=False)
            
            yield postgres
            
            # Teardown - clean up test data
            postgres.execute_query("DROP TABLE posts", fetch=False)
    
    @allure.story("Create Post and Verify in Database")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test creating a post via API and verifying it in the database")
    def test_create_post_and_verify_in_db(self, api, db):
        """Test creating a post via API and then verifying it was saved in the database."""
        # 1. Create a new post via API
        payload = {
            "title": "Test Post via API",
            "body": "This post was created via the API and should be in the database",
            "userId": 1
        }
        
        response = api.post("/posts", json_data=payload)
        
        # 2. Assert API response
        APIAssert.status_code(response, 201)
        json_data = APIAssert.json_body(response)
        post_id = json_data['id']
        
        # 3. Simulate saving the post to our local database
        # In a real scenario, the API would save to the database automatically
        # Here we're simulating that by manually inserting the record
        db.execute_query("""
        INSERT INTO posts (id, user_id, title, body) VALUES (%s, %s, %s, %s)
        """, (post_id, payload['userId'], payload['title'], payload['body']), fetch=False)
        
        # 4. Query the database to verify the post was saved
        result = db.execute_query(
            "SELECT id, user_id, title, body FROM posts WHERE id = %s",
            (post_id,)
        )
        
        # 5. Assert database state
        DBAssert.row_count(result, 1)
        DBAssert.result_contains(result, (
            post_id,
            payload['userId'],
            payload['title'],
            payload['body']
        ))
    
    @allure.story("Update Post and Verify in Database")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test updating a post via API and verifying it in the database")
    def test_update_post_and_verify_in_db(self, api, db):
        """Test updating a post via API and then verifying the update in the database."""
        # 0. Verify the initial state in the database
        initial_result = db.execute_query("SELECT * FROM posts WHERE id = 1")
        DBAssert.row_count(initial_result, 1)
        
        # 1. Update the post via API
        updated_payload = {
            "id": 1,
            "title": "Updated Post Title",
            "body": "This post was updated via the API",
            "userId": 1
        }
        
        response = api.put("/posts/1", json_data=updated_payload)
        
        # 2. Assert API response
        APIAssert.status_code(response, 200)
        APIAssert.json_key_equals(response, "title", "Updated Post Title")
        
        # 3. Simulate updating the post in our local database
        # In a real scenario, the API would update the database automatically
        db.execute_query("""
        UPDATE posts SET title = %s, body = %s WHERE id = %s
        """, (updated_payload['title'], updated_payload['body'], 1), fetch=False)
        
        # 4. Query the database to verify the post was updated
        result = db.execute_query("SELECT title, body FROM posts WHERE id = 1")
        
        # 5. Assert database state
        DBAssert.row_count(result, 1)
        DBAssert.column_values_match(result, 0, ["Updated Post Title"])
        DBAssert.column_values_match(result, 1, ["This post was updated via the API"])
    
    @allure.story("Delete Post and Verify in Database")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test deleting a post via API and verifying it's removed from the database")
    def test_delete_post_and_verify_in_db(self, api, db):
        """Test deleting a post via API and then verifying it was removed from the database."""
        # 0. Verify the post exists in the database
        initial_result = db.execute_query("SELECT * FROM posts WHERE id = 1")
        DBAssert.row_count(initial_result, 1)
        
        # 1. Delete the post via API
        response = api.delete("/posts/1")
        
        # 2. Assert API response
        APIAssert.status_code(response, 200)
        
        # 3. Simulate deleting the post from our local database
        # In a real scenario, the API would delete from the database automatically
        db.execute_query("DELETE FROM posts WHERE id = 1", fetch=False)
        
        # 4. Query the database to verify the post was deleted
        result = db.execute_query("SELECT * FROM posts WHERE id = 1")
        
        # 5. Assert database state
        DBAssert.row_count(result, 0)

import pytest
import allure
import uuid
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
    def db(self, request):
        """Fixture to provide a database helper instance with a unique table for each test."""
        # Generate a unique table name for this test to avoid conflicts
        test_name = request.node.name
        # Create a unique suffix based on a uuid
        unique_suffix = str(uuid.uuid4()).replace('-', '')[:8]
        table_name = f"posts_test_{unique_suffix}"
        
        with PostgreSQLHelper(
            host="localhost",
            port=5432,
            database="testdb",
            user="postgres",
            password="postgres"
        ) as postgres:
            try:
                # Setup - create test table with a unique name
                postgres.execute_query(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL
                )
                """, fetch=False)
                
                # Seed with initial data
                postgres.execute_query(f"""
                INSERT INTO {table_name} (id, user_id, title, body) VALUES
                (1, 1, 'Initial Post', 'This is the initial post content')
                ON CONFLICT (id) DO NOTHING
                """, fetch=False)
                
                # Store the table name for use in tests and cleanup
                postgres.table_name = table_name
                
                yield postgres
                
            except Exception as e:
                allure.attach(
                    f"Error in database setup: {str(e)}",
                    name="Database Setup Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise
            finally:
                # Always attempt to clean up the table, even if an error occurred
                try:
                    postgres.execute_query(f"DROP TABLE IF EXISTS {table_name}", fetch=False)
                except Exception as e:
                    allure.attach(
                        f"Error dropping test table {table_name}: {str(e)}",
                        name="Database Cleanup Error",
                        attachment_type=allure.attachment_type.TEXT
                    )
    
    @allure.story("Create Post and Verify in Database")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test creating a post via API and verifying it in the database")
    def test_create_post_and_verify_in_db(self, api, db):
        """Test creating a post via API and then verifying it was saved in the database."""
        # Get the table name from the db fixture
        table_name = db.table_name
        
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
        db.execute_query(f"""
        INSERT INTO {table_name} (id, user_id, title, body) VALUES (%s, %s, %s, %s)
        """, (post_id, payload['userId'], payload['title'], payload['body']), fetch=False)
        
        # 4. Query the database to verify the post was saved
        result = db.execute_query(
            f"SELECT id, user_id, title, body FROM {table_name} WHERE id = %s",
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
        # Get the table name from the db fixture
        table_name = db.table_name
        
        # 0. Verify the initial state in the database
        initial_result = db.execute_query(f"SELECT * FROM {table_name} WHERE id = 1")
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
        db.execute_query(f"""
        UPDATE {table_name} SET title = %s, body = %s WHERE id = %s
        """, (updated_payload['title'], updated_payload['body'], 1), fetch=False)
        
        # 4. Query the database to verify the post was updated
        result = db.execute_query(f"SELECT title, body FROM {table_name} WHERE id = 1")
        
        # 5. Assert database state
        DBAssert.row_count(result, 1)
        DBAssert.column_values_match(result, 0, ["Updated Post Title"])
        DBAssert.column_values_match(result, 1, ["This post was updated via the API"])
    
    @allure.story("Delete Post and Verify in Database")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test deleting a post via API and verifying it's removed from the database")
    def test_delete_post_and_verify_in_db(self, api, db):
        """Test deleting a post via API and then verifying it was removed from the database."""
        # Get the table name from the db fixture
        table_name = db.table_name
        
        # 0. Verify the post exists in the database
        initial_result = db.execute_query(f"SELECT * FROM {table_name} WHERE id = 1")
        DBAssert.row_count(initial_result, 1)
        
        # 1. Delete the post via API
        response = api.delete("/posts/1")
        
        # 2. Assert API response
        APIAssert.status_code(response, 200)
        
        # 3. Simulate deleting the post from our local database
        # In a real scenario, the API would delete from the database automatically
        db.execute_query(f"DELETE FROM {table_name} WHERE id = 1", fetch=False)
        
        # 4. Query the database to verify the post was deleted
        result = db.execute_query(f"SELECT * FROM {table_name} WHERE id = 1")
        
        # 5. Assert database state
        DBAssert.row_count(result, 0)

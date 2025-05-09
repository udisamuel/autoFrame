import pytest
import allure
from utils.db_helper import PostgreSQLHelper, ClickHouseHelper, DBAssert

@allure.feature("Database Testing")
@pytest.mark.db
class TestDBSample:
    """
    Sample database test class to demonstrate the usage of the database helpers.
    """
    
    @pytest.fixture
    def postgres(self):
        """
        Fixture to provide an instance of the PostgreSQL helper.
        """
        with PostgreSQLHelper(
            host="localhost",
            port=5432,
            database="testdb",
            user="postgres",
            password="postgres"
        ) as pg:
            yield pg
    
    @pytest.fixture
    def clickhouse(self):
        """
        Fixture to provide an instance of the ClickHouse helper.
        """
        with ClickHouseHelper(
            host="localhost",
            port=8123,
            database="default",
            user="default",
            password=""
        ) as ch:
            yield ch
    
    @allure.story("PostgreSQL Query")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test a simple PostgreSQL query")
    def test_postgres_query(self, postgres):
        """Test executing a simple query on PostgreSQL."""
        # Create a test table
        postgres.execute_query("""
        CREATE TABLE IF NOT EXISTS test_table (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """, fetch=False)
        
        # Insert test data
        postgres.execute_query("""
        INSERT INTO test_table (name, email) VALUES
        ('Alice', 'alice@example.com'),
        ('Bob', 'bob@example.com'),
        ('Charlie', 'charlie@example.com')
        ON CONFLICT (email) DO NOTHING
        """, fetch=False)
        
        # Query the data
        result = postgres.execute_query("SELECT id, name, email FROM test_table ORDER BY id")
        
        # Perform assertions
        DBAssert.row_count(result, 3)
        DBAssert.result_contains(result, (2, 'Bob', 'bob@example.com'))
        
        # Get the table schema
        schema = postgres.get_table_schema('test_table')
        
        # Assert schema contains expected columns
        DBAssert.contains_column(schema, 'id')
        DBAssert.contains_column(schema, 'name')
        DBAssert.contains_column(schema, 'email')
        
        # Assert column types
        DBAssert.column_is_of_type(schema, 'id', 'integer')
        DBAssert.column_is_of_type(schema, 'name', 'character varying')
        
        # Clean up
        postgres.execute_query("DROP TABLE test_table", fetch=False)
    
    @allure.story("PostgreSQL Parameterized Query")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test a parameterized query on PostgreSQL")
    def test_postgres_parameterized_query(self, postgres):
        """Test executing a parameterized query on PostgreSQL."""
        # Create a test table
        postgres.execute_query("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            age INTEGER
        )
        """, fetch=False)
        
        # Insert test data
        postgres.execute_query("""
        INSERT INTO users (username, age) VALUES
        ('user1', 25),
        ('user2', 30),
        ('user3', 35),
        ('user4', 40)
        """, fetch=False)
        
        # Execute a parameterized query
        min_age = 30
        result = postgres.execute_query(
            "SELECT username, age FROM users WHERE age >= %s ORDER BY age",
            (min_age,)
        )
        
        # Perform assertions
        DBAssert.row_count(result, 3)
        DBAssert.result_contains(result, ('user2', 30))
        DBAssert.result_contains(result, ('user3', 35))
        DBAssert.result_contains(result, ('user4', 40))
        
        # Assert all ages are >= min_age
        DBAssert.column_values_all_match_condition(
            result, 1, lambda age: age >= min_age, f"age >= {min_age}"
        )
        
        # Clean up
        postgres.execute_query("DROP TABLE users", fetch=False)

    @pytest.mark.skip(reason="Skipping ClickHouse query test")
    @allure.story("ClickHouse Query")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test a simple ClickHouse query")
    def test_clickhouse_query(self, clickhouse):
        """Test executing a simple query on ClickHouse."""
        # Create a test table
        clickhouse.execute_query("""
        CREATE TABLE IF NOT EXISTS test_events (
            event_date Date,
            event_type String,
            user_id UInt32,
            value Float64
        ) ENGINE = MergeTree()
        ORDER BY (event_date, event_type, user_id)
        """)
        
        # Insert test data
        clickhouse.execute_query("""
        INSERT INTO test_events VALUES
        ('2023-01-01', 'click', 1, 10.5),
        ('2023-01-01', 'view', 1, 0.0),
        ('2023-01-02', 'click', 2, 15.2),
        ('2023-01-02', 'purchase', 2, 100.0),
        ('2023-01-03', 'view', 3, 0.0)
        """)
        
        # Query the data
        result = clickhouse.execute_query("""
        SELECT event_type, count() as count, sum(value) as total_value
        FROM test_events
        GROUP BY event_type
        ORDER BY event_type
        """)
        
        # Perform assertions
        DBAssert.row_count(result, 3)
        
        # Clean up
        clickhouse.execute_query("DROP TABLE test_events")

    @pytest.mark.skip(reason="Skipping ClickHouse parameterized query test")
    @allure.story("ClickHouse Parameterized Query")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test a parameterized query on ClickHouse")
    def test_clickhouse_parameterized_query(self, clickhouse):
        """Test executing a parameterized query on ClickHouse."""
        # Create a test table
        clickhouse.execute_query("""
        CREATE TABLE IF NOT EXISTS user_metrics (
            date Date,
            user_id UInt32,
            page_views UInt32,
            clicks UInt32,
            duration_sec Float64
        ) ENGINE = MergeTree()
        ORDER BY (date, user_id)
        """)
        
        # Insert test data
        clickhouse.execute_query("""
        INSERT INTO user_metrics VALUES
        ('2023-01-01', 1, 10, 5, 120.5),
        ('2023-01-01', 2, 15, 7, 180.0),
        ('2023-01-02', 1, 8, 3, 90.2),
        ('2023-01-02', 3, 20, 10, 300.0),
        ('2023-01-03', 2, 12, 6, 150.0)
        """)
        
        # Execute a parameterized query
        min_clicks = 5
        query = "SELECT user_id, sum(clicks) as total_clicks FROM user_metrics WHERE clicks >= {clicks:UInt32} GROUP BY user_id ORDER BY user_id"
        result = clickhouse.execute_query(query, {"clicks": min_clicks})
        
        # Perform assertions
        DBAssert.row_count_greater_than(result, 0)
        
        # Clean up
        clickhouse.execute_query("DROP TABLE user_metrics")

import logging
import os
from typing import List, Dict, Any, Optional, Union, Tuple
import allure
from config.config import Config

logger = logging.getLogger(__name__)

class BaseDBHelper:
    """
    Base class for database helpers with common functionality.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize the database helper.
        
        Args:
            connection_string: The connection string for the database. If not provided,
                              it will be constructed from environment variables.
        """
        self.connection_string = connection_string
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """
        Connect to the database. This method should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def disconnect(self):
        """
        Disconnect from the database. This method should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def execute_query(self, query: str, params: Optional[Union[List, Dict, Tuple]] = None):
        """
        Execute a query on the database. This method should be overridden by subclasses.
        
        Args:
            query: The SQL query to execute
            params: The parameters for the query
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def _log_query(self, query: str, params: Optional[Union[List, Dict, Tuple]] = None):
        """
        Log a query for debugging purposes.
        
        Args:
            query: The SQL query
            params: The parameters for the query
        """
        with allure.step(f"Database Query"):
            # Sanitize the query to hide sensitive information
            sanitized_query = self._sanitize_query(query)
            
            logger.info(f"Executing query: {sanitized_query}")
            if params:
                logger.debug(f"Query parameters: {self._sanitize_params(params)}")
            
            allure.attach(
                f"Query: {sanitized_query}\n"
                f"Parameters: {self._sanitize_params(params) if params else 'None'}",
                name="Database Query",
                attachment_type=allure.attachment_type.TEXT
            )
    
    def _log_result(self, result):
        """
        Log the result of a query for debugging purposes.
        
        Args:
            result: The query result
        """
        with allure.step(f"Database Result"):
            # For large results, we might want to limit what we log
            result_to_log = self._format_result_for_logging(result)
            
            logger.debug(f"Query result: {result_to_log}")
            
            allure.attach(
                f"Result: {result_to_log}",
                name="Database Result",
                attachment_type=allure.attachment_type.TEXT
            )
    
    def _sanitize_query(self, query: str) -> str:
        """
        Sanitize a query to hide sensitive information.
        
        Args:
            query: The SQL query
            
        Returns:
            The sanitized query
        """
        # List of keywords that might indicate sensitive information
        sensitive_keywords = ['password', 'passwd', 'secret', 'token', 'apikey', 'api_key', 'auth']
        
        # Simple sanitization: check for sensitive keywords followed by some delimiter and a value
        sanitized = query
        for keyword in sensitive_keywords:
            # Match patterns like "password = 'xyz'" or "password='xyz'" or "password = xyz"
            patterns = [
                f"{keyword}\\s*=\\s*'[^']*'",  # password = 'xyz'
                f"{keyword}\\s*=\\s*\"[^\"]*\"",  # password = "xyz"
                f"{keyword}\\s*:\\s*'[^']*'",  # password: 'xyz'
                f"{keyword}\\s*:\\s*\"[^\"]*\"",  # password: "xyz"
                f"{keyword}\\s*=>\\s*'[^']*'",  # password => 'xyz'
                f"{keyword}\\s*=>\\s*\"[^\"]*\""  # password => "xyz"
            ]
            
            import re
            for pattern in patterns:
                sanitized = re.sub(pattern, f"{keyword} = '********'", sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def _sanitize_params(self, params: Union[List, Dict, Tuple]) -> Union[List, Dict, Tuple]:
        """
        Sanitize parameters to hide sensitive information.
        
        Args:
            params: The parameters for the query
            
        Returns:
            The sanitized parameters
        """
        # List of parameter names that might indicate sensitive information
        sensitive_params = ['password', 'passwd', 'secret', 'token', 'apikey', 'api_key', 'auth']
        
        if isinstance(params, dict):
            sanitized = params.copy()
            for key in sanitized:
                if any(sensitive in key.lower() for sensitive in sensitive_params):
                    sanitized[key] = '********'
            return sanitized
        
        # For lists and tuples, we can't easily identify which values are sensitive
        # So we'll return them as-is for now
        return params
    
    def _format_result_for_logging(self, result):
        """
        Format a query result for logging.
        
        Args:
            result: The query result
            
        Returns:
            The formatted result
        """
        # This is a simple implementation that can be overridden by subclasses
        # For large result sets, we might want to limit what we log
        
        if isinstance(result, (list, tuple)):
            if len(result) > 10:
                # If the result has more than 10 rows, only log the first 5 and last 5
                return (
                    f"[First 5 of {len(result)} rows]\n" +
                    "\n".join(str(row) for row in result[:5]) +
                    "\n...\n" +
                    f"[Last 5 of {len(result)} rows]\n" +
                    "\n".join(str(row) for row in result[-5:])
                )
            else:
                return "\n".join(str(row) for row in result)
        
        return str(result)
    
    def __enter__(self):
        """
        Enter context manager - connect to the database.
        """
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context manager - disconnect from the database.
        """
        self.disconnect()


class PostgreSQLHelper(BaseDBHelper):
    """
    Helper class for PostgreSQL database operations.
    """
    
    def __init__(self, connection_string: Optional[str] = None, 
                 host: Optional[str] = None, 
                 port: Optional[int] = None, 
                 database: Optional[str] = None,
                 user: Optional[str] = None, 
                 password: Optional[str] = None):
        """
        Initialize the PostgreSQL helper.
        
        Args:
            connection_string: The connection string for the database. If not provided,
                              it will be constructed from other parameters.
            host: The database host
            port: The database port
            database: The database name
            user: The database user
            password: The database password
        """
        super().__init__(connection_string)
        
        # If no connection string is provided, construct one from individual parameters
        if self.connection_string is None:
            self.host = host or os.getenv('POSTGRES_HOST', 'localhost')
            self.port = port or int(os.getenv('POSTGRES_PORT', '5432'))
            self.database = database or os.getenv('POSTGRES_DB', 'postgres')
            self.user = user or os.getenv('POSTGRES_USER', 'postgres')
            self.password = password or os.getenv('POSTGRES_PASSWORD', 'postgres')
            
            # We don't include the password in the constructed connection string for security
            # It will be passed separately
            self.connection_string = f"host={self.host} port={self.port} dbname={self.database} user={self.user}"
        else:
            # Parse connection string to extract components
            try:
                import re
                host_match = re.search(r'host=([^ ]+)', self.connection_string)
                port_match = re.search(r'port=([^ ]+)', self.connection_string)
                dbname_match = re.search(r'dbname=([^ ]+)', self.connection_string)
                user_match = re.search(r'user=([^ ]+)', self.connection_string)
                password_match = re.search(r'password=([^ ]+)', self.connection_string)
                
                self.host = host_match.group(1) if host_match else None
                self.port = int(port_match.group(1)) if port_match else None
                self.database = dbname_match.group(1) if dbname_match else None
                self.user = user_match.group(1) if user_match else None
                self.password = password_match.group(1) if password_match else None
                
                # Remove password from connection string for security
                if password_match:
                    self.connection_string = self.connection_string.replace(
                        f"password={self.password}", "password=********"
                    )
            except Exception as e:
                logger.warning(f"Failed to parse connection string: {str(e)}")
    
    def connect(self):
        """
        Connect to the PostgreSQL database.
        """
        try:
            import psycopg2
            logger.info(f"Connecting to PostgreSQL database: {self.host}:{self.port}/{self.database}")
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.database,
                user=self.user,
                password=self.password
            )
            self.cursor = self.connection.cursor()
            logger.info("Connected to PostgreSQL database successfully")
        except Exception as e:
            logger.exception(f"Failed to connect to PostgreSQL database: {str(e)}")
            allure.attach(
                f"Failed to connect to PostgreSQL database: {str(e)}",
                name="Database Connection Error",
                attachment_type=allure.attachment_type.TEXT
            )
            raise
    
    def disconnect(self):
        """
        Disconnect from the PostgreSQL database.
        """
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("Disconnected from PostgreSQL database")
        except Exception as e:
            logger.exception(f"Error disconnecting from PostgreSQL database: {str(e)}")
    
    def execute_query(self, query: str, params: Optional[Union[List, Dict, Tuple]] = None, 
                      fetch: bool = True) -> List[Tuple]:
        """
        Execute a query on the PostgreSQL database.
        
        Args:
            query: The SQL query to execute
            params: The parameters for the query
            fetch: Whether to fetch the results (True for SELECT, False for INSERT/UPDATE/DELETE)
            
        Returns:
            The query results as a list of tuples, or None for non-SELECT queries
        """
        if not self.connection or not self.cursor:
            self.connect()
        
        self._log_query(query, params)
        
        try:
            self.cursor.execute(query, params)
            
            if fetch:
                result = self.cursor.fetchall()
                self._log_result(result)
                return result
            else:
                # For non-SELECT queries (INSERT, UPDATE, DELETE), commit the changes
                self.connection.commit()
                rowcount = self.cursor.rowcount
                self._log_result(f"Affected rows: {rowcount}")
                return rowcount
                
        except Exception as e:
            logger.exception(f"Error executing query: {str(e)}")
            allure.attach(
                f"Query error: {str(e)}",
                name="Database Query Error",
                attachment_type=allure.attachment_type.TEXT
            )
            # Rollback in case of error
            if self.connection:
                self.connection.rollback()
            raise
    
    def execute_file(self, file_path: str, params: Optional[Dict[str, Any]] = None) -> None:
        """
        Execute a SQL file on the database.
        
        Args:
            file_path: The path to the SQL file
            params: Optional parameters to substitute in the SQL file
        """
        try:
            with open(file_path, 'r') as file:
                sql = file.read()
            
            # Simple parameter substitution
            if params:
                for key, value in params.items():
                    sql = sql.replace(f":{key}", f"'{value}'")
            
            # Split the SQL by semicolons to execute multiple statements
            statements = sql.split(';')
            
            for statement in statements:
                statement = statement.strip()
                if statement:  # Skip empty statements
                    self.execute_query(statement, fetch=False)
                    
            logger.info(f"Executed SQL file: {file_path}")
            
        except Exception as e:
            logger.exception(f"Error executing SQL file {file_path}: {str(e)}")
            raise
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get the schema of a table.
        
        Args:
            table_name: The name of the table
            
        Returns:
            A list of dictionaries with column information
        """
        query = """
        SELECT column_name, data_type, character_maximum_length, 
               column_default, is_nullable
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position;
        """
        
        result = self.execute_query(query, (table_name,))
        
        # Convert result to a list of dictionaries
        columns = []
        for row in result:
            columns.append({
                'name': row[0],
                'data_type': row[1],
                'max_length': row[2],
                'default': row[3],
                'nullable': row[4] == 'YES'
            })
        
        return columns


class ClickHouseHelper(BaseDBHelper):
    """
    Helper class for ClickHouse database operations.
    """
    
    def __init__(self, connection_string: Optional[str] = None, 
                 host: Optional[str] = None, 
                 port: Optional[int] = None, 
                 database: Optional[str] = None,
                 user: Optional[str] = None, 
                 password: Optional[str] = None,
                 settings: Optional[Dict[str, Any]] = None):
        """
        Initialize the ClickHouse helper.
        
        Args:
            connection_string: The connection string for the database. If not provided,
                              it will be constructed from other parameters.
            host: The database host
            port: The database port
            database: The database name
            user: The database user
            password: The database password
            settings: Additional ClickHouse client settings
        """
        super().__init__(connection_string)
        
        # If no connection string is provided, use individual parameters
        if self.connection_string is None:
            self.host = host or os.getenv('CLICKHOUSE_HOST', 'localhost')
            self.port = port or int(os.getenv('CLICKHOUSE_PORT', '8123'))
            self.database = database or os.getenv('CLICKHOUSE_DB', 'default')
            self.user = user or os.getenv('CLICKHOUSE_USER', 'default')
            self.password = password or os.getenv('CLICKHOUSE_PASSWORD', '')
            self.settings = settings or {}
        else:
            # Parse connection string to extract components
            try:
                import urllib.parse
                parsed = urllib.parse.urlparse(self.connection_string)
                
                self.host = parsed.hostname or 'localhost'
                self.port = parsed.port or 8123
                self.user = parsed.username or 'default'
                self.password = parsed.password or ''
                
                # Extract database from path
                if parsed.path and parsed.path != '/':
                    self.database = parsed.path.strip('/')
                else:
                    self.database = 'default'
                
                # Extract settings from query params
                self.settings = {}
                if parsed.query:
                    query_params = urllib.parse.parse_qs(parsed.query)
                    for key, value in query_params.items():
                        self.settings[key] = value[0] if len(value) == 1 else value
                
            except Exception as e:
                logger.warning(f"Failed to parse connection string: {str(e)}")
    
    def connect(self):
        """
        Connect to the ClickHouse database.
        """
        try:
            from clickhouse_driver import Client
            
            logger.info(f"Connecting to ClickHouse database: {self.host}:{self.port}/{self.database}")
            self.connection = Client(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                settings=self.settings
            )
            logger.info("Connected to ClickHouse database successfully")
        except Exception as e:
            logger.exception(f"Failed to connect to ClickHouse database: {str(e)}")
            allure.attach(
                f"Failed to connect to ClickHouse database: {str(e)}",
                name="Database Connection Error",
                attachment_type=allure.attachment_type.TEXT
            )
            raise
    
    def disconnect(self):
        """
        Disconnect from the ClickHouse database.
        """
        # ClickHouse driver doesn't require explicit disconnect
        self.connection = None
        logger.info("Disconnected from ClickHouse database")
    
    def execute_query(self, query: str, params: Optional[Union[List, Dict, Tuple]] = None, 
                      settings: Optional[Dict[str, Any]] = None) -> List[Tuple]:
        """
        Execute a query on the ClickHouse database.
        
        Args:
            query: The SQL query to execute
            params: The parameters for the query
            settings: Additional settings for this query
            
        Returns:
            The query results
        """
        if not self.connection:
            self.connect()
        
        self._log_query(query, params)
        
        try:
            # For ClickHouse, we always fetch results
            result = self.connection.execute(query, params or {}, with_column_types=True, settings=settings)
            
            # The result is a tuple of (data, column_types)
            data, column_types = result
            
            self._log_result(data)
            
            # Return just the data for consistency with PostgreSQLHelper
            return data
                
        except Exception as e:
            logger.exception(f"Error executing query: {str(e)}")
            allure.attach(
                f"Query error: {str(e)}",
                name="Database Query Error",
                attachment_type=allure.attachment_type.TEXT
            )
            raise
    
    def execute_file(self, file_path: str, params: Optional[Dict[str, Any]] = None,
                    settings: Optional[Dict[str, Any]] = None) -> None:
        """
        Execute a SQL file on the database.
        
        Args:
            file_path: The path to the SQL file
            params: Optional parameters to substitute in the SQL file
            settings: Additional settings for this query
        """
        try:
            with open(file_path, 'r') as file:
                sql = file.read()
            
            # Simple parameter substitution
            if params:
                for key, value in params.items():
                    placeholder = f":{key}"
                    if isinstance(value, str):
                        value = f"'{value}'"
                    else:
                        value = str(value)
                    sql = sql.replace(placeholder, value)
            
            # Split the SQL by semicolons to execute multiple statements
            statements = sql.split(';')
            
            for statement in statements:
                statement = statement.strip()
                if statement:  # Skip empty statements
                    self.execute_query(statement, settings=settings)
                    
            logger.info(f"Executed SQL file: {file_path}")
            
        except Exception as e:
            logger.exception(f"Error executing SQL file {file_path}: {str(e)}")
            raise
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get the schema of a table.
        
        Args:
            table_name: The name of the table
            
        Returns:
            A list of dictionaries with column information
        """
        query = f"""
        DESCRIBE TABLE {table_name}
        """
        
        result = self.execute_query(query)
        
        # Convert result to a list of dictionaries
        columns = []
        for row in result:
            columns.append({
                'name': row[0],
                'data_type': row[1],
                'default_type': row[2],
                'default_expression': row[3],
                'comment': row[4],
                'codec_expression': row[5],
                'ttl_expression': row[6]
            })
        
        return columns


class DBAssert:
    """
    Helper class for database assertions.
    """
    
    @staticmethod
    def row_count(result: List[Tuple], expected_count: int) -> None:
        """
        Assert the number of rows in the result.
        
        Args:
            result: The query result
            expected_count: The expected number of rows
        """
        with allure.step(f"Assert row count is {expected_count}"):
            actual_count = len(result)
            assert actual_count == expected_count, f"Expected {expected_count} rows, got {actual_count}"
    
    @staticmethod
    def row_count_greater_than(result: List[Tuple], min_count: int) -> None:
        """
        Assert the number of rows in the result is greater than a minimum value.
        
        Args:
            result: The query result
            min_count: The minimum expected number of rows
        """
        with allure.step(f"Assert row count is greater than {min_count}"):
            actual_count = len(result)
            assert actual_count > min_count, f"Expected more than {min_count} rows, got {actual_count}"
    
    @staticmethod
    def row_count_less_than(result: List[Tuple], max_count: int) -> None:
        """
        Assert the number of rows in the result is less than a maximum value.
        
        Args:
            result: The query result
            max_count: The maximum expected number of rows
        """
        with allure.step(f"Assert row count is less than {max_count}"):
            actual_count = len(result)
            assert actual_count < max_count, f"Expected less than {max_count} rows, got {actual_count}"
    
    @staticmethod
    def contains_column(columns: List[Dict[str, Any]], column_name: str) -> None:
        """
        Assert that a table schema contains a specific column.
        
        Args:
            columns: The table schema as a list of dictionaries
            column_name: The name of the column to check for
        """
        with allure.step(f"Assert schema contains column '{column_name}'"):
            column_names = [col['name'] for col in columns]
            assert column_name in column_names, f"Column '{column_name}' not found in table schema"
    
    @staticmethod
    def column_is_of_type(columns: List[Dict[str, Any]], column_name: str, data_type: str) -> None:
        """
        Assert that a column in a table schema is of a specific data type.
        
        Args:
            columns: The table schema as a list of dictionaries
            column_name: The name of the column
            data_type: The expected data type
        """
        with allure.step(f"Assert column '{column_name}' is of type '{data_type}'"):
            for col in columns:
                if col['name'] == column_name:
                    actual_type = col['data_type']
                    assert actual_type.lower() == data_type.lower(), \
                        f"Expected column '{column_name}' to be of type '{data_type}', got '{actual_type}'"
                    return
            assert False, f"Column '{column_name}' not found in table schema"

    @staticmethod
    def result_contains(result: List[Tuple], expected_data: Union[Tuple, List[Tuple]]) -> None:
        """
        Assert that the result contains specific data.
        
        Args:
            result: The query result
            expected_data: A single row or list of rows that should be in the result
        """
        # Convert expected_data to a list if it's a single tuple
        if isinstance(expected_data, tuple):
            expected_data = [expected_data]
        
        with allure.step(f"Assert result contains expected data"):
            for row in expected_data:
                assert row in result, f"Expected row {row} not found in result"
    
    @staticmethod
    def result_not_contains(result: List[Tuple], unexpected_data: Union[Tuple, List[Tuple]]) -> None:
        """
        Assert that the result does not contain specific data.
        
        Args:
            result: The query result
            unexpected_data: A single row or list of rows that should not be in the result
        """
        # Convert unexpected_data to a list if it's a single tuple
        if isinstance(unexpected_data, tuple):
            unexpected_data = [unexpected_data]
        
        with allure.step(f"Assert result does not contain unexpected data"):
            for row in unexpected_data:
                assert row not in result, f"Unexpected row {row} found in result"
    
    @staticmethod
    def result_equals(result: List[Tuple], expected_result: List[Tuple]) -> None:
        """
        Assert that the result exactly equals the expected result.
        
        Args:
            result: The query result
            expected_result: The expected result
        """
        with allure.step(f"Assert result equals expected result"):
            assert result == expected_result, f"Result does not match expected result"
    
    @staticmethod
    def column_values_match(result: List[Tuple], column_index: int, expected_values: List[Any]) -> None:
        """
        Assert that the values in a specific column match expected values.
        
        Args:
            result: The query result
            column_index: The index of the column
            expected_values: The expected values in that column
        """
        with allure.step(f"Assert values in column {column_index} match expected values"):
            actual_values = [row[column_index] for row in result]
            assert actual_values == expected_values, \
                f"Values in column {column_index} do not match expected values"
    
    @staticmethod
    def column_values_contain(result: List[Tuple], column_index: int, expected_value: Any) -> None:
        """
        Assert that the values in a specific column contain an expected value.
        
        Args:
            result: The query result
            column_index: The index of the column
            expected_value: The expected value to be contained
        """
        with allure.step(f"Assert values in column {column_index} contain '{expected_value}'"):
            actual_values = [row[column_index] for row in result]
            assert expected_value in actual_values, \
                f"Value '{expected_value}' not found in column {column_index}"
    
    @staticmethod
    def column_values_all_match_condition(result: List[Tuple], column_index: int, 
                                         condition_fn: callable, condition_desc: str) -> None:
        """
        Assert that all values in a specific column satisfy a condition.
        
        Args:
            result: The query result
            column_index: The index of the column
            condition_fn: A function that takes a value and returns True if the condition is satisfied
            condition_desc: A description of the condition for reporting
        """
        with allure.step(f"Assert all values in column {column_index} satisfy: {condition_desc}"):
            actual_values = [row[column_index] for row in result]
            failing_values = [value for value in actual_values if not condition_fn(value)]
            assert not failing_values, \
                f"Values in column {column_index} that don't satisfy '{condition_desc}': {failing_values}"

# Pytest-xdist Best Practices

This guide covers best practices for ensuring proper test isolation when running tests in parallel using pytest-xdist.

## Table of Contents

- [Introduction](#introduction)
- [1. Use Unique Resources for Each Test Process](#1-use-unique-resources-for-each-test-process)
  - [Database Testing](#database-testing)
  - [File System Operations](#file-system-operations)
- [2. Avoid Global State](#2-avoid-global-state)
  - [Static Variables](#static-variables)
  - [Singleton Objects](#singleton-objects)
- [3. Avoid Timing Dependencies](#3-avoid-timing-dependencies)
  - [Use Proper Waiting Mechanisms](#use-proper-waiting-mechanisms)
- [4. Use Worker-Specific Test Data](#4-use-worker-specific-test-data)
  - [Generate Unique Test Data](#generate-unique-test-data)
  - [Parameterize Tests Wisely](#parameterize-tests-wisely)
- [5. Utilize pytest-xdist's Built-in Fixtures](#5-utilize-pytest-xdists-built-in-fixtures)
  - [Worker ID Fixture](#worker-id-fixture)
  - [Lock Fixture for Critical Sections](#lock-fixture-for-critical-sections)
- [6. Port and Resource Management](#6-port-and-resource-management)
  - [Dynamic Port Allocation](#dynamic-port-allocation)
  - [Resource Cleanup](#resource-cleanup)
- [7. Test Interdependency Management](#7-test-interdependency-management)
  - [Avoid Order Dependencies](#avoid-order-dependencies)
  - [Fixture Scopes](#fixture-scopes)
- [8. Environment Variables and Configuration](#8-environment-variables-and-configuration)
  - [Isolate Environment Variables](#isolate-environment-variables)
  - [Worker-Specific Config Files](#worker-specific-config-files)
- [9. UI Testing Specifics](#9-ui-testing-specifics)
  - [Browser Instance Isolation](#browser-instance-isolation)
  - [Isolated Storage State](#isolated-storage-state)
- [10. Implementation in Your Framework](#10-implementation-in-your-framework)

## Introduction

When running tests in parallel with pytest-xdist, proper test isolation is critical to avoid race conditions, flaky tests, and intermittent failures. This document provides best practices and code examples to ensure your tests run reliably in parallel.

## 1. Use Unique Resources for Each Test Process

### Database Testing

Create isolated database resources for each test worker:

```python
@pytest.fixture(scope="session")
def test_db_connection(worker_id):
    """Create a unique database schema for each worker process."""
    # For PostgreSQL
    schema_name = f"test_schema_{worker_id}"
    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", 5432),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
        database=os.environ.get("POSTGRES_DB", "testdb")
    )
    
    # Create a schema for this worker and set it as default
    with conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        cur.execute(f"SET search_path TO {schema_name}")
    conn.commit()
    
    yield conn
    
    # Clean up after tests are done
    with conn.cursor() as cur:
        cur.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")
    conn.commit()
    conn.close()
```

Use transaction rollbacks to isolate each test:

```python
@pytest.fixture(scope="function")
def db_transaction(db_connection):
    """Create a transaction that will be rolled back after the test."""
    conn = db_connection
    # Save the current autocommit state
    original_autocommit = conn.autocommit
    conn.autocommit = False
    
    # Start a transaction
    with conn.cursor() as cur:
        cur.execute("BEGIN")
    
    yield conn
    
    # Rollback changes after each test
    conn.rollback()
    # Restore original autocommit state
    conn.autocommit = original_autocommit
```

### File System Operations

Use temporary directories specific to each worker:

```python
@pytest.fixture
def temp_dir(worker_id, tmp_path):
    """Create a worker-specific temporary directory."""
    worker_path = tmp_path / f"worker_{worker_id}"
    worker_path.mkdir(exist_ok=True)
    return worker_path
```

## 2. Avoid Global State

### Static Variables

Avoid using static variables that can cause shared state:

```python
# BAD - Shared state across processes
class TestClass:
    shared_resource = None  # This is shared across all test processes!
    
    def test_something(self):
        TestClass.shared_resource = "modified"  # Modifies shared state

# GOOD - Instance-level state
class TestClass:
    def setup_method(self):
        self.resource = None  # Instance-level, not shared between processes
        
    def test_something(self):
        self.resource = "modified"  # Only affects this test instance
```

### Singleton Objects

Reset singletons between tests:

```python
# Assuming you have a singleton like this
class MySingleton:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls):
        cls._instance = None

# Reset before each test
@pytest.fixture(autouse=True)
def reset_singleton():
    MySingleton.reset()
    yield
```

## 3. Avoid Timing Dependencies

### Use Proper Waiting Mechanisms

Avoid arbitrary sleep times and use explicit waits:

```python
# BAD
def test_with_sleep():
    submit_form()
    time.sleep(3)  # Arbitrary wait time, may not be enough or wastes time
    assert check_result()

# GOOD - In UI testing with Playwright
def test_with_explicit_wait(page):
    page.click("button#submit")
    page.wait_for_selector("div.success-message", state="visible")
    assert page.inner_text("div.success-message") == "Success!"
```

Create helper functions for complex waiting conditions:

```python
def wait_for_condition(condition_func, timeout=10, poll_interval=0.5):
    """Wait for a condition to be true with timeout."""
    start_time = time.time()
    last_exception = None
    
    while time.time() - start_time < timeout:
        try:
            if condition_func():
                return True
        except Exception as e:
            last_exception = e
        time.sleep(poll_interval)
    
    if last_exception:
        raise TimeoutError(f"Condition not met within {timeout}s. Last error: {last_exception}")
    raise TimeoutError(f"Condition not met within {timeout}s")

# Usage example
def test_with_custom_wait(api_client):
    job_id = api_client.start_job()
    
    # Wait for job to complete
    wait_for_condition(
        lambda: api_client.get_job_status(job_id) == "completed",
        timeout=30
    )
    
    result = api_client.get_job_result(job_id)
    assert result["status"] == "success"
```

## 4. Use Worker-Specific Test Data

### Generate Unique Test Data

Create unique test data for each worker:

```python
@pytest.fixture
def unique_user(worker_id):
    """Create a user with a unique name based on worker ID."""
    timestamp = int(time.time())
    return {
        "username": f"test_user_{worker_id}_{timestamp}",
        "email": f"user_{worker_id}_{timestamp}@example.com",
        "password": "password123"
    }

def test_user_registration(api_client, unique_user):
    response = api_client.register_user(unique_user)
    assert response["status"] == "success"
    assert response["user"]["username"] == unique_user["username"]
```

### Parameterize Tests Wisely

Use parameterization to create independent test cases:

```python
# Each worker gets a completely independent test case
@pytest.mark.parametrize("test_input,expected", [
    ("input_a", "result_a"),
    ("input_b", "result_b"),
    ("input_c", "result_c"),
    ("input_d", "result_d"),
])
def test_something(test_input, expected):
    assert process(test_input) == expected
```

## 5. Utilize pytest-xdist's Built-in Fixtures

### Worker ID Fixture

Use the worker_id fixture for resource isolation:

```python
def test_with_worker_id(worker_id):
    """Use worker_id to create isolated resources."""
    # The worker_id will be "gw0", "gw1", etc., or "master" when not using xdist
    resource_name = f"resource_{worker_id}"
    
    # Use resource_name for isolation
    with open(f"/tmp/{resource_name}.txt", "w") as f:
        f.write("test data")
    
    # Test logic...
```

### Lock Fixture for Critical Sections

Use the xdist_lockfile fixture for shared resources:

```python
def test_critical_shared_resource(xdist_lockfile):
    """Use lock to safely access a shared resource."""
    # This will prevent other workers from entering this block at the same time
    with xdist_lockfile("my_shared_resource"):
        # Safely modify a shared resource that cannot be isolated
        with open("/tmp/shared_counter.txt", "r+") as f:
            value = int(f.read().strip() or "0")
            value += 1
            f.seek(0)
            f.write(str(value))
            f.truncate()
```

## 6. Port and Resource Management

### Dynamic Port Allocation

Allocate ports dynamically based on worker ID:

```python
@pytest.fixture
def server_port(worker_id):
    """Allocate a unique port for each worker."""
    # Base port + worker offset ensures unique ports
    base_port = 8000
    
    # Convert "gw0", "gw1", etc. to integers 0, 1, etc.
    if worker_id == "master":
        worker_num = 0
    else:
        worker_num = int(worker_id.replace("gw", ""))
    
    return base_port + worker_num

@pytest.fixture
def http_server(server_port):
    """Start an HTTP server on a worker-specific port."""
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    import threading
    
    server = HTTPServer(('localhost', server_port), SimpleHTTPRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    yield server_port
    
    server.shutdown()
    server.server_close()
```

### Resource Cleanup

Always clean up resources, even on failure:

```python
@pytest.fixture
def resource_fixture():
    """Create and clean up a resource, even on test failure."""
    # Setup resource
    resource = create_resource()
    
    try:
        yield resource
    finally:
        # Always clean up, even if tests fail
        cleanup_resource(resource)
```

## 7. Test Interdependency Management

### Avoid Order Dependencies

Never write tests that depend on execution order:

```python
# BAD - Tests depend on execution order
def test_1_create():
    # Creates a resource needed by test_2
    result = create_resource()
    assert result["id"] is not None
    
def test_2_use():
    # Assumes test_1_create has run first and created a resource
    resources = list_resources()
    assert len(resources) > 0

# GOOD - Each test is self-contained
def test_create_and_verify():
    resource = create_resource()
    assert resource["id"] is not None
    
def test_use_resource():
    # Create fresh resource for this test
    resource = create_resource()
    result = use_resource(resource["id"])
    assert result["status"] == "success"
```

### Fixture Scopes

Use appropriate fixture scopes:

```python
# Function scope - recreated for each test (safest for parallelism)
@pytest.fixture(scope="function")
def volatile_resource():
    """Create a fresh resource for each test."""
    resource = create_resource()
    yield resource
    delete_resource(resource["id"])

# Module scope - shared within a module, but not across modules
@pytest.fixture(scope="module")
def module_resource():
    """Create a resource shared by all tests in a module."""
    resource = create_expensive_resource()
    yield resource
    delete_resource(resource["id"])

# Session scope with worker ID for parallel safety
@pytest.fixture(scope="session")
def session_resource(worker_id):
    """Create a resource shared by all tests in a worker session."""
    resource = create_expensive_resource(name=f"session_{worker_id}")
    yield resource
    delete_resource(resource["id"])
```

## 8. Environment Variables and Configuration

### Isolate Environment Variables

Isolate environment variables for each worker:

```python
@pytest.fixture
def isolated_env_vars(worker_id, monkeypatch):
    """Set worker-specific environment variables."""
    # Set worker-specific environment variables
    monkeypatch.setenv("TEST_PROCESS_ID", worker_id)
    monkeypatch.setenv("TEMP_DIR", f"/tmp/test_{worker_id}")
    monkeypatch.setenv("API_PORT", str(8000 + int(worker_id.replace("gw", "")) if worker_id != "master" else 8000))
    
    return worker_id

def test_with_env_vars(isolated_env_vars):
    """Test that uses isolated environment variables."""
    assert os.environ["TEST_PROCESS_ID"] == isolated_env_vars
    # Test logic using the environment variables...
```

### Worker-Specific Config Files

Create and use config files specific to each worker:

```python
@pytest.fixture(scope="session")
def worker_config(worker_id, tmp_path_factory):
    """Create a worker-specific configuration file."""
    # Create worker-specific config directory
    config_dir = tmp_path_factory.getbasetemp() / f"worker_{worker_id}_config"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.json"
    
    # Convert worker_id to numeric value for port offset
    if worker_id == "master":
        worker_num = 0
    else:
        worker_num = int(worker_id.replace("gw", ""))
    
    # Create worker-specific configuration
    config = {
        "worker_id": worker_id,
        "test_port": 8000 + worker_num,
        "db_schema": f"test_schema_{worker_id}",
        "api_url": f"http://localhost:{8000 + worker_num}/api",
        "temp_dir": str(tmp_path_factory.getbasetemp() / f"worker_{worker_id}_temp")
    }
    
    # Ensure temp directory exists
    os.makedirs(config["temp_dir"], exist_ok=True)
    
    # Write config to file
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)
    
    return config_file

def test_with_config(worker_config):
    """Test that uses worker-specific config."""
    with open(worker_config) as f:
        config = json.load(f)
    
    # Use the worker-specific configuration
    api_client = APIClient(base_url=config["api_url"])
    response = api_client.get("/status")
    assert response["status"] == "ok"
```

## 9. UI Testing Specifics

### Browser Instance Isolation

Use separate browser instances for each worker:

```python
@pytest.fixture(scope="session")
def browser_context(worker_id, playwright):
    """Create a worker-specific browser context."""
    # Launch browser
    browser = playwright.chromium.launch(headless=True)
    
    # Create a worker-specific context
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        user_agent=f"TestAgent/1.0 (Worker-{worker_id})"
    )
    
    yield context
    
    # Clean up
    context.close()
    browser.close()

@pytest.fixture
def page(browser_context):
    """Create a new page for each test."""
    page = browser_context.new_page()
    yield page
    page.close()
```

### Isolated Storage State

Use separate storage states for browser cookies/localStorage:

```python
@pytest.fixture
def auth_context(browser_context, worker_id, tmp_path):
    """Create an authenticated browser context with isolated storage."""
    storage_file = tmp_path / f"storage_state_{worker_id}.json"
    
    # Setup authentication in a temporary page
    page = browser_context.new_page()
    page.goto("https://example.com/login")
    page.fill("input#username", "testuser")
    page.fill("input#password", "password")
    page.click("button#login")
    page.wait_for_url("**/dashboard")
    
    # Save authentication state to worker-specific storage file
    browser_context.storage_state(path=storage_file)
    page.close()
    
    # Create new context with this storage state
    context = browser_context.browser.new_context(storage_state=storage_file)
    yield context
    context.close()

@pytest.fixture
def auth_page(auth_context):
    """Create authenticated page for each test."""
    page = auth_context.new_page()
    yield page
    page.close()
```

## 10. Implementation in Your Framework

Here's how to implement these best practices in your automation framework:

### Creating a Common Helper Module

```python
# utils/xdist_helpers.py

import os
import pytest
import time

def get_worker_id():
    """Get the current worker ID, or 'master' if not using xdist."""
    return getattr(pytest, "xdist_worker", "master") or "master"
    
def get_worker_temp_dir(base_dir):
    """Create and return a worker-specific temporary directory."""
    worker_id = get_worker_id()
    worker_dir = os.path.join(base_dir, f"worker_{worker_id}")
    os.makedirs(worker_dir, exist_ok=True)
    return worker_dir

def get_worker_num():
    """Convert worker_id to a numeric value for port offsets etc."""
    worker_id = get_worker_id()
    if worker_id == "master":
        return 0
    return int(worker_id.replace("gw", ""))

def get_unique_resource_name(prefix):
    """Generate a unique resource name based on worker ID and timestamp."""
    worker_id = get_worker_id()
    timestamp = int(time.time())
    return f"{prefix}_{worker_id}_{timestamp}"
```

### Add a Section in Your Framework's conftest.py

```python
# tests/conftest.py

import os
import pytest
from utils.xdist_helpers import get_worker_id, get_worker_temp_dir

@pytest.fixture(scope="session", autouse=True)
def configure_xdist_isolation(worker_id, tmp_path_factory):
    """Configure isolation for pytest-xdist workers."""
    # Create worker-specific directories
    worker_tmp = tmp_path_factory.getbasetemp() / f"worker_{worker_id}"
    worker_tmp.mkdir(exist_ok=True)
    
    # Set worker-specific environment variables
    os.environ["WORKER_ID"] = worker_id
    os.environ["WORKER_TEMP"] = str(worker_tmp)
    
    # Configure database isolation if needed
    if worker_id != "master":
        # Set worker-specific DB schema or connection params
        os.environ["DB_SCHEMA"] = f"test_schema_{worker_id}"
    
    # Return worker ID for other fixtures to use
    return worker_id
```

### Update Your Database Helper

```python
# utils/db_helper.py

import os
import psycopg2
from utils.xdist_helpers import get_worker_id

def get_db_connection(config):
    """Get a database connection with worker isolation."""
    worker_id = get_worker_id()
    schema = config.get("schema") or f"test_schema_{worker_id}"
    
    # Connect to database
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"]
    )
    
    # Set search path to worker-specific schema
    with conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        cur.execute(f"SET search_path TO {schema}")
    conn.commit()
    
    return conn

def cleanup_db_schema(conn, schema=None):
    """Clean up a worker-specific schema."""
    if schema is None:
        worker_id = get_worker_id()
        schema = f"test_schema_{worker_id}"
    
    with conn.cursor() as cur:
        cur.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
    conn.commit()
```

By implementing these best practices, you'll ensure that your tests can run in parallel without interference, leading to more reliable test results and significantly faster test execution times.


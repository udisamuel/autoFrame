# Pytest-xdist Usage Guide

This guide provides a quick reference for using pytest-xdist for parallel test execution in your automation framework.

## Basic Usage

### Running Tests in Parallel

```bash
# Run tests using all available CPU cores
pytest -n auto

# Run tests with a specific number of workers
pytest -n 4

# Run only marked tests in parallel
pytest -n auto -m integration

# Using our run_tests.sh script (automatically uses optimal number of processes)
./run_tests.sh

# Using run_tests.sh with specific options
./run_tests.sh -m integration
```

## Distribution Modes

```bash
# Default load balancing mode - distributes tests among workers
pytest -n 4

# Load file distribution - distribute by test file
pytest -n 4 --dist=loadfile

# Load scope distribution - distribute by test scope (requires pytest plugins)
pytest -n 4 --dist=loadscope

# Load group distribution - distribute by test group (requires markers)
pytest -n 4 --dist=loadgroup
```

## Useful Options

```bash
# Run failed tests first
pytest -n 4 --failed-first

# Stop after first failure
pytest -n 4 -x

# Limit the number of failures
pytest -n 4 --maxfail=5

# Show output from all workers in real-time
pytest -n 4 -v

# Disable output capturing (show all stdout/stderr)
pytest -n 4 -s
```

## Worker-Specific Fixtures

```python
# Using the worker_id fixture
def test_example(worker_id):
    print(f"Running on worker {worker_id}")
    # Will print "Running on worker gw0", "Running on worker gw1", etc.

# Using the xdist_lockfile fixture
def test_shared_resource(xdist_lockfile):
    with xdist_lockfile("resource_name"):
        # Critical section that accesses a shared resource
        # Only one worker can run this block at a time
```

## Load Balancing Strategies

### When to use each distribution mode:

1. **--dist=load** (default): 
   - Distributes tests to available workers as they finish their previous tests
   - Best for tests with varying execution times
   - Generally the fastest approach

2. **--dist=loadfile**:
   - Sends all tests from a single file to the same worker
   - Best when tests in the same file share expensive setup/teardown at module level
   - Good for file-specific fixtures with scope="module"

3. **--dist=loadscope**:
   - Group tests with common scope (class, module, or session) to the same worker
   - Best for tests with shared fixture state
   - Requires proper fixture setup

4. **--dist=loadgroup**:
   - Group tests explicitly marked with the same group
   - Best for manually controlling test distribution
   - Example: `@pytest.mark.xdist_group("database")`

## Performance Considerations

1. **Optimal Number of Workers**:
   - A good rule of thumb is to use `N - 1` workers, where N is the number of CPU cores
   - Our `run_tests.sh` script calculates this automatically

2. **Test Collection Time**:
   - For large test suites, collection time can be significant
   - Consider using pytest-xvs to run only changed tests

3. **Memory Usage**:
   - Each worker uses additional memory
   - If memory is limited, reduce the number of workers

4. **CI/CD Considerations**:
   - In CI/CD environments, worker count may be limited by the build server
   - GitHub Actions: Standard runners typically have 2 cores

## Debugging

```bash
# Debug with a single worker
pytest -n0

# Debug specific tests with a specific worker
pytest -n1 tests/test_specific.py::test_name

# See what's happening inside each worker (useful for debugging)
pytest -n2 --verbose
```

## Common Issues & Solutions

### 1. Test Isolation Problems

If you see flaky tests when running in parallel but they pass sequentially:
- Check for shared state between tests
- Ensure tests don't rely on global variables
- Use proper worker-specific resources

### 2. Fixture Issues

If fixtures aren't properly isolated:
- Use the worker_id fixture to create isolated resources
- Avoid session-scoped fixtures that modify shared state
- Review our best practices document for detailed solutions

### 3. Performance Bottlenecks

If tests run slower than expected:
- Check if tests are I/O or CPU bound
- Use --dist=loadfile for tests with shared setup
- Identify and optimize slow tests

## Conclusion

Pytest-xdist is a powerful tool to speed up your test execution by running tests in parallel. By following best practices for test isolation and choosing appropriate distribution modes, you can achieve significant time savings while maintaining reliable test results.

For detailed best practices and code examples, see [pytest_xdist_best_practices.md](./pytest_xdist_best_practices.md).

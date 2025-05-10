# Performance Testing with Locust

This directory contains performance tests using [Locust](https://locust.io/), an open source load testing tool.

## Setup

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Running Tests

To run a performance test:

```bash
cd performance
locust -f locustfiles/example_test.py
```

Then open your browser to http://localhost:8089 to access the Locust web interface.

## Structure

- `locustfiles/`: Contains all Locust test files
- `data/`: Test data files (if needed)
- `configs/`: Configuration files for different test environments
- `reports/`: Generated test reports

## Creating New Tests

Create a new Python file in the `locustfiles` directory. See `example_test.py` for a basic template.

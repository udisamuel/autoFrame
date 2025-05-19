#!/usr/bin/env python
"""
Script to run tests with Jira/Xray integration.

This script:
1. Creates a new Xray Test Execution
2. Runs the tests with Jira and Xray integration
3. Reports test results back to Xray

Usage:
    python run_tests_with_xray.py [test_pattern] [--no-execution]

Arguments:
    test_pattern     Optional pattern to filter tests (e.g., tests/test_api_*.py)
    --no-execution   Run tests without creating a new Test Execution

Examples:
    python run_tests_with_xray.py
    python run_tests_with_xray.py tests/test_api_*.py
    python run_tests_with_xray.py --no-execution
"""

import argparse
import os
import re
import subprocess
import sys
import time
from datetime import datetime

# Add project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import Config
from utils.jira_helper import JiraHelper
from utils.xray_helper import XrayHelper


def collect_test_keys(test_pattern):
    """Collect Xray test keys from test files matching the pattern."""
    import glob
    
    # Default pattern if none provided
    if not test_pattern:
        test_pattern = "tests/test_*.py"
    
    # Get all test files
    test_files = glob.glob(test_pattern)
    
    # Extract test keys from markers
    test_keys = set()
    for file in test_files:
        try:
            with open(file, 'r') as f:
                content = f.read()
                # Look for pytest.mark.xray annotations
                matches = re.findall(r'@pytest\.mark\.xray\(test_key=\"([^\"]+)\"', content)
                for match in matches:
                    test_keys.add(match)
        except Exception as e:
            print(f'Error processing {file}: {e}')
    
    return list(test_keys)


def create_test_execution(test_keys):
    """Create a new Test Execution in Xray."""
    if not Config.JIRA_ENABLED or not Config.XRAY_ENABLED:
        print("Jira or Xray integration not enabled in configuration")
        return None
    
    if not test_keys:
        print("No Xray test keys found in test files")
        return None
    
    try:
        jira_helper = JiraHelper()
        xray_helper = XrayHelper(jira_helper=jira_helper)
        
        # Create the test execution
        print(f"Creating Test Execution with {len(test_keys)} tests...")
        execution = xray_helper.create_test_execution(
            summary=f'Automated Test Execution - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            description=f'Automated test execution created by run_tests_with_xray.py',
            test_keys=test_keys
        )
        
        # Extract the execution key
        if isinstance(execution, dict) and 'key' in execution:
            print(f"Created Test Execution: {execution['key']}")
            return execution['key']
        else:
            print(f"Unexpected response format: {execution}")
            return None
    except Exception as e:
        print(f"Error creating Test Execution: {e}")
        return None


def run_tests(test_pattern, execution_key=None):
    """Run the tests with pytest."""
    # Default pattern if none provided
    if not test_pattern:
        test_pattern = "tests/"
    
    # Set the execution key as an environment variable if provided
    env = os.environ.copy()
    if execution_key:
        env["XRAY_EXECUTION_KEY"] = execution_key
    
    # Run the tests
    command = [
        "python", "-m", "pytest", 
        test_pattern, 
        "-v", 
        "--junitxml=reports/junit-results.xml"
    ]
    
    print(f"Running tests: {' '.join(command)}")
    start_time = time.time()
    
    process = subprocess.Popen(
        command,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    # Stream the output
    for line in process.stdout:
        print(line, end='')
    
    process.wait()
    
    end_time = time.time()
    print(f"Tests completed in {end_time - start_time:.2f} seconds")
    
    return process.returncode


def import_results_to_xray(execution_key):
    """Import JUnit results to Xray."""
    if not execution_key:
        print("No Test Execution key provided, skipping import to Xray")
        return
    
    if not os.path.exists("reports/junit-results.xml"):
        print("JUnit results file not found, skipping import to Xray")
        return
    
    try:
        jira_helper = JiraHelper()
        xray_helper = XrayHelper(jira_helper=jira_helper)
        
        print(f"Importing test results to Xray execution {execution_key}...")
        result = xray_helper.import_results_from_junit(
            execution_key=execution_key,
            junit_path='reports/junit-results.xml'
        )
        print(f"Successfully imported results to execution {execution_key}")
    except Exception as e:
        print(f"Error importing results to Xray: {e}")


def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Run tests with Jira/Xray integration')
    parser.add_argument('test_pattern', nargs='?', help='Pattern to filter tests')
    parser.add_argument('--no-execution', action='store_true', help='Run tests without creating a Test Execution')
    
    args = parser.parse_args()
    
    # Make sure reports directory exists
    os.makedirs("reports", exist_ok=True)
    
    execution_key = None
    if not args.no_execution:
        # Collect test keys and create test execution
        test_keys = collect_test_keys(args.test_pattern)
        execution_key = create_test_execution(test_keys)
    
    # Run the tests
    return_code = run_tests(args.test_pattern, execution_key)
    
    # Import results to Xray
    if execution_key:
        import_results_to_xray(execution_key)
    
    return return_code


if __name__ == "__main__":
    sys.exit(main())

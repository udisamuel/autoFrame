# Jira and Xray Integration Guide

This document provides information on how to set up and use the Jira and Xray integration with the autoFrame test framework.

## Overview

The integration allows tests to:
- Be linked to Jira test cases
- Report test results to Xray
- Create Jira issues automatically for failed tests
- Import JUnit XML results into Xray test executions

## Setup

### Configuration

1. Add the following configuration to your `.env` file:

```
# Jira Configuration
JIRA_ENABLED=true
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=PROJ

# Xray Configuration
XRAY_ENABLED=true
XRAY_CLOUD=true  # Set to false if using Xray Server/Data Center
XRAY_AUTO_REPORT_RESULTS=true

# Xray Cloud specific settings
XRAY_CLIENT_ID=your-client-id
XRAY_CLIENT_SECRET=your-client-secret

# Xray Server/Data Center specific settings (only if XRAY_CLOUD=false)
XRAY_TEST_EXECUTION_TYPE_FIELD=customfield_10100
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Create Test Cases in Jira/Xray and note their issue keys.

### Test Marking

Mark your tests with the Xray test key using the `xray` marker:

```python
@pytest.mark.xray(test_key="PROJ-123", summary="Test API endpoint")
def test_api_functionality():
    # Test code here
    pass
```

## Running Tests with Xray Integration

### Option 1: Using the Framework's Built-in Reporting

When running tests, the framework will automatically report the test results to Xray if the integration is enabled.

```bash
python -m pytest tests/test_my_feature.py -v
```

### Option 2: Import JUnit XML Reports

1. Run the tests with JUnit XML output:

```bash
python -m pytest tests/test_my_feature.py -v --junitxml=reports/junit_results.xml
```

2. Import the JUnit results to Xray using the helper:

```python
from utils.xray_helper import XrayHelper
from utils.jira_helper import JiraHelper

jira_helper = JiraHelper()
xray_helper = XrayHelper(jira_helper=jira_helper)

# Create a new test execution from the JUnit results
execution = xray_helper.import_results_from_junit(
    execution_key=None,  # None to create a new execution
    junit_path="reports/junit_results.xml"
)
```

## Helper Classes

The integration provides two helper classes:

### JiraHelper

Located in `utils/jira_helper.py`, this class provides methods for interacting with the Jira API:

- `create_issue`: Create a new Jira issue
- `update_issue`: Update an existing issue
- `add_comment`: Add a comment to an issue
- `get_issue`: Get issue details
- `search_issues`: Search for issues using JQL
- `create_issue_link`: Create a link between two issues
- `transition_issue`: Change the status of an issue
- `get_available_transitions`: Get available status transitions
- `upload_attachment`: Attach a file to an issue

### XrayHelper

Located in `utils/xray_helper.py`, this class provides methods for interacting with the Xray API:

- `create_test_execution`: Create a new Test Execution issue
- `report_test_results`: Report test results to an existing Test Execution
- `import_results_from_junit`: Import test results from a JUnit XML file
- `get_test_by_id`: Get details for a specific Test issue
- `get_tests_by_execution`: Get all tests in a Test Execution

## Fixtures

The following pytest fixtures are available for use in your tests:

- `jira_helper`: An instance of `JiraHelper`
- `xray_helper`: An instance of `XrayHelper`
- `xray_test_info`: Information about the Xray test from the marker

## Example Test

```python
import pytest
import allure

@allure.feature("User Management")
@pytest.mark.xray(test_key="PROJ-123", summary="Test user login")
def test_user_login(jira_helper, xray_helper, xray_test_info):
    """Test user login functionality."""
    # Test code here
    assert True, "Login test passed"
```

## Automatic Jira Issue Creation for Failed Tests

The framework can automatically create Jira issues for failed tests:

```python
@pytest.mark.xray(test_key="PROJ-456", summary="Feature test")
def test_feature(jira_helper, xray_helper, xray_test_info):
    try:
        # Test code that might fail
        assert False, "Feature not working"
    except AssertionError as e:
        if jira_helper:
            issue = jira_helper.create_issue(
                summary=f"Test Failure: {xray_test_info['summary']}",
                description=f"The test {xray_test_info['test_key']} failed with error: {str(e)}",
                issue_type="Bug",
                priority="Medium",
                labels=["automated-test"]
            )
            
            # Link the issue to the test in Xray
            if xray_helper:
                jira_helper.create_issue_link(
                    link_type="Tests",
                    inward_issue=issue["key"],
                    outward_issue=xray_test_info["test_key"]
                )
                
            pytest.fail(f"Test failed and created Jira issue: {issue['key']}")
        else:
            pytest.fail(str(e))
```

## Using with Allure Reports

The Jira and Xray integration works well with Allure reports. The integration will add information about the test's Jira/Xray links to the Allure report.

To run tests with Allure reporting:

```bash
python -m pytest tests/test_my_feature.py -v --alluredir=reports/allure-results
```

Then generate the Allure report:

```bash
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

## Troubleshooting

### Connection Issues

- Verify your Jira base URL, username, and API token
- For Xray Cloud, verify your client ID and client secret
- Check that you have the necessary permissions in Jira

### Test Reporting Issues

- Ensure the test key in the marker matches a valid Test issue in Jira
- Check that you have an active test execution (XRAY_EXECUTION_KEY environment variable)
- Verify that your API tokens and credentials have not expired

### Other Issues

- Look for detailed error messages in the test output
- Check the Jira and Xray API documentation for any changes that might affect the integration

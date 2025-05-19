# Jira and Xray Integration - Implementation Summary

## Overview

This document summarizes the changes made to integrate Jira and Xray with the autoFrame test framework.

## Files Created

1. **utils/jira_helper.py**
   - Helper class for Jira API integration
   - Methods for creating, updating, and querying issues
   - Support for issue transitions, attachments, and linking

2. **utils/xray_helper.py**
   - Helper class for Xray API integration
   - Support for both Xray Cloud and Xray Server/Data Center
   - Methods for test execution creation and test result reporting

3. **tests/test_jira_xray_integration.py**
   - Example test file demonstrating Jira and Xray integration
   - Examples of test marking with Xray test keys
   - Automatic issue creation for failed tests

4. **docs/jira_xray_integration.md**
   - Comprehensive documentation for using the integration
   - Setup instructions
   - Usage examples
   - Troubleshooting tips

## Files Modified

1. **config/config.py**
   - Added Jira configuration settings
   - Added Xray configuration settings
   - Settings for Xray Cloud and Server/Data Center variants

2. **tests/conftest.py**
   - Added Jira and Xray fixture definitions
   - Added hooks for automatic test result reporting
   - Added support for extracting Xray test info from markers

3. **requirements.txt**
   - Added pytest-xray package for enhanced integration

4. **.env.example**
   - Added Jira and Xray configuration examples

5. **README.md**
   - Added documentation for Jira and Xray integration
   - Added example commands for running tests with Jira/Xray integration

## Features Implemented

1. **Jira Integration**
   - Issue creation, updating, and retrieval
   - Searching for issues using JQL
   - Creating links between issues
   - Adding comments and attachments
   - Transitioning issues between statuses

2. **Xray Integration**
   - Test execution creation
   - Test result reporting
   - JUnit XML report import
   - Support for both Xray Cloud and Server/Data Center

3. **Test Framework Integration**
   - Pytest markers for linking tests to Xray test issues
   - Automatic test result reporting to Xray
   - Automatic issue creation for failed tests
   - Screenshots and logs as evidence in Xray

## Usage Examples

### Marking Tests with Xray Test Keys

```python
@pytest.mark.xray(test_key="TEST-123", summary="Test description")
def test_feature():
    # Test implementation
    assert True
```

### Creating Test Executions

```python
def test_create_execution(xray_helper):
    execution = xray_helper.create_test_execution(
        summary="Sprint 1 Regression",
        description="Automated regression tests for Sprint 1",
        test_keys=["TEST-123", "TEST-124", "TEST-125"]
    )
    
    # Store the execution key for later use
    os.environ["XRAY_EXECUTION_KEY"] = execution["key"]
```

### Automatic Jira Issue Creation for Failed Tests

```python
def test_with_jira_issue_creation(jira_helper, xray_helper, xray_test_info):
    try:
        # Test that might fail
        assert False, "Feature not working"
    except AssertionError as e:
        if jira_helper:
            issue = jira_helper.create_issue(
                summary=f"Test Failure: {xray_test_info['summary']}",
                description=f"Error: {str(e)}",
                issue_type="Bug"
            )
            pytest.fail(f"Test failed and created Jira issue: {issue['key']}")
        else:
            pytest.fail(str(e))
```

## Configuration

The integration can be enabled by setting these environment variables:

```
# Jira Configuration
JIRA_ENABLED=true
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=PROJ

# Xray Configuration
XRAY_ENABLED=true
XRAY_CLOUD=true  # Set to false for Server/DC
XRAY_AUTO_REPORT_RESULTS=true

# Xray Cloud specific settings
XRAY_CLIENT_ID=your-client-id
XRAY_CLIENT_SECRET=your-client-secret
```

## Next Steps

1. **Environment-Specific Configuration**
   - Set up separate configurations for different environments

2. **CI/CD Integration**
   - Add scripts for CI/CD pipeline integration

3. **Expand Test Coverage**
   - Add more test types with Xray integration

4. **Reporting Enhancements**
   - Customize Allure reports with Jira/Xray links

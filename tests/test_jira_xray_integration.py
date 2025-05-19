"""
Example test file demonstrating Jira and Xray integration.

This file shows how to:
1. Mark tests with Xray test keys
2. Report test results to Xray
3. Create Jira issues from test results
"""

import pytest
import allure
import os
from datetime import datetime
from config.config import Config


@allure.feature("Jira Integration")
@allure.story("API Tests")
@pytest.mark.xray(test_key="TEST-1", summary="Test API endpoint")
def test_api_with_xray_integration(jira_helper, xray_helper, xray_test_info):
    """Test example with Xray integration for API testing."""
    # This is just a sample test that will pass
    assert True, "API test passed"


@allure.feature("Jira Integration")
@allure.story("UI Tests")
@pytest.mark.xray(test_key="TEST-2", summary="Test UI functionality")
def test_ui_with_xray_integration(_setup, jira_helper, xray_helper, xray_test_info):
    """Test example with Xray integration for UI testing."""
    # This demonstrates using the page object from _setup
    page = _setup
    page.goto("https://example.com")
    assert page.title() == "Example Domain", "Page title does not match"


@allure.feature("Jira Integration")
@allure.story("Failed Tests")
@pytest.mark.xray(test_key="TEST-3", summary="Test that will fail to demonstrate issue creation")
def test_failure_with_jira_issue_creation(jira_helper, xray_helper, xray_test_info):
    """Test example that fails and creates a Jira issue."""
    try:
        # This will intentionally fail
        assert False, "This test is designed to fail"
    except AssertionError as e:
        # Only create Jira issue if integration is enabled
        if jira_helper and Config.JIRA_ENABLED:
            issue = jira_helper.create_issue(
                summary=f"Test Failure: {xray_test_info['summary']}",
                description=f"The test {xray_test_info['test_key']} failed with error: {str(e)}",
                issue_type="Bug",
                priority="Medium",
                labels=["automated-test", "regression"]
            )
            
            # Add a comment with test details
            jira_helper.add_comment(
                issue_key=issue["key"],
                comment=f"Failure occurred at {datetime.now().isoformat()}. Test: {xray_test_info['test_key']}"
            )
            
            # Link the issue to the test in Xray
            if xray_helper and Config.XRAY_ENABLED:
                jira_helper.create_issue_link(
                    link_type="Tests",
                    inward_issue=issue["key"],
                    outward_issue=xray_test_info["test_key"],
                    comment="Bug identified by automated test"
                )
                
            pytest.fail(f"Test failed and created Jira issue: {issue['key']}")
        else:
            pytest.fail(str(e))


@pytest.mark.skipif(not Config.JIRA_ENABLED, reason="Jira integration not enabled")
def test_jira_connection(jira_helper):
    """Test that Jira connection is working."""
    assert jira_helper is not None, "Jira helper is None"
    
    # Test search functionality 
    jql = f"project = {Config.JIRA_PROJECT_KEY} ORDER BY created DESC"
    try:
        result = jira_helper.search_issues(jql, max_results=1)
        assert result is not None, "Search result is None"
        assert "issues" in result, "No issues property in search result"
        
        print(f"Successfully connected to Jira project {Config.JIRA_PROJECT_KEY}")
        if result["issues"]:
            print(f"Latest issue: {result['issues'][0]['key']}")
        else:
            print("No issues found in the project")
    except Exception as e:
        pytest.fail(f"Jira connection test failed: {str(e)}")


@pytest.mark.skipif(not Config.XRAY_ENABLED, reason="Xray integration not enabled")
def test_xray_connection(xray_helper):
    """Test that Xray connection is working."""
    assert xray_helper is not None, "Xray helper is None"
    
    execution_key = os.environ.get("XRAY_EXECUTION_KEY")
    if execution_key:
        try:
            # Try to get tests for the execution
            tests = xray_helper.get_tests_by_execution(execution_key)
            assert tests is not None, "Tests result is None"
            
            print(f"Successfully connected to Xray execution {execution_key}")
            print(f"Number of tests in execution: {len(tests)}")
        except Exception as e:
            pytest.fail(f"Xray connection test failed: {str(e)}")
    else:
        print("XRAY_EXECUTION_KEY not set, skipping execution tests check")
        pytest.skip("XRAY_EXECUTION_KEY not set")


def test_create_test_execution(jira_helper, xray_helper):
    """Test creating a new test execution in Xray."""
    if not Config.XRAY_ENABLED or not Config.JIRA_ENABLED:
        pytest.skip("Jira or Xray integration not enabled")
    
    try:
        # Create a new test execution
        execution = xray_helper.create_test_execution(
            summary=f"Automated Test Execution - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            description="This test execution was created by an automated test",
            test_keys=["TEST-1", "TEST-2", "TEST-3"]  # Replace with your actual test keys
        )
        
        assert execution is not None, "Execution result is None"
        
        # Set the execution key for other tests to use
        if "key" in execution:
            os.environ["XRAY_EXECUTION_KEY"] = execution["key"]
            print(f"Created test execution: {execution['key']}")
        else:
            print(f"Created test execution with response: {execution}")
    except Exception as e:
        pytest.fail(f"Failed to create test execution: {str(e)}")

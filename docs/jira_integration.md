# Jira Integration for Test Automation

This feature automatically creates Jira tickets when tests fail, streamlining the bug tracking process and ensuring that test failures are properly documented and tracked.

## Features

- **Automatic Ticket Creation**: Failed tests automatically create Jira tickets
- **Duplicate Detection**: Prevents creating duplicate tickets for the same test failure
- **Screenshot Attachment**: Automatically attaches screenshots of failed UI tests
- **AI Analysis Integration**: Includes AI-powered failure analysis if enabled
- **Flexible Configuration**: Configure priority, labels, components, and custom fields
- **Decorator Support**: Use decorators to customize Jira behavior per test
- **Class-level Configuration**: Apply Jira settings to entire test classes

## Setup

### 1. Configure Environment Variables

Add the following to your `.env` file:

```bash
# Enable Jira integration
JIRA_ENABLED=true

# Jira instance configuration
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=your-api-token  # Generate from Jira Account Settings

# Project configuration
JIRA_PROJECT_KEY=PROJ  # Your Jira project key
JIRA_ISSUE_TYPE=Bug    # Issue type for test failures

# Optional settings
JIRA_CREATE_DUPLICATES=false  # Set to true to create duplicate issues
```

### 2. Generate Jira API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a descriptive name (e.g., "Test Automation")
4. Copy the token and add it to your `.env` file

## Usage

### Basic Usage (Default Behavior)

By default, all failed tests will create Jira tickets when `JIRA_ENABLED=true`:

```python
def test_example(_setup):
    """This test will create a Jira ticket if it fails."""
    page = _setup
    page.goto("https://example.com")
    assert page.title() == "Expected Title"
```

### Using Decorators

#### Set Priority and Labels

```python
from utils.jira_decorator import jira_ticket

@jira_ticket(priority="High", labels=["regression", "critical"])
def test_critical_feature(_setup):
    """Creates a high-priority ticket with custom labels on failure."""
    # Test implementation
```

#### Skip Jira Ticket Creation

```python
from utils.jira_decorator import skip_jira_ticket

@skip_jira_ticket("Known flaky test")
def test_flaky_feature(_setup):
    """This test won't create Jira tickets even if it fails."""
    # Test implementation
```

#### Assign to Components

```python
@jira_ticket(
    priority="Medium",
    labels=["api", "integration"],
    components=["Backend", "API Gateway"]
)
def test_api_endpoint():
    """Assigns the ticket to specific Jira components."""
    # Test implementation
```

### Class-Level Configuration

Apply Jira settings to all tests in a class:

```python
from utils.jira_decorator import JiraTestMarker

@JiraTestMarker.mark(priority="Medium", labels=["ui-tests"])
class TestUserInterface:
    def test_login_page(self, _setup):
        # Inherits class-level Jira settings
        pass
    
    def test_dashboard(self, _setup):
        # Also inherits class-level settings
        pass
    
    @jira_ticket(priority="High")  # Override class priority
    def test_critical_ui_element(self, _setup):
        # Uses High priority instead of Medium
        pass
```

### Using pytest Markers

Alternative to decorators:

```python
import pytest

@pytest.mark.jira(priority="Low", labels=["experimental"])
def test_experimental_feature():
    """Uses pytest marker for Jira configuration."""
    pass

@pytest.mark.skip_jira
def test_skip_jira_marker():
    """Skips Jira ticket creation using pytest marker."""
    pass
```

### Custom Fields

Set custom Jira fields (field IDs depend on your Jira configuration):

```python
@jira_ticket(
    custom_fields={
        "customfield_10001": "Sprint 23",      # Sprint field
        "customfield_10002": "2024.1",         # Version field
        "customfield_10003": "CustomerA"       # Customer field
    }
)
def test_with_custom_fields():
    """Sets custom Jira fields in the created ticket."""
    pass
```

## Jira Ticket Format

Created tickets include:

### Summary
Just the test method name (e.g., `test_login_functionality`, `test_api_endpoint`)

### Description
- **Test Details**: Name, timestamp, file location
- **Error Message**: Full error message and stack trace
- **Test Code**: Source code of the failed test
- **AI Analysis** (if enabled):
  - Root cause analysis
  - Suggested fixes
  - Additional context
- **Attachments**: Screenshots (for UI tests)

### Fields
- **Issue Type**: Configured via `JIRA_ISSUE_TYPE`
- **Priority**: Default "Medium" or as specified
- **Labels**: Always includes "test-failure", "automated-test", plus custom labels
- **Components**: As specified in decorator/marker

## Integration with AI Analysis

When both Jira and AI analysis are enabled:

1. AI analyzes the test failure
2. Analysis results are included in the Jira ticket
3. Priority may be adjusted based on AI severity assessment
4. Suggested fixes are added to the ticket description

## Best Practices

### 1. Use Descriptive Labels

```python
@jira_ticket(labels=["checkout-flow", "payment", "critical-path"])
def test_payment_processing():
    pass
```

### 2. Set Appropriate Priorities

- **Highest/High**: Critical business flows, security issues
- **Medium**: Standard functionality
- **Low**: Edge cases, cosmetic issues

### 3. Organize with Components

Map tests to Jira components for better organization:

```python
# API tests
@jira_ticket(components=["API", "Backend"])

# UI tests  
@jira_ticket(components=["Frontend", "UI"])

# Database tests
@jira_ticket(components=["Database", "Infrastructure"])
```

### 4. Skip Known Issues

```python
@skip_jira_ticket("Waiting for API fix in PROJ-123")
def test_known_api_issue():
    pass
```

### 5. Use Class Markers for Test Suites

```python
@JiraTestMarker.mark(
    labels=["nightly-regression"],
    components=["E2E-Tests"]
)
class TestNightlyRegression:
    # All tests inherit these settings
```

## Troubleshooting

### Issue: Authentication Failed

**Error**: `Failed to create Jira issue: 401 Client Error`

**Solution**: 
- Verify `JIRA_USERNAME` is your email address
- Check `JIRA_API_TOKEN` is valid
- Ensure the user has permissions in the project

### Issue: Project Not Found

**Error**: `Project 'PROJ' does not exist`

**Solution**:
- Verify `JIRA_PROJECT_KEY` matches your Jira project
- Check user has access to the project

### Issue: Invalid Issue Type

**Error**: `Issue type 'Bug' is not valid`

**Solution**:
- Check available issue types in your project settings
- Update `JIRA_ISSUE_TYPE` to match

### Issue: Custom Field Errors

**Error**: `Field 'customfield_10001' cannot be set`

**Solution**:
- Verify custom field IDs in Jira settings
- Ensure fields are available for the issue type
- Check field permissions

## Command Line Options

Run tests with Jira integration:

```bash
# Run all tests (Jira tickets created for failures)
pytest -v

# Run specific test file
pytest tests/test_jira_integration_example.py -v

# Disable Jira temporarily via environment
JIRA_ENABLED=false pytest -v

# Run with specific markers
pytest -m "not skip_jira" -v
```

## Example Test Run Output

```
$ pytest tests/test_example.py -v
...
FAILED tests/test_example.py::test_critical_feature - AssertionError
Taking screenshot for failed test: tests/test_example.py::test_critical_feature
Screenshot saved to: reports/screenshots/test_example_py_test_critical_feature.png
Created Jira issue: PROJ-1234 - https://your-domain.atlassian.net/browse/PROJ-1234
```

## Viewing Results

1. **Console Output**: Shows created ticket keys and URLs
2. **Allure Report**: Includes Jira ticket information as attachments
3. **Jira Dashboard**: View all created tickets with full details

## Advanced Configuration

### Conditional Ticket Creation

Create tickets only in specific environments:

```python
import os

def test_production_only():
    if os.getenv("ENVIRONMENT") == "production":
        test_production_only.jira_create_on_failure = True
        test_production_only.jira_priority = "Highest"
```

### Dynamic Labels

Add labels based on test context:

```python
@jira_ticket(labels=[f"sprint-{os.getenv('SPRINT_NUMBER', 'unknown')}"])
def test_sprint_feature():
    pass
```

### Integration with CI/CD

```yaml
# Example GitHub Actions
- name: Run Tests with Jira Integration
  env:
    JIRA_ENABLED: true
    JIRA_BASE_URL: ${{ secrets.JIRA_BASE_URL }}
    JIRA_USERNAME: ${{ secrets.JIRA_USERNAME }}
    JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
    JIRA_PROJECT_KEY: ${{ secrets.JIRA_PROJECT_KEY }}
  run: pytest -v
```
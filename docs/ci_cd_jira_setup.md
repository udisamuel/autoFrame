# Setting Up Jira Integration in CI/CD

This guide explains how to enable Jira ticket creation for failed tests in your CI/CD pipeline.

## GitHub Actions Setup

### 1. Add GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions, and add these secrets:

| Secret Name | Value | Example |
|------------|-------|---------|
| `JIRA_BASE_URL` | Your Jira instance URL | `https://your-domain.atlassian.net` |
| `JIRA_USERNAME` | Your Jira email | `your-email@example.com` |
| `JIRA_API_TOKEN` | Your Jira API token | `ATATT3xFfGF0...` |
| `JIRA_PROJECT_KEY` | Your Jira project key | `PROJ` |

### 2. Update Your Workflow

Add environment variables to your GitHub Actions workflow:

```yaml
- name: Run tests
  env:
    # Enable Jira integration
    JIRA_ENABLED: true
    
    # Jira credentials from GitHub Secrets
    JIRA_BASE_URL: ${{ secrets.JIRA_BASE_URL }}
    JIRA_USERNAME: ${{ secrets.JIRA_USERNAME }}
    JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
    JIRA_PROJECT_KEY: ${{ secrets.JIRA_PROJECT_KEY }}
    
    # Optional settings
    JIRA_ISSUE_TYPE: Bug
    JIRA_CREATE_DUPLICATES: false
  run: |
    pytest -v
```

## Environment Variables for CI/CD

### Required Variables

- `JIRA_ENABLED=true` - Must be set to enable Jira integration
- `JIRA_BASE_URL` - Your Jira instance URL
- `JIRA_USERNAME` - Email associated with your Jira account
- `JIRA_API_TOKEN` - API token (not password)
- `JIRA_PROJECT_KEY` - Project where tickets will be created

### Optional Variables

- `JIRA_ISSUE_TYPE=Bug` - Type of issue to create (default: Bug)
- `JIRA_CREATE_DUPLICATES=false` - Whether to create duplicate tickets (default: false)

## Conditional Ticket Creation for CI/CD

You can make tests create Jira tickets only in CI/CD:

```python
def test_critical_feature():
    """Only creates Jira ticket when running in CI/CD."""
    import os
    
    if os.getenv("CI") == "true":  # GitHub Actions sets CI=true
        test_critical_feature.jira_create_on_failure = True
        test_critical_feature.jira_priority = "High"
        test_critical_feature.jira_labels = ["ci-failure"]
    
    # Your test code here
    assert some_critical_check()
```

## Best Practices for CI/CD

### 1. Avoid Creating Too Many Tickets

```yaml
env:
  JIRA_CREATE_DUPLICATES: false  # Prevent duplicate tickets
```

### 2. Filter Which Tests Create Tickets

Only create tickets for critical tests:

```python
# Mark only critical tests for Jira
@jira_ticket(labels=["critical", "ci"])
def test_critical_payment_flow():
    pass

# Skip Jira for flaky tests
@skip_jira_ticket("Known flaky in CI")
def test_flaky_ui_interaction():
    pass
```

### 3. Add CI-Specific Labels

```python
@jira_ticket(labels=["ci-failure", f"build-{os.getenv('GITHUB_RUN_NUMBER', 'unknown')}"])
def test_in_ci():
    pass
```

### 4. Use Different Projects for Different Environments

```yaml
env:
  JIRA_PROJECT_KEY: ${{ github.ref == 'refs/heads/main' && 'PROD' || 'DEV' }}
```

## Troubleshooting

### No Tickets Being Created

1. Check if `JIRA_ENABLED=true` is set
2. Verify all required secrets are configured
3. Check test output for error messages
4. Ensure tests are actually failing (not skipped)

### Authentication Errors

```
Error: Failed to create Jira issue: 401 Client Error
```

- Verify `JIRA_USERNAME` is your email
- Check `JIRA_API_TOKEN` is valid (not your password)
- Ensure the user has permissions in the project

### Project Not Found

```
Error: Project 'PROJ' does not exist
```

- Verify `JIRA_PROJECT_KEY` matches your Jira project
- Check user has access to the project

## Example Output

When properly configured, failed tests in CI/CD will show:

```
tests/test_payment.py::test_payment_processing FAILED
Taking screenshot for failed test: tests/test_payment.py::test_payment_processing
Screenshot saved to: reports/screenshots/test_payment_processing.png

Jira Integration: Processing failed test tests/test_payment.py::test_payment_processing
Created Jira issue: PROJ-123 - https://your-domain.atlassian.net/browse/PROJ-123
```

## Jenkins Setup

For Jenkins, set environment variables in your pipeline:

```groovy
pipeline {
    environment {
        JIRA_ENABLED = 'true'
        JIRA_BASE_URL = credentials('jira-base-url')
        JIRA_USERNAME = credentials('jira-username')
        JIRA_API_TOKEN = credentials('jira-api-token')
        JIRA_PROJECT_KEY = 'PROJ'
    }
    stages {
        stage('Test') {
            steps {
                sh 'pytest -v'
            }
        }
    }
}
```

## GitLab CI Setup

For GitLab CI, add to `.gitlab-ci.yml`:

```yaml
test:
  variables:
    JIRA_ENABLED: "true"
    JIRA_BASE_URL: $JIRA_BASE_URL
    JIRA_USERNAME: $JIRA_USERNAME
    JIRA_API_TOKEN: $JIRA_API_TOKEN
    JIRA_PROJECT_KEY: $JIRA_PROJECT_KEY
  script:
    - pytest -v
```

## Disabling for Specific Runs

To temporarily disable Jira integration:

```bash
# In GitHub Actions
JIRA_ENABLED=false pytest -v

# Or exclude Jira tests
pytest -v -k "not jira"
```
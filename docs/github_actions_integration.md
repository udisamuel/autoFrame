# GitHub Actions Integration with Jira and Xray

This document explains how to set up and use the GitHub Actions workflow for Jira and Xray integration.

## Overview

The GitHub Actions workflow automatically:
1. Sets up the testing environment
2. Creates a new Xray Test Execution
3. Runs the tests with Jira and Xray integration
4. Reports test results back to Xray
5. Uploads test reports as artifacts

## Required Secrets

The following secrets must be set in your GitHub repository settings:

| Secret Name | Description |
|-------------|-------------|
| `JIRA_API_TOKEN` | API token for Jira authentication |
| `JIRA_PROJECT_KEY` | The project key in Jira (e.g., TEST) |
| `JIRA_URL` | The base URL of your Jira instance (e.g., https://your-domain.atlassian.net) |
| `JIRA_USERNAME` | Your Jira username or email |
| `XRAY_CLIENT_ID` | Client ID for Xray Cloud API |
| `XRAY_CLIENT_SECRET` | Client Secret for Xray Cloud API |
| `XRAY_CLOUD_ENABLED` | Set to "true" for Xray Cloud, "false" for Xray Server/DC |

To add these secrets:
1. Go to your repository on GitHub
2. Click on "Settings" > "Secrets and variables" > "Actions"
3. Click "New repository secret" and add each secret

## Optional Variables

You can also set these as repository variables for additional configuration:

| Variable Name | Description |
|---------------|-------------|
| `BASE_URL` | Base URL for your application under test |

## Workflow Triggers

The workflow is triggered by:
- Push to main or master branch
- Pull requests to main or master branch
- Manual trigger (workflow_dispatch)

When triggered manually, you can specify a test pattern to run specific tests.

## Using the Workflow

### Automatic Runs

The workflow will run automatically on push to the main branch or on pull requests.

### Manual Runs

To run the workflow manually:
1. Go to your repository on GitHub
2. Click on "Actions"
3. Select "Test with Jira/Xray Integration" workflow
4. Click "Run workflow"
5. Optionally enter a test pattern (e.g., `tests/test_api_*.py`) to run specific tests
6. Click "Run workflow"

## Test Reports

After each workflow run, test reports are available as artifacts:
1. Go to the workflow run
2. Scroll down to "Artifacts"
3. Download the "test-reports" artifact

## Customizing the Workflow

You can customize the workflow by editing the `.github/workflows/jira_xray_integration.yml` file:

### Adding More Environment Variables

Modify the "Create .env file" step to add more variables:

```yaml
- name: Create .env file
  run: |
    # ... existing variables ...
    
    # Add your custom variables
    echo "MY_CUSTOM_VAR=${{ secrets.MY_CUSTOM_VAR }}" >> .env
```

### Running Different Test Suites

Modify the "Run tests" step to run different test suites:

```yaml
- name: Run tests
  run: |
    # Run API tests only
    python -m pytest tests/test_api_*.py -v --junitxml=reports/junit-results.xml
```

### Adding Test Labels or Metadata

You can add additional information to the test execution in the "Create Test Execution in Xray" step:

```python
execution = xray_helper.create_test_execution(
    summary=f'Automated Test Execution - GitHub Actions - {os.environ.get("GITHUB_RUN_ID", "manual")}',
    description=f'Automated test execution created by GitHub Actions workflow run #{os.environ.get("GITHUB_RUN_NUMBER", "manual")} for {os.environ.get("GITHUB_REPOSITORY", "unknown repo")}',
    test_keys=test_keys,
    # Add custom fields
    custom_fields={
        'customfield_10100': {'value': 'CI/CD'}
    }
)
```

## Troubleshooting

### Workflow Failed to Create Test Execution

If the "Create Test Execution in Xray" step fails:
1. Check that all required secrets are set correctly
2. Verify that you have permissions to create Test Executions in your Jira project
3. Check that your test files are properly marked with Xray test keys

### Tests Run But Results Not Reported to Xray

If tests run but results are not reported to Xray:
1. Check the workflow logs for error messages
2. Verify that the Xray test keys in your test files match actual Test issues in Jira
3. Confirm that your Xray API credentials have the necessary permissions

### Authentication Failures

If you see authentication failures:
1. Verify that your Jira and Xray credentials are correct
2. Check that your API token has not expired
3. Ensure that your user account has the necessary permissions in Jira and Xray

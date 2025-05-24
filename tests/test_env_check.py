"""Test to verify environment configuration in CI/CD."""
import os
import pytest


def test_environment_variables():
    """Check if Jira environment variables are properly set."""
    print("\n=== Environment Check ===")
    print(f"CI: {os.getenv('CI', 'not set')}")
    print(f"GITHUB_ACTIONS: {os.getenv('GITHUB_ACTIONS', 'not set')}")
    print(f"JIRA_ENABLED: {os.getenv('JIRA_ENABLED', 'not set')}")
    print(f"JIRA_BASE_URL: {os.getenv('JIRA_BASE_URL', 'not set')}")
    print(f"JIRA_PROJECT_KEY: {os.getenv('JIRA_PROJECT_KEY', 'not set')}")
    print(f"JIRA_USERNAME: {os.getenv('JIRA_USERNAME', 'not set')}")
    print(f"JIRA_API_TOKEN: {'***' if os.getenv('JIRA_API_TOKEN') else 'not set'}")
    
    # Also check Config values
    from config.config import Config
    print("\n=== Config Values ===")
    print(f"Config.JIRA_ENABLED: {Config.JIRA_ENABLED}")
    print(f"Config.JIRA_BASE_URL: {Config.JIRA_BASE_URL}")
    print(f"Config.JIRA_PROJECT_KEY: {Config.JIRA_PROJECT_KEY}")
    
    # This test always passes - it's just for debugging
    assert True


@pytest.mark.skipif(
    os.getenv('JIRA_ENABLED', 'false').lower() != 'true',
    reason="Jira integration is disabled"
)
def test_jira_enabled_verification():
    """This test runs only when Jira is enabled."""
    from config.config import Config
    assert Config.JIRA_ENABLED, "JIRA_ENABLED should be True"
    assert Config.JIRA_BASE_URL, "JIRA_BASE_URL should be set"
    assert Config.JIRA_USERNAME, "JIRA_USERNAME should be set"
    assert Config.JIRA_API_TOKEN, "JIRA_API_TOKEN should be set"
    assert Config.JIRA_PROJECT_KEY, "JIRA_PROJECT_KEY should be set"
    print("✅ All Jira configuration verified!")
"""Simple test to verify Jira integration setup."""
import pytest
from utils.jira_decorator import jira_ticket

def test_simple_pass():
    """This test should pass - no Jira ticket created."""
    assert True

@jira_ticket(priority="Low", labels=["test-setup"])
def test_simple_fail():
    """This test will fail and create a Jira ticket if JIRA_ENABLED=true."""
    assert False, "This is a test failure to verify Jira integration"

def test_verify_configuration():
    """Verify Jira configuration is loaded correctly."""
    from config.config import Config
    
    # Just verify the configuration is accessible
    assert hasattr(Config, 'JIRA_ENABLED')
    assert hasattr(Config, 'JIRA_BASE_URL')
    assert hasattr(Config, 'JIRA_PROJECT_KEY')
    
    print(f"\nJira Configuration Status:")
    print(f"  JIRA_ENABLED: {Config.JIRA_ENABLED}")
    print(f"  JIRA_PROJECT_KEY: {Config.JIRA_PROJECT_KEY}")
    print(f"  Ready for integration: {'Yes' if Config.JIRA_ENABLED else 'No (enable JIRA_ENABLED in .env)'}")
    
    assert True  # This test always passes
import pytest
from utils.jira_decorator import jira_ticket, skip_jira_ticket, JiraTestMarker


class TestJiraIntegrationExamples:
    """Examples of how to use Jira integration with tests."""
    
    @jira_ticket(priority="High", labels=["regression", "critical"])
    def test_with_jira_decorator_high_priority(self, _setup):
        """This test will create a high priority Jira ticket if it fails."""
        page = _setup
        page.goto("https://google.com")
        
        # This assertion will fail, creating a Jira ticket
        assert page.title() == "Wrong Title", "Intentional failure for Jira ticket creation"
    
    @jira_ticket(labels=["ui-test", "search-functionality"])
    def test_with_custom_labels(self, _setup):
        """This test will create a Jira ticket with custom labels if it fails."""
        page = _setup
        page.goto("https://google.com")
        
        # Perform a search
        search_box = page.locator('input[name="q"]')
        search_box.fill("Playwright testing")
        search_box.press("Enter")
        
        # This might fail depending on the page load
        assert page.locator("h3").count() > 0, "No search results found"
    
    @skip_jira_ticket("This is a known flaky test")
    def test_skip_jira_ticket(self, _setup):
        """This test will NOT create a Jira ticket even if it fails."""
        page = _setup
        page.goto("https://google.com")
        
        # Even if this fails, no Jira ticket will be created
        assert False, "This failure won't create a Jira ticket"
    
    def test_default_jira_behavior(self, _setup):
        """This test will create a Jira ticket with default settings if it fails."""
        page = _setup
        page.goto("https://google.com")
        
        # Default behavior - creates ticket on failure
        assert page.locator("non-existent-element").is_visible(), "Element not found"
    
    @pytest.mark.jira(priority="Low", labels=["experimental"])
    def test_with_pytest_marker(self, _setup):
        """This test uses pytest.mark.jira for Jira configuration."""
        page = _setup
        page.goto("https://google.com")
        
        # Uses pytest marker instead of decorator
        assert page.title() == "Not Google", "Title mismatch"
    
    @pytest.mark.skip_jira
    def test_skip_with_pytest_marker(self, _setup):
        """This test uses pytest.mark.skip_jira to skip ticket creation."""
        page = _setup
        page.goto("https://google.com")
        
        # Won't create Jira ticket due to skip_jira marker
        assert False, "Skipped from Jira"


@JiraTestMarker.mark(priority="Medium", labels=["api-tests", "integration"])
class TestJiraClassMarker:
    """All tests in this class will have the same Jira settings."""
    
    def test_class_marked_test1(self):
        """This test inherits Jira settings from the class."""
        # This will create a Medium priority ticket with api-tests and integration labels
        assert 1 == 2, "Math is broken"
    
    def test_class_marked_test2(self):
        """Another test with class-level Jira settings."""
        # Also inherits the class settings
        assert "hello" == "world", "String comparison failed"
    
    @jira_ticket(priority="High")  # This overrides the class priority
    def test_override_class_settings(self):
        """This test overrides the class priority setting."""
        # Will create a High priority ticket instead of Medium
        assert [] is not None, "List is None"


class TestJiraIntegrationWithComponents:
    """Examples using Jira components."""
    
    @jira_ticket(
        priority="High",
        labels=["backend", "database"],
        components=["Backend", "Database Layer"]
    )
    def test_with_components(self):
        """This test assigns the ticket to specific Jira components."""
        # Simulating a database connection failure
        raise ConnectionError("Failed to connect to database")
    
    @jira_ticket(
        custom_fields={
            "customfield_10001": "Sprint 23",  # Example: Sprint field
            "customfield_10002": "2024.1"       # Example: Version field
        }
    )
    def test_with_custom_fields(self):
        """This test sets custom Jira fields."""
        # Custom fields depend on your Jira configuration
        assert False, "Test with custom Jira fields"


# Example of conditional Jira ticket creation
def test_conditional_jira_creation():
    """Example of how to conditionally create Jira tickets."""
    import os
    
    # Only create Jira tickets in CI/CD environment
    if os.getenv("CI", "false").lower() == "true":
        test_func = test_conditional_jira_creation
        test_func.jira_create_on_failure = True
        test_func.jira_priority = "High"
        test_func.jira_labels = ["ci-failure"]
    
    assert False, "This might create a Jira ticket depending on environment"
import pytest
from functools import wraps
from typing import Optional, List, Dict, Any


def jira_ticket(
    create_on_failure: bool = True,
    priority: Optional[str] = None,
    labels: Optional[List[str]] = None,
    components: Optional[List[str]] = None,
    custom_fields: Optional[Dict[str, Any]] = None
):
    """
    Decorator to mark tests for Jira ticket creation on failure.
    
    Args:
        create_on_failure: Whether to create a Jira ticket when the test fails
        priority: Override priority for the Jira ticket (e.g., "High", "Medium", "Low")
        labels: Additional labels to add to the Jira ticket
        components: Components to assign the ticket to
        custom_fields: Custom field values for the Jira ticket
        
    Usage:
        @jira_ticket(priority="High", labels=["regression", "critical"])
        def test_critical_feature():
            assert False, "This test should create a high priority Jira ticket"
    """
    def decorator(func):
        # Store Jira metadata as test attributes
        func.jira_create_on_failure = create_on_failure
        func.jira_priority = priority
        func.jira_labels = labels or []
        func.jira_components = components or []
        func.jira_custom_fields = custom_fields or {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def skip_jira_ticket(reason: str = "Jira ticket creation skipped"):
    """
    Decorator to explicitly skip Jira ticket creation for a test.
    
    Args:
        reason: Reason for skipping Jira ticket creation
        
    Usage:
        @skip_jira_ticket("Known flaky test")
        def test_flaky_feature():
            # This test won't create Jira tickets even if it fails
            pass
    """
    def decorator(func):
        func.jira_create_on_failure = False
        func.jira_skip_reason = reason
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


class JiraTestMarker:
    """
    Class-based marker for applying Jira settings to all tests in a class.
    
    Usage:
        @JiraTestMarker.mark(priority="High", labels=["api-tests"])
        class TestAPIEndpoints:
            def test_endpoint1(self):
                pass
    """
    
    @staticmethod
    def mark(
        create_on_failure: bool = True,
        priority: Optional[str] = None,
        labels: Optional[List[str]] = None,
        components: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ):
        """Mark all tests in a class with Jira settings."""
        def class_decorator(cls):
            # Apply settings to the class
            cls._jira_create_on_failure = create_on_failure
            cls._jira_priority = priority
            cls._jira_labels = labels or []
            cls._jira_components = components or []
            cls._jira_custom_fields = custom_fields or {}
            
            # Apply settings to all test methods
            for attr_name in dir(cls):
                if attr_name.startswith('test_'):
                    attr = getattr(cls, attr_name)
                    if callable(attr):
                        # Only set if not already set on the method
                        if not hasattr(attr, 'jira_create_on_failure'):
                            attr.jira_create_on_failure = create_on_failure
                        if not hasattr(attr, 'jira_priority') and priority:
                            attr.jira_priority = priority
                        if not hasattr(attr, 'jira_labels'):
                            attr.jira_labels = labels or []
                        if not hasattr(attr, 'jira_components'):
                            attr.jira_components = components or []
                        if not hasattr(attr, 'jira_custom_fields'):
                            attr.jira_custom_fields = custom_fields or {}
            
            return cls
        
        return class_decorator


# Pytest markers for use with pytest.mark
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "jira: Mark test for Jira ticket creation on failure"
    )
    config.addinivalue_line(
        "markers", 
        "skip_jira: Skip Jira ticket creation for this test"
    )
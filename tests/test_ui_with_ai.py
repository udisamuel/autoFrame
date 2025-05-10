import pytest
import allure
import os
from pages.base_page import BasePage

class LoginPage(BasePage):
    """Sample login page class for demonstration."""
    
    # Locators
    USERNAME_INPUT = "input#username"
    PASSWORD_INPUT = "input#password"
    LOGIN_BUTTON = "button[type='submit']"
    ERROR_MESSAGE = ".error-message"
    
    def navigate(self):
        """Navigate to the login page."""
        self.navigate_to("/login")
        
    def login(self, username, password):
        """Perform login with the given credentials."""
        self.fill(self.USERNAME_INPUT, username)
        self.fill(self.PASSWORD_INPUT, password)
        self.click(self.LOGIN_BUTTON)
        
    def get_error_message(self):
        """Get the error message text if present."""
        if self.is_element_visible(self.ERROR_MESSAGE):
            return self.get_text(self.ERROR_MESSAGE)
        return None

@allure.feature("UI Testing with AI")
@pytest.mark.ui
class TestLoginWithAI:
    """
    Sample UI test class demonstrating AI integration.
    """
    
    @allure.story("AI-Generated Test Data")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description("Test login with AI-generated credentials")
    def test_login_with_ai_data(self, _setup, ai_data_generator):
        """Test login functionality with AI-generated user data."""
        # Skip test if AI data generator is not available
        if ai_data_generator is None:
            pytest.skip("AI data generation is not enabled")
            
        # Initialize the login page
        login_page = LoginPage(_setup)
        
        # Navigate to login page
        login_page.navigate()
        
        # Generate login credentials using AI
        user_data = ai_data_generator.generate_user_profile()
        
        # Extract username and password fields
        # For demonstration, we'll use email as username and a field from the data as password
        username = user_data.get("email", "test@example.com")
        password = user_data.get("phone", "password123").replace("-", "")
        
        # Log the generated credentials for debugging
        allure.attach(
            f"Username: {username}\nPassword: {password}",
            name="AI-Generated Credentials",
            attachment_type=allure.attachment_type.TEXT
        )
        
        # Perform login - note: this will likely fail in a real environment
        # as the AI-generated credentials are not actually registered
        login_page.login(username, password)
        
        # Take a screenshot after login attempt
        screenshot_path = login_page.take_screenshot("login_attempt")
        
        # Check for error message (expected in this demo since credentials are generated)
        error_message = login_page.get_error_message()
        if error_message:
            allure.attach(
                f"Error message: {error_message}",
                name="Login Error",
                attachment_type=allure.attachment_type.TEXT
            )
            
        # Note: In a real test, you would make assertions here
        # For this demo, we're just demonstrating the AI data generation
    
    @allure.story("AI Test Analysis")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test with intentional failure for AI analysis demonstration")
    def test_login_for_ai_analysis(self, _setup, ai_test_analyzer):
        """Test with intentional failure to demonstrate AI test analysis."""
        # Skip test if AI test analyzer is not available
        if ai_test_analyzer is None:
            pytest.skip("AI test analysis is not enabled")
            
        # Initialize the login page
        login_page = LoginPage(_setup)
        
        # Navigate to login page
        login_page.navigate()
        
        # Perform login with invalid credentials
        login_page.login("invalid@example.com", "wrongpassword")
        
        # Take a screenshot after login attempt
        screenshot_path = login_page.take_screenshot("failed_login")
        
        # Intentional assertion failure for demonstration
        # The AI test analyzer will analyze this failure via the pytest hook
        assert False, "Intentional failure for AI analysis demonstration"

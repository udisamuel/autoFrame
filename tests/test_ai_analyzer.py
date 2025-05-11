from pages.main_page.main_page import MainPage
import allure
import pytest
import inspect
import json
import os
from utils.ai_test_analyzer import AITestAnalyzer

@allure.feature("Test AI Analyzer")
@pytest.mark.AIAnalyzer
class TestAIAnalyzer:

    @allure.story("Sample AI Analyzer Test - Simulated Failure Analysis")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test to demonstrate AI analysis without failing the test")
    def test_automatic_analyzer(self, _setup, ai_test_analyzer):
        """
        This test demonstrates AI analysis with a simulated failure.
        
        Instead of intentionally failing the test, we:
        1. Simulate an error
        2. Perform the same analysis that would happen on failure
        3. Report the analysis in the test report
        """
        # Skip test if AI analyzer is not enabled
        if not ai_test_analyzer:
            pytest.skip("AI Test Analyzer is not enabled")
            
        try:
            # Initialize Main Page
            mp = MainPage(_setup)

            # Navigate to the home page
            mp.navigate_to_home()

            # Take a screenshot
            mp.take_screenshot("home_page")
            
            # Create a simulated error for analysis
            simulated_error = "AssertionError: Simulated failure for AI analysis demonstration. Element not found: #login-button"
            test_code = inspect.getsource(TestAIAnalyzer.test_automatic_analyzer)
            
            # Get screenshot path
            screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "screenshots")
            test_name = "tests_test_ai_analyzer.py_TestAIAnalyzer_test_automatic_analyzer"
            screenshot_path = os.path.join(screenshots_dir, f"{test_name}.png")
            
            # Simulate the analysis that would normally happen on a test failure
            analysis = ai_test_analyzer.analyze_test_failure(
                test_name=f"{__name__}.TestAIAnalyzer.test_automatic_analyzer",
                error_message=simulated_error,
                test_code=test_code,
                screenshot_path=screenshot_path
            )
            
            # Add the analysis to the Allure report
            allure.attach(
                json.dumps(analysis, indent=2),
                name="AI Test Failure Analysis (Simulated)",
                attachment_type=allure.attachment_type.JSON
            )

            # Add a test step to show this is working as expected
            with allure.step("Verify AI analysis was performed"):
                assert "root_cause" in analysis, "Expected root cause in analysis"
                assert "suggested_fixes" in analysis, "Expected suggested fixes in analysis"
            
        except Exception as e:
            error_message = f"Error in test_automatic_analyzer simulation: {str(e)}"
            print(error_message)
            allure.attach(
                error_message,
                name="Test Error",
                attachment_type=allure.attachment_type.TEXT
            )
            raise
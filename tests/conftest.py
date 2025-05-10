import pytest
import sys
import os
import allure
import importlib.metadata
import inspect
import json
from datetime import datetime
from playwright.sync_api import Playwright

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from config.config import Config

# Allure environment information
@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    allure_dir = os.path.join(project_root, "reports", "allure-results")
    if not os.path.exists(allure_dir):
        os.makedirs(allure_dir)
        
    env_file = os.path.join(allure_dir, "environment.properties")
    with open(env_file, "w") as f:
        f.write(f"Python.Version={sys.version.split()[0]}\n")
        f.write(f"Playwright.Version={importlib.metadata.version('playwright')}\n")
        f.write(f"OS={sys.platform}\n")
        f.write(f"Timestamp={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"AI.Enabled={Config.AI_FEATURES_ENABLED}\n")

@pytest.fixture(scope="function")
def _setup(playwright: Playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    yield page
    
    # --------------------- Tear down ---------------------
    browser.close()

# AI-related fixtures
@pytest.fixture(scope="session")
def ai_data_generator():
    """Fixture to provide an instance of the AI data generator."""
    if Config.AI_FEATURES_ENABLED and Config.AI_DATA_GENERATION_ENABLED:
        from utils.ai_data_generator import AIDataGenerator
        return AIDataGenerator()
    return None

@pytest.fixture(scope="session")
def ai_test_analyzer():
    """Fixture to provide an instance of the AI test analyzer."""
    if Config.AI_FEATURES_ENABLED and Config.AI_TEST_ANALYSIS_ENABLED:
        from utils.ai_test_analyzer import AITestAnalyzer
        return AITestAnalyzer()
    return None

@pytest.fixture(scope="session")
def ai_test_generator():
    """Fixture to provide an instance of the AI test generator."""
    if Config.AI_FEATURES_ENABLED and Config.AI_TEST_GENERATION_ENABLED:
        from utils.ai_test_generator import AITestGenerator
        return AITestGenerator()
    return None

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    
    # We need to capture screenshots for failed tests
    if report.when == "call" and report.failed:
        try:
            # Get the page object from the _setup fixture
            page = item.funcargs.get("_setup", None)
            if page:
                # Debugging information
                print(f"Taking screenshot for failed test: {item.nodeid}")
                
                # Take a full-page screenshot
                screenshot_bytes = page.screenshot(full_page=True)
                
                # Save to file for debugging
                screenshots_dir = os.path.join(project_root, "reports", "screenshots")
                os.makedirs(screenshots_dir, exist_ok=True)
                test_name = item.nodeid.replace("::", "_").replace("/", "_")
                screenshot_path = os.path.join(screenshots_dir, f"{test_name}.png")
                
                with open(screenshot_path, "wb") as f:
                    f.write(screenshot_bytes)
                print(f"Screenshot saved to: {screenshot_path}")
                
                # Attach to Allure report
                allure.attach(
                    screenshot_bytes,
                    name=f"screenshot_on_failure",
                    attachment_type=allure.attachment_type.PNG
                )
                
                # AI Analysis of failure (if enabled)
                ai_test_analyzer = item.funcargs.get("ai_test_analyzer", None)
                if ai_test_analyzer and Config.AI_TEST_ANALYSIS_ENABLED:
                    try:
                        # Get test information
                        test_name = item.nodeid
                        error_message = str(call.excinfo.value)
                        test_code = inspect.getsource(item.function)
                        
                        # Try to get response data for API tests
                        response_data = None
                        if hasattr(call.excinfo.value, "response"):
                            try:
                                response_data = call.excinfo.value.response.json()
                            except:
                                response_data = call.excinfo.value.response.text
                        
                        # Analyze the failure
                        analysis = ai_test_analyzer.analyze_test_failure(
                            test_name,
                            error_message,
                            test_code,
                            screenshot_path,
                            response_data
                        )
                        
                        # Add the analysis to the Allure report
                        allure.attach(
                            json.dumps(analysis, indent=2),
                            name="AI Test Failure Analysis",
                            attachment_type=allure.attachment_type.JSON
                        )
                        
                        print(f"\nAI Analysis of test failure: {test_name}")
                        print(f"Likely root cause: {analysis.get('root_cause', 'Unknown')}")
                        print("Suggested fixes:")
                        for fix in analysis.get('suggested_fixes', []):
                            print(f"- {fix}")
                        
                    except Exception as e:
                        print(f"Error in AI test analysis: {str(e)}")
        except Exception as e:
            print(f"Error taking screenshot: {str(e)}")
            allure.attach(
                f"Failed to take screenshot: {str(e)}",
                name="screenshot_error",
                attachment_type=allure.attachment_type.TEXT
            )

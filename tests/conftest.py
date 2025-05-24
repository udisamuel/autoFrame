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
from utils.jira_helper import JiraHelper

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

def _create_jira_ticket_for_failure(item, call, screenshot_path=None, ai_analysis=None):
    """Helper function to create Jira ticket for test failure."""
    from utils.jira_helper import JiraHelper
    
    try:
        # Check if test is marked for Jira ticket creation
        test_func = item.function
        create_jira_ticket = getattr(test_func, 'jira_create_on_failure', True)
        
        # Check for skip marker
        if hasattr(test_func, 'jira_skip_reason'):
            print(f"Skipping Jira ticket creation: {test_func.jira_skip_reason}")
            create_jira_ticket = False
        
        # Check for pytest.mark.skip_jira
        if item.get_closest_marker('skip_jira'):
            print("Skipping Jira ticket creation due to skip_jira marker")
            create_jira_ticket = False
        
        if create_jira_ticket:
            jira_helper = JiraHelper()
            
            # Check for duplicate issues first
            if not Config.JIRA_CREATE_DUPLICATES:
                existing_issue = jira_helper.check_duplicate_issue(item.nodeid)
                if existing_issue:
                    print(f"Jira issue already exists for this test: {existing_issue}")
                    allure.attach(
                        f"Existing Jira issue: {existing_issue}",
                        name="Jira Issue Reference",
                        attachment_type=allure.attachment_type.TEXT
                    )
                    return
            
            # Get test metadata
            priority = getattr(test_func, 'jira_priority', None)
            labels = getattr(test_func, 'jira_labels', [])
            components = getattr(test_func, 'jira_components', [])
            custom_fields = getattr(test_func, 'jira_custom_fields', {})
            
            # Check for pytest.mark.jira
            jira_mark = item.get_closest_marker('jira')
            if jira_mark and jira_mark.kwargs:
                priority = priority or jira_mark.kwargs.get('priority')
                labels.extend(jira_mark.kwargs.get('labels', []))
                components.extend(jira_mark.kwargs.get('components', []))
                custom_fields.update(jira_mark.kwargs.get('custom_fields', {}))
            
            # Create Jira issue
            issue = jira_helper.create_issue_from_test_failure(
                test_name=item.nodeid,
                error_message=str(call.excinfo.value),
                test_code=inspect.getsource(item.function),
                screenshot_path=screenshot_path,
                ai_analysis=ai_analysis
            )
            
            print(f"Created Jira issue: {issue['key']} - {issue['url']}")
            
    except Exception as e:
        error_msg = f"Error creating Jira ticket: {str(e)}"
        print(error_msg)
        allure.attach(
            error_msg,
            name="Jira Integration Error",
            attachment_type=allure.attachment_type.TEXT
        )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    
    # We need to capture screenshots for failed tests, unless it's a simulated test
    if report.when == "call" and report.failed:
        try:
            # Skip simulated tests - they handle their own analysis
            if item.name == "test_automatic_analyzer" and "TestAIAnalyzer" in item.nodeid:
                print(f"Skipping automatic analysis for simulated test: {item.nodeid}")
                return
                
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
                            except Exception as resp_err:
                                try:
                                    response_data = call.excinfo.value.response.text
                                except Exception:
                                    response_data = f"Could not extract response data: {str(resp_err)}"
                        
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
                        error_msg = f"Error in AI test analysis: {str(e)}"
                        print(error_msg)
                        allure.attach(
                            error_msg,
                            name="AI Analysis Error",
                            attachment_type=allure.attachment_type.TEXT
                        )
                
                # Jira Integration - Create ticket for failed test
                if Config.JIRA_ENABLED:
                    print(f"\nJira Integration: Processing failed test {item.nodeid}")
                    # Get AI analysis if available
                    ai_analysis_result = analysis if 'analysis' in locals() else None
                    screenshot_file_path = screenshot_path if 'screenshot_path' in locals() else None
                    _create_jira_ticket_for_failure(item, call, screenshot_file_path, ai_analysis_result)
            else:
                # For non-UI tests (no _setup fixture), still create Jira tickets
                if Config.JIRA_ENABLED:
                    print(f"\nJira Integration: Processing failed test {item.nodeid} (non-UI test)")
                    _create_jira_ticket_for_failure(item, call)
        except Exception as e:
            print(f"Error taking screenshot: {str(e)}")
            allure.attach(
                f"Failed to take screenshot: {str(e)}",
                name="screenshot_error",
                attachment_type=allure.attachment_type.TEXT
            )

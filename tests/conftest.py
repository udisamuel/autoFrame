import pytest
import sys
import os
import allure
import importlib.metadata
from datetime import datetime
from playwright.sync_api import Playwright

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

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

@pytest.fixture(scope="function")
def _setup(playwright: Playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    yield page
    
    # --------------------- Tear down ---------------------
    browser.close()

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
        except Exception as e:
            print(f"Error taking screenshot: {str(e)}")
            allure.attach(
                f"Failed to take screenshot: {str(e)}",
                name="screenshot_error",
                attachment_type=allure.attachment_type.TEXT
            )

import logging
import os
import allure
from playwright.sync_api import Page
from config.config import Config
from utils.playwright_wrapper import PlaywrightWrapper

class BasePage:
    """Base page class that all page objects will inherit from."""
    
    def __init__(self, page: Page):
        self.page = page
        self.pw = PlaywrightWrapper(page)  # Initialize the Playwright wrapper
        self.base_url = Config.BASE_URL
        self.timeout = Config.DEFAULT_TIMEOUT
        self.logger = logging.getLogger(__name__)

    @allure.step("Navigate to {url_path}")
    def navigate_to(self, url_path):
        """Navigate to a specific URL path."""
        full_url = f"{self.base_url}{url_path}"
        self.logger.info(f"Navigating to: {full_url}")
        self.pw.navigate_to(full_url)
        
    def get_title(self):
        """Get the page title."""
        return self.page.title()
    
    @allure.step("Wait for element {selector} to be {state}")
    def wait_for_element(self, selector, state="visible"):
        """Wait for an element to be in a specific state."""
        self.pw.wait_for_selector(selector, state=state)
        
    @allure.step("Click on {selector}")
    def click(self, selector):
        """Click on an element."""
        self.pw.click(selector)
        
    @allure.step("Fill {selector} with '{text}'")
    def fill(self, selector, text):
        """Fill text into an input field."""
        self.pw.fill(selector, text)
        
    def get_text(self, selector):
        """Get text from an element."""
        return self.pw.get_text(selector)
    
    def is_element_visible(self, selector):
        """Check if an element is visible."""
        return self.pw.is_visible(selector)
    
    @allure.step("Take screenshot: {name}")
    def take_screenshot(self, name):
        """Take a screenshot."""
        # Ensure the screenshots directory exists
        os.makedirs(Config.SCREENSHOTS_PATH, exist_ok=True)
        
        # Generate a filename
        screenshot_path = f"{Config.SCREENSHOTS_PATH}/{name}.png"
        self.logger.info(f"Taking screenshot: {screenshot_path}")
        
        # Take the screenshot using Playwright's API
        screenshot_bytes = self.page.screenshot(full_page=True)
        
        # Save the screenshot to file
        with open(screenshot_path, 'wb') as f:
            f.write(screenshot_bytes)
        
        # Attach the screenshot bytes directly to the Allure report
        allure.attach(
            screenshot_bytes,
            name=name,
            attachment_type=allure.attachment_type.PNG
        )
        
        self.logger.info(f"Screenshot saved to: {screenshot_path}")
        return screenshot_path
    
    def element_contains_text(self, selector, text):
        """Check if an element contains specific text."""
        return self.pw.element_contains_text(selector, text)
    
    @allure.step("Select option in {selector}")
    def select_option(self, selector, value=None, index=None, label=None):
        """Select an option from a dropdown."""
        return self.pw.select_option(selector, value, index, label)
    
    @allure.step("Hover over {selector}")
    def hover(self, selector):
        """Hover over an element."""
        self.pw.hover(selector)
    
    def get_attribute(self, selector, attribute):
        """Get an attribute value from an element."""
        return self.pw.get_attribute(selector, attribute)
    
    @allure.step("Check {selector}")
    def check(self, selector):
        """Check a checkbox or radio button."""
        self.pw.check(selector)
    
    @allure.step("Uncheck {selector}")
    def uncheck(self, selector):
        """Uncheck a checkbox."""
        self.pw.uncheck(selector)
    
    @allure.step("Wait for URL: {url}")
    def wait_for_url(self, url, timeout=None):
        """Wait for URL to be a specific value."""
        self.pw.wait_for_url(url, timeout)

    @allure.step("Press key: {key}")
    def press_key(self, key):
        """Press a key on an element."""
        self.pw.press_global_key(key)
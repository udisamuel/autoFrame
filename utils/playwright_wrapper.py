import logging
from typing import Optional, Union, List, Dict, Any
from playwright.sync_api import Page, Locator
from config.config import Config

logger = logging.getLogger(__name__)

class PlaywrightWrapper:
    """
    Wrapper class for Playwright that provides enhanced functionality and utility methods.
    """
    
    def __init__(self, page: Page):
        """
        Initialize the wrapper with a Playwright page object.
        
        Args:
            page: The Playwright page object
        """
        self.page = page
        self.timeout = Config.DEFAULT_TIMEOUT
    
    def navigate_to(self, url: str) -> None:
        """
        Navigate to a specified URL.
        
        Args:
            url: The URL to navigate to
        """
        logger.info(f"Navigating to: {url}")
        self.page.goto(url, timeout=self.timeout)
    
    def click(self, selector: str, options: Optional[Dict[str, Any]] = None) -> None:
        """
        Click on an element.
        
        Args:
            selector: The selector for the element to click
            options: Optional click options
        """
        options = options or {}
        logger.info(f"Clicking element: {selector}")
        self.page.click(selector, timeout=self.timeout, **options)
    
    def fill(self, selector: str, value: str) -> None:
        """
        Fill text into an input field.
        
        Args:
            selector: The selector for the input field
            value: The text to fill
        """
        logger.info(f"Filling '{value}' in element: {selector}")
        self.page.fill(selector, value, timeout=self.timeout)
    
    def get_text(self, selector: str) -> str:
        """
        Get text content from an element.
        
        Args:
            selector: The selector for the element
            
        Returns:
            The text content of the element
        """
        return self.page.text_content(selector, timeout=self.timeout)
    
    def element_contains_text(self, selector: str, text: str) -> bool:
        """
        Check if an element contains specific text.
        
        Args:
            selector: The selector for the element
            text: The text to check for
            
        Returns:
            True if the element contains the text, False otherwise
        """
        element_text = self.page.text_content(selector, timeout=self.timeout)
        logger.debug(f"Element text: '{element_text}', checking for: '{text}'")
        return text in element_text

    def wait_for_selector(self, selector: str, state: str = "visible", timeout: Optional[int] = None) -> Locator:
        """
        Wait for an element to be in a specific state.

        Args:
            selector: The selector for the element
            state: The state to wait for (visible, hidden, attached, detached)
            timeout: The timeout in milliseconds

        Returns:
            The Playwright Locator object for the element
        """
        actual_timeout = timeout or self.timeout
        logger.info(f"Waiting for element: {selector} to be {state} (timeout: {actual_timeout}ms)")
        return self.page.wait_for_selector(selector, state=state, timeout=actual_timeout)

    
    def is_visible(self, selector: str) -> bool:
        """
        Check if an element is visible.
        
        Args:
            selector: The selector for the element
            
        Returns:
            True if the element is visible, False otherwise
        """
        return self.page.is_visible(selector)

    
    def take_screenshot(self, path: str, full_page: bool = False) -> None:
        """
        Take a screenshot.
        
        Args:
            path: The path where to save the screenshot
            full_page: Whether to take a screenshot of the full page
        """
        logger.info(f"Taking screenshot: {path}")
        self.page.screenshot(path=path, full_page=full_page)

    
    def select_option(self, selector: str, value: Optional[Union[str, List[str]]] = None, 
                      index: Optional[Union[int, List[int]]] = None,
                      label: Optional[Union[str, List[str]]] = None) -> List[str]:
        """
        Select an option from a dropdown.
        
        Args:
            selector: The selector for the dropdown
            value: The value to select
            index: The index to select
            label: The label to select
            
        Returns:
            A list of selected values
        """
        options = {}
        if value is not None:
            options['value'] = value
        if index is not None:
            options['index'] = index
        if label is not None:
            options['label'] = label
            
        logger.info(f"Selecting option in dropdown: {selector} with options: {options}")
        return self.page.select_option(selector, **options, timeout=self.timeout)
    
    def hover(self, selector: str) -> None:
        """
        Hover over an element.
        
        Args:
            selector: The selector for the element
        """
        logger.info(f"Hovering over element: {selector}")
        self.page.hover(selector, timeout=self.timeout)
    
    def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """
        Get an attribute value from an element.
        
        Args:
            selector: The selector for the element
            attribute: The attribute name
            
        Returns:
            The attribute value or None if not found
        """
        return self.page.get_attribute(selector, attribute, timeout=self.timeout)

    
    def check(self, selector: str) -> None:
        """
        Check a checkbox or radio button.
        
        Args:
            selector: The selector for the element
        """
        logger.info(f"Checking element: {selector}")
        self.page.check(selector, timeout=self.timeout)
    
    def uncheck(self, selector: str) -> None:
        """
        Uncheck a checkbox.
        
        Args:
            selector: The selector for the element
        """
        logger.info(f"Unchecking element: {selector}")
        self.page.uncheck(selector, timeout=self.timeout)
    
    def wait_for_url(self, url: str, timeout: Optional[int] = None) -> None:
        """
        Wait for URL to be a specific value.
        
        Args:
            url: The URL to wait for
            timeout: The timeout in milliseconds
        """
        actual_timeout = timeout or self.timeout
        logger.info(f"Waiting for URL: {url} (timeout: {actual_timeout}ms)")
        self.page.wait_for_url(url, timeout=actual_timeout)

    def press_global_key(self, key):
        """
        Press a keyboard key globally (not specific to any element).

        Args:
            key: The key to press
        """
        self.page.keyboard.press(key)

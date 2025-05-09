from dataclasses import dataclass
from pages.base_page import BasePage
import allure

@dataclass
class MainPageLocators:
    """Locators for the Main Page."""
    HOME_URL: str = "/"

class MainPage(BasePage):
    """Main Page class for handling main page interactions."""

    def navigate_to_home(self):
        """Navigate to the home page."""
        self.navigate_to(MainPageLocators.HOME_URL)
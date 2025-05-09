from pages.main_page.main_page import MainPage
import allure
import pytest

@allure.feature("Test Sample")
@pytest.mark.sample
class TestSample:

    @allure.story("Sample Test")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test sample functionality")
    def test_sample(self, _setup):
        """Sample test to demonstrate the structure."""
        # Initialize Main Page
        mp = MainPage(_setup)

        # Navigate to the home page
        mp.navigate_to_home()


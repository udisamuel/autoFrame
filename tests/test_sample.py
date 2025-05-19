from pages.main_page.main_page import MainPage
import allure
import pytest
from utils.timer import Timer

@allure.feature("Test Sample")
@pytest.mark.sample
class TestSample:

    @pytest.mark.xray("AUTOFRAME-1")
    @allure.story("Sample Test")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test sample functionality")
    def test_sample(self, _setup):
        """Sample test to demonstrate the structure."""
        print("Running sample test...")
        # Start the timer
        with Timer(name="Sample Test Timer", store_stats=True, allure_attach=True) as timer:

            # Initialize Main Page
            mp = MainPage(_setup)

            # Navigate to the home page
            mp.navigate_to_home()

        assert True


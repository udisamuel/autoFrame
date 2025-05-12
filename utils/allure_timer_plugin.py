import allure
import json
import pytest
from typing import Dict, Any, List
from utils.timer import Timer

@pytest.hookimpl
def pytest_configure(config):
    """Register the custom category for timer data."""
    allure.dynamic.title("Timer Data")
    

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Add timer data to Allure report as a separate tab."""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call":
        # Only do this for the actual test call, not setup or teardown
        stats = Timer.get_stats()
        if stats:
            # Add overall timer statistics
            add_timer_data_to_allure(stats)


def add_timer_data_to_allure(stats: Dict[str, Any]):
    """Add timer data as a custom attachment to Allure report."""
    if not stats:
        return
    
    # Create a formatted representation of timer stats
    formatted_stats = {}
    
    for timer_name, timer_data in stats.items():
        formatted_stats[timer_name] = {
            "count": timer_data["count"],
            "total_seconds": round(timer_data["total"], 4),
            "min_seconds": round(timer_data["min"], 4),
            "max_seconds": round(timer_data["max"], 4),
            "mean_seconds": round(timer_data["mean"], 4),
            "median_seconds": round(timer_data["median"], 4),
            "stdev_seconds": round(timer_data["stdev"], 4) if timer_data["count"] > 1 else 0,
        }
    
    # Convert to JSON for easy reading in the report
    json_stats = json.dumps(formatted_stats, indent=4)
    
    # Add as an attachment to the Allure report
    allure.attach(
        json_stats,
        name="Timer Statistics",
        attachment_type=allure.attachment_type.JSON
    )
    
    # Also add a simple text summary for quick reference
    summary_text = "## Timer Summary\n\n"
    for timer_name, timer_data in formatted_stats.items():
        summary_text += f"### {timer_name}\n"
        summary_text += f"- Count: {timer_data['count']}\n"
        summary_text += f"- Average time: {timer_data['mean_seconds']}s\n"
        summary_text += f"- Min/Max: {timer_data['min_seconds']}s / {timer_data['max_seconds']}s\n\n"
    
    allure.attach(
        summary_text,
        name="Timer Summary",
        attachment_type=allure.attachment_type.MARKDOWN
    )


# Add test environment info related to timers
def pytest_sessionstart(session):
    """Add environment info at the start of the test session."""
    environment_properties = {
        "Timer enabled": "True",
        "Timer version": "1.1.0",  # Version of your enhanced timer
    }
    
    # Create environment.properties file for Allure
    with open('environment.properties', 'w') as f:
        for key, value in environment_properties.items():
            f.write(f"{key}={value}\n")

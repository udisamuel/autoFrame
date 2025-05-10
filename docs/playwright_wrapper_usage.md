# Playwright Wrapper Usage Guide

## Overview

The `PlaywrightWrapper` class provides a convenient wrapper around Playwright's core functionality, making it easier to write maintainable UI tests. This guide covers all the available methods with examples.

## Table of Contents

- [Basic Setup](#basic-setup)
- [Navigation](#navigation)
- [Element Interaction](#element-interaction)
  - [Click and Fill](#click-and-fill)
  - [Element Properties](#element-properties)
  - [Form Elements](#form-elements)
  - [Hovering and Keyboard](#hovering-and-keyboard)
- [Waiting and Assertions](#waiting-and-assertions)
- [Screenshots](#screenshots)
- [Drag and Drop Operations](#drag-and-drop-operations)
  - [Drag and Drop Between Elements](#drag-and-drop-between-elements)
  - [Drag to Coordinates](#drag-to-coordinates)
  - [Drag By Offset](#drag-by-offset)
- [Integration with Page Object Model](#integration-with-page-object-model)
- [Best Practices](#best-practices)

## Basic Setup

To use the `PlaywrightWrapper`, you'll need to first obtain a Playwright page object. Typically, this is done through a fixture in `conftest.py`.

```python
# In conftest.py
@pytest.fixture
def page():
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()
    browser.close()

@pytest.fixture
def playwright_wrapper(page):
    return PlaywrightWrapper(page)
```

```python
# In your test file
def test_example(playwright_wrapper):
    # Now you can use the wrapper
    playwright_wrapper.navigate_to("https://example.com")
```

## Navigation

### Navigate to URL

```python
# Navigate to a URL
playwright_wrapper.navigate_to("https://example.com")

# Wait for URL to change
playwright_wrapper.wait_for_url("https://example.com/dashboard", timeout=10000)
```

## Element Interaction

### Click and Fill

```python
# Click an element
playwright_wrapper.click("#submit-button")

# Click with options (force, position, etc.)
playwright_wrapper.click("#submit-button", {"force": True, "position": {"x": 5, "y": 5}})

# Fill a form field
playwright_wrapper.fill("#username", "testuser")
playwright_wrapper.fill("#password", "password123")
```

### Element Properties

```python
# Get text content
text = playwright_wrapper.get_text(".message")
print(f"Message: {text}")

# Check if element contains text
has_welcome = playwright_wrapper.element_contains_text(".header", "Welcome")
if has_welcome:
    print("Welcome message is displayed")

# Check if element is visible
is_visible = playwright_wrapper.is_visible(".notification")
print(f"Notification visible: {is_visible}")

# Get attribute value
href = playwright_wrapper.get_attribute("a.main-link", "href")
print(f"Link URL: {href}")
```

### Form Elements

```python
# Select option by value
playwright_wrapper.select_option("#country", value="US")

# Select option by label
playwright_wrapper.select_option("#country", label="United States")

# Select option by index
playwright_wrapper.select_option("#country", index=0)

# Check a checkbox
playwright_wrapper.check("#agree-terms")

# Uncheck a checkbox
playwright_wrapper.uncheck("#marketing-emails")
```

### Hovering and Keyboard

```python
# Hover over element
playwright_wrapper.hover(".dropdown-menu")

# Press a key globally
playwright_wrapper.press_global_key("Escape")
```

## Waiting and Assertions

```python
# Wait for element to be visible
playwright_wrapper.wait_for_selector(".loading-indicator", state="visible")

# Wait for element to be hidden
playwright_wrapper.wait_for_selector(".loading-indicator", state="hidden")

# Wait for specific timeout
playwright_wrapper.wait_for_selector(".content", timeout=5000)
```

## Screenshots

```python
# Take a screenshot of viewport
playwright_wrapper.take_screenshot("login_form.png")

# Take a full page screenshot
playwright_wrapper.take_screenshot("full_page.png", full_page=True)
```

## Drag and Drop Operations

### Drag and Drop Between Elements

The `drag_and_drop` method allows you to drag an element onto another element.

```python
# Basic drag and drop from source to target
playwright_wrapper.drag_and_drop(
    source_selector="#draggable-item", 
    target_selector="#drop-zone"
)

# Drag and drop with specific positions within the elements
playwright_wrapper.drag_and_drop(
    source_selector="#draggable-item", 
    target_selector="#drop-zone",
    source_position={"x": 0.1, "y": 0.1},  # Near the top-left of source element
    target_position={"x": 0.5, "y": 0.5}   # Center of target element
)
```

### Drag to Coordinates

The `drag_to_coordinates` method allows you to drag an element to specific coordinates on the page.

```python
# Drag element to specific x, y coordinates on the page
playwright_wrapper.drag_to_coordinates(
    source_selector="#draggable-item", 
    x=500,  # X coordinate on the page
    y=300   # Y coordinate on the page
)
```

### Drag By Offset

The `drag_by_offset` method allows you to drag an element by a specific amount from its current position.

```python
# Drag element by offset
playwright_wrapper.drag_by_offset(
    source_selector="#draggable-item", 
    x_offset=100,  # Drag 100px to the right
    y_offset=-50   # Drag 50px up
)

# Drag horizontally only
playwright_wrapper.drag_by_offset(
    source_selector="#slider", 
    x_offset=200,  # Drag 200px to the right
    y_offset=0     # No vertical movement
)
```

## Integration with Page Object Model

Here's an example of integrating the Playwright wrapper with the Page Object Model:

```python
# In a page object file
class DragDropPage(BasePage):
    # Locators
    DRAGGABLE_ITEM = "#draggable"
    DROP_ZONE = "#droppable"
    SUCCESS_MESSAGE = "#success-message"
    SLIDER = "#slider"
    SLIDER_VALUE = "#slider-value"
    
    def __init__(self, page):
        super().__init__(page)
        self.url = "/drag-drop-demo"
    
    def load_page(self):
        self.navigate_to(self.url)
    
    def drag_item_to_zone(self):
        self.pw.drag_and_drop(self.DRAGGABLE_ITEM, self.DROP_ZONE)
    
    def drag_with_offset(self, x_offset, y_offset):
        self.pw.drag_by_offset(self.DRAGGABLE_ITEM, x_offset, y_offset)
    
    def adjust_slider(self, value_percentage):
        # Calculate the offset to achieve the desired percentage
        slider_box = self.page.locator(self.SLIDER).bounding_box()
        offset = int(slider_box["width"] * (value_percentage / 100))
        self.pw.drag_by_offset(self.SLIDER, offset, 0)
    
    def get_success_message(self):
        return self.get_text(self.SUCCESS_MESSAGE)
    
    def get_slider_value(self):
        return self.get_text(self.SLIDER_VALUE)
```

And in your test:

```python
def test_drag_drop_functionality(page):
    drag_drop_page = DragDropPage(page)
    
    # Load the page
    drag_drop_page.load_page()
    
    # Perform drag and drop
    drag_drop_page.drag_item_to_zone()
    
    # Verify success message
    assert "Dropped!" in drag_drop_page.get_success_message()
    
    # Adjust slider to 75%
    drag_drop_page.adjust_slider(75)
    
    # Verify slider value
    assert "75" in drag_drop_page.get_slider_value()
```

## Best Practices

1. **Use Appropriate Selectors**: Prefer stable selectors like IDs, data-testid, or specific test attributes rather than relying on CSS classes or XPaths that may change.

2. **Handle Waiting Properly**: Always wait for elements to be in the expected state before interacting with them.

3. **Log Actions Properly**: The wrapper automatically logs most actions, but add additional logging for complex sequences.

4. **Encapsulate in Page Objects**: Use the wrapper within page object methods rather than directly in test cases.

5. **Set Appropriate Timeouts**: Configure the default timeout in your Config class to match the responsiveness of your application.

6. **Take Screenshots on Failure**: Configure your test framework to take screenshots when tests fail:

```python
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call" and report.failed:
        if "page" in item.funcargs:
            page = item.funcargs["page"]
            screenshot_path = f"failures/{item.nodeid.replace('/', '_')}.png"
            page.screenshot(path=screenshot_path, full_page=True)
            allure.attach.file(screenshot_path, attachment_type=allure.attachment_type.PNG)
```

7. **Handle Drag and Drop Dynamically**: When using drag and drop operations, consider the specific behavior of your application—some may require holding the mouse down longer or moving it more slowly.

---

This guide covers the core functionality of the `PlaywrightWrapper`. For more advanced usage, refer to the [Playwright Python documentation](https://playwright.dev/python/docs/intro).

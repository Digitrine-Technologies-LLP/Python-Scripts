import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# Common device viewport sizes
VIEWPORTS = [
    ("Mobile S",    375,  667),
    ("Mobile L",    414,  896),
    ("Tablet",      768, 1024),
    ("Laptop",     1280,  800),
    ("Desktop",    1920, 1080),
]

@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Remove this to see the browser
    d = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    yield d
    d.quit()

@pytest.mark.parametrize("device,width,height", VIEWPORTS)
def test_responsive_layout(driver, device, width, height):
    driver.set_window_size(width, height)
    driver.get("https://www.spanishamericancenter.org/")

    # Take a screenshot for each viewport
    driver.save_screenshot(f"screenshot_{device.replace(' ', '_')}.png")

    # Check that the page body is visible at this size
    body = driver.find_element(By.TAG_NAME, "body")
    assert body.is_displayed(), f"Body not visible on {device}"

    print(f"✓ {device} ({width}x{height}) passed")
import time
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


VIEWPORTS = [
    ("Mobile_S",  375,  667),
    ("Mobile_L",  414,  896),
    ("Tablet",    768, 1024),
    ("Laptop",   1280,  800),
    ("Desktop",  1920, 1080),
]


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    # Disable scrollbars so they don't appear in full-page shots
    options.add_argument("--hide-scrollbars")
    d = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    yield d
    d.quit()


def full_page_screenshot(driver, width, path):
    """
    Scroll the page to trigger lazy-loaded content, then expand the window
    to the full scroll height and capture one screenshot.
    """
    # Set initial viewport width so the page lays out correctly
    driver.set_window_size(width, 900)

    # Scroll through the page to trigger any lazy-loaded content
    total_height = driver.execute_script("return document.body.scrollHeight")
    scroll_y = 0
    step = 600
    while scroll_y < total_height:
        driver.execute_script(f"window.scrollTo(0, {scroll_y});")
        time.sleep(0.15)
        scroll_y += step
        total_height = driver.execute_script("return document.body.scrollHeight")

    # Scroll back to top, expand window to full height, then screenshot
    driver.execute_script("window.scrollTo(0, 0);")
    driver.set_window_size(width, total_height)
    time.sleep(0.3)
    driver.save_screenshot(path)


@pytest.mark.parametrize("device,width,height", VIEWPORTS)
def test_responsive_layout(driver, url, device, width, height):
    driver.set_window_size(width, height)
    driver.get(url)

    # Wait for page to settle
    time.sleep(1)

    full_page_screenshot(driver, width, f"screenshot_{device}.png")

    body = driver.find_element(By.TAG_NAME, "body")
    assert body.is_displayed(), f"Body not visible on {device} ({width}x{height})"

    print(f"✓ {device} ({width}x{height}) — full-page screenshot saved")

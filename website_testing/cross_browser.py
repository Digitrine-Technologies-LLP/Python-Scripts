import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# Define the browsers to test against
@pytest.fixture(params=["chrome", "firefox", "edge"])
def driver(request):
    if request.param == "chrome":
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    elif request.param == "firefox":
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
    elif request.param == "edge":
        driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()))

    driver.implicitly_wait(10)
    yield driver
    driver.quit()

# This test will automatically run once per browser
def test_page_title(driver):
    driver.get("https://example.com")
    assert "Example" in driver.title

def test_heading_visible(driver):
    from selenium.webdriver.common.by import By
    driver.get("https://example.com")
    heading = driver.find_element(By.TAG_NAME, "h1")
    assert heading.is_displayed()
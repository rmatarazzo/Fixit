from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()  # Replace with your preferred browser driver
driver.get("https://www.youtube.com/watch?v=ooFOKTpDfyc&pp=ygUaaG93IHRvIGZpeDogc3F1ZWFreSBmbG9vcnM%3D")

# Find the thumbnail element (adjust the selector as needed)
thumbnail_element = driver.find_element(By.ID, "thumbnail")

# Get the thumbnail URL
thumbnail_url = thumbnail_element.get_attribute('src')

# Download or use the thumbnail URL as needed
print(thumbnail_url)

driver.quit()
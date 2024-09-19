from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import os
import logging
import time

def setup_logging():
    """Sets up logging configuration."""
    logging.basicConfig(
        filename='search_log.log',
        level=logging.DEBUG,  # Set the logging level to DEBUG to capture all types of log messages
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def log_message(message, level='info'):
    """Logs messages at different levels."""
    if level == 'info':
        logging.info(message)
    elif level == 'error':
        logging.error(message)
    elif level == 'debug':
        logging.debug(message)
    elif level == 'warning':
        logging.warning(message)
    elif level == 'critical':
        logging.critical(message)

def ensure_output_folder_exists(folder_name='data_output_files'):
    """Ensures the output folder exists, creates it if it does not."""
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

def get_current_timestamp():
    """Returns the current timestamp as a string."""
    return time.strftime("%Y%m%d-%H%M%S")

def format_duration(duration):
    """Formats the duration string."""
    return duration.strip()

def search_youtube(query, progress_bar, progress_text):
    """Searches YouTube for the given query and saves video titles, URLs, durations, descriptions, and thumbnails in JSON format."""
    
    # Set up Selenium WebDriver with headless option
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Runs Chrome in headless mode.
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        base_url = "https://www.youtube.com"
        search_url = f"{base_url}/results?search_query={query.replace(' ', '+')}"
        
        # Access the YouTube search results page
        driver.get(search_url)
        log_message(f"Accessing YouTube for query: {query}", level='debug')
        progress_text.text("Accessing YouTube...")

        # Wait for the video results to load
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ytd-video-renderer')))
        progress_bar.progress(50)
        progress_text.text("Fetching video titles, URLs, descriptions, thumbnails, and durations...")

        # Scroll to the bottom of the page to load more videos
        last_height = driver.execute_script("return document.documentElement.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)  # Wait for the page to load
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Collect videos
        videos = []
        video_elements = driver.find_elements(By.CSS_SELECTOR, 'ytd-video-renderer')

        for video in video_elements:
            try:
                title_element = video.find_element(By.ID, 'video-title')
                title = title_element.get_attribute('title')
                url = title_element.get_attribute('href')

                # Fetching duration with script handling
                try:
                    duration_script = '''
                        return arguments[0].querySelector('span.ytd-thumbnail-overlay-time-status-renderer').innerText.trim();
                    '''
                    duration = driver.execute_script(duration_script, video)
                    formatted_duration = format_duration(duration)
                except Exception as e:
                    formatted_duration = "Unknown"
                    log_message(f"Duration not found for video {title}: {e}", level='error')

                # Fetching full description, considering dynamic parts
                try:
                    description_element = video.find_element(By.CSS_SELECTOR, 'yt-formatted-string.metadata-snippet-text')
                    description = description_element.text.strip()
                except Exception as e:
                    description = "No description available"
                    log_message(f"Description not found for video {title}: {e}", level='error')

                # Fetching thumbnail URL, checking multiple paths
                thumbnail_url = None  # Initialize as None
                try:
                    # First try the direct img element within the video element
                    thumbnail_element = video.find_element(By.CSS_SELECTOR, 'img')
                    thumbnail_url = thumbnail_element.get_attribute('src')
                except Exception as e:
                    log_message(f"Thumbnail not found at main path for video {title}: {e}", level='debug')

                # If direct img element doesn't work, try alternative path(s)
                if not thumbnail_url:
                    try:
                        thumbnail_element = video.find_element(By.CSS_SELECTOR, 'ytd-thumbnail img')
                        thumbnail_url = thumbnail_element.get_attribute('src')
                    except Exception as e:
                        log_message(f"Thumbnail not found at alternative path for video {title}: {e}", level='debug')

                if url and title:
                    videos.append({
                        'title': title, 
                        'url': url, 
                        'duration': formatted_duration, 
                        'description': description, 
                        'thumbnail_url': thumbnail_url
                    })
                    log_message(f"Found video: {title} ({url}) [Duration: {formatted_duration}] [Thumbnail: {thumbnail_url}]", level='debug')

            except Exception as e:
                log_message(f"Error while processing a video element: {e}", level='error')

        ensure_output_folder_exists()

        timestamp = get_current_timestamp()
        output_file_path = os.path.join('data_output_files', f'video_data_{timestamp}.json')

        output_data = {
            'timestamp': timestamp,
            'videos': videos
        }

        with open(output_file_path, 'w') as file:
            json.dump(output_data, file, indent=4)
        log_message(f"Successfully saved video data to {output_file_path}", level='info')

        progress_bar.progress(75)
        progress_text.text("Saved video data to JSON file and displaying results...")

        return videos

    except Exception as e:
        log_message(f"Error while searching YouTube: {e}", level='error')
        progress_text.text("Error occurred while fetching video data.")
        return []

    finally:
        if driver:
            driver.quit()
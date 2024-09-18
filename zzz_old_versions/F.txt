import os
import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import streamlit as st

def get_current_timestamp():
    """Returns the current timestamp in a string format suitable for filenames."""
    return datetime.now().strftime('%Y-%m-%d_%H%M%S')

def setup_logging():
    """Sets up logging configuration with dynamic filename in the logs folder."""
    logs_folder = 'logs'
    
    # Ensure logs directory exists
    if not os.path.exists(logs_folder):
        os.makedirs(logs_folder)
    
    log_filename = os.path.join(logs_folder, f'search_log_{get_current_timestamp()}.log')
    
    logging.basicConfig(filename=log_filename, level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logging.info(f"Logging initialized. Log file: {log_filename}")

def ensure_output_folder_exists(folder_name='data_output_files'):
    """Ensures the output folder exists, creates it if it does not."""
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

def log_message(message, level='info'):
    """Logs messages at different levels with timestamps."""
    if level == 'info':
        logging.info(message)
    elif level == 'error':
        logging.error(message)
    elif level == 'debug':
        logging.debug(message)

def format_duration(duration):
    """Converts duration from 'mm:ss' or 'hh:mm:ss' format to 'X minutes, Y seconds'."""
    parts = duration.split(':')
    
    if len(parts) == 2:  # Format is mm:ss
        minutes, seconds = parts
        return f"{int(minutes)} minutes, {int(seconds)} seconds"
    
    elif len(parts) == 3:  # Format is hh:mm:ss
        hours, minutes, seconds = parts
        return f"{int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"
    
    return duration  # If the format doesn't match, return as is

def search_youtube(query, progress_bar, progress_text):
    """Searches YouTube for the given query and saves video titles, URLs, and durations in JSON format with a timestamped filename."""
    
    # Set up Selenium WebDriver with headless option
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Runs Chrome in headless mode.
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        base_url = "https://www.youtube.com"
        search_url = f"{base_url}/results?search_query={query.replace(' ', '+')}"
        
        # Access the YouTube search results page
        driver.get(search_url)
        log_message(f"Accessing YouTube for query: {query}", level='debug')
        progress_text.text("Accessing YouTube...")

        # Wait for the video results to load (search for video titles to ensure content is present)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ytd-video-renderer')))
        progress_bar.progress(50)
        progress_text.text("Fetching video titles, URLs, and durations...")

        # Collect video titles, URLs, and durations from the search result page
        videos = []
        video_elements = driver.find_elements(By.CSS_SELECTOR, 'ytd-video-renderer')

        for video in video_elements:
            title_element = video.find_element(By.ID, 'video-title')
            title = title_element.get_attribute('title')
            url = title_element.get_attribute('href')

            # Execute JavaScript to extract the duration from the thumbnailOverlayTimeStatusRenderer
            try:
                script = '''
                    return arguments[0].querySelector('span.ytd-thumbnail-overlay-time-status-renderer').innerText.trim();
                '''
                duration = driver.execute_script(script, video)
                formatted_duration = format_duration(duration)  # Convert to the new format
            except Exception as e:
                formatted_duration = "Unknown"  # If duration is not found or an error occurs
                log_message(f"Duration not found for video {title}: {e}", level='error')

            if url and title:
                videos.append({'title': title, 'url': url, 'duration': formatted_duration})
                log_message(f"Found video: {title} ({url}) [Duration: {formatted_duration}]", level='debug')

        # Ensure output directory exists
        ensure_output_folder_exists()

        # Generate timestamped JSON file name
        timestamp = get_current_timestamp()
        output_file_path = os.path.join('data_output_files', f'video_data_{timestamp}.json')

        # Save video data (titles, URLs, and durations) to JSON file with timestamp
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
        driver.quit()

def main():
    """Main function to run the Streamlit app."""
    setup_logging()
    
    st.title("YouTube Video Scraper")
    st.write("This app searches YouTube for a given query and scrapes related video titles, URLs, and durations.")
    
    # Input field for search query
    query = st.text_input("Enter your YouTube search query:", "how to fix: ")
    
    # Button to start the scraping process
    if st.button("Start Search"):
        # Display progress bar and status text
        progress_bar = st.progress(0)
        progress_text = st.empty()
        
        # Perform the YouTube search
        progress_text.text("Starting search...")
        videos = search_youtube(query, progress_bar, progress_text)
        
        # Display results with numbering
        if videos:
            st.write(f"Total videos collected: {len(videos)}")
            st.write("Video Titles, URLs, and Durations found:")
            for idx, video in enumerate(videos, start=1):
                st.write(f"{idx}. **Title:** {video['title']}")
                st.write(f"   **URL:** {video['url']}")
                st.write(f"   **Duration:** {video['duration']}")
        else:
            st.write("No videos found.")

         # Now that all videos have been displayed, update the progress message
        progress_bar.progress(100)
        progress_text.text("Completed!")  # Move this after the videos are displayed

if __name__ == "__main__":
    main()

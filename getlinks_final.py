from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re
import time
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# File to store patent URLs
PATENTS_FILE = "patent_urls.txt"
no_of_results = 100

PAGE_LOAD_DELAY = 15  # Seconds to wait for page load
BETWEEN_PAGES_DELAY = 10  # Seconds to wait between pages
MAX_RETRIES = 3  # Maximum number of retries per page

def get_date_range():
    # end_date = datetime.now()
    end_date = datetime.now() - timedelta(days=5)  # Exclude today
    start_date = end_date - timedelta(days=10)
    return start_date, end_date

def load_existing_patents():
    if os.path.exists(PATENTS_FILE):
        with open(PATENTS_FILE, 'r') as f:
            return set(line.strip() for line in f)
    return set()

def save_new_patents(new_patents, existing_patents):
    with open(PATENTS_FILE, 'a') as f:
        for patent in new_patents:
            if patent not in existing_patents:
                f.write(f"{patent}\n")

def construct_url(page_num, start_date, end_date):
    formatted_start_date = start_date.strftime("%Y%m%d")
    formatted_end_date = end_date.strftime("%Y%m%d")
    return f"https://patents.google.com/?country=US&before=publication:{formatted_end_date}&after=publication:{formatted_start_date}&language=ENGLISH&type=PATENT&num={no_of_results}&dups=language&page={page_num}"

def save_scraping_state(date, page_num):
    """Save the current scraping state"""
    with open("recent_scraping_state.txt", "w") as f:
        f.write(f"{date.strftime('%Y-%m-%d')},{page_num}")

def load_scraping_state():
    """Load the last scraping state"""
    try:
        with open("recent_scraping_state.txt", "r") as f:
            date_str, page_num = f.read().strip().split(",")
            return datetime.strptime(date_str, "%Y-%m-%d"), int(page_num)
    except FileNotFoundError:
        return None, 0

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--remote-debugging-port=9222")
chrome_options.binary_location = "/snap/bin/chromium"  # Path to Chromium binary from snap

def getLinks():
    # Get dynamic date range
    start_date, end_date = get_date_range()
    print(f"\nScraping patents from {start_date.date()} to {end_date.date()}")
    
    # Initialize the driver with specific ChromeDriver path
    driver = webdriver.Chrome(
        service=Service("/snap/chromium/current/usr/lib/chromium-browser/chromedriver"),
        options=chrome_options
    )
    all_patent_links = []
    
    # Load existing patents
    existing_patents = load_existing_patents()
    print(f"Found {len(existing_patents)} existing patents in {PATENTS_FILE}")
    
    # Load last state
    last_date, page_num = load_scraping_state()
    if last_date and last_date == start_date:
        print(f"Resuming from page {page_num + 1}")
    else:
        page_num = 0
    
    try:
        while True:
            # Load the page
            current_url = construct_url(page_num, start_date, end_date)
            print(f"\nFetching page {page_num + 1}")
            print(f"URL: {current_url}")
            
            retry_count = 0
            while retry_count < MAX_RETRIES:
                try:
                    driver.get(current_url)
                    time.sleep(PAGE_LOAD_DELAY)  # Wait for content to load
                    
                    # Get the page source after JavaScript execution
                    html_content = driver.page_source
                    
                    # Use regex to find all patent numbers
                    patent_numbers = re.findall(r"US\d{1,11}", html_content)
                    break
                except Exception as e:
                    retry_count += 1
                    print(f"Attempt {retry_count} failed: {str(e)}")
                    if retry_count == MAX_RETRIES:
                        raise
                    time.sleep(PAGE_LOAD_DELAY)
            
            # If no patents found on the page, break the loop
            if not patent_numbers:
                print(f"No more results found after page {page_num + 1}")
                break
            
            # Remove duplicates while preserving order
            patent_numbers = list(dict.fromkeys(patent_numbers))
            
            # Generate full URLs
            patent_links = [f"https://patents.google.com/patent/{patent_number}" for patent_number in patent_numbers]
            
            # Filter out already existing patents
            new_patents = [link for link in patent_links if link not in existing_patents]
            
            # Print the extracted links for current page
            print(f"Patents found on page {page_num + 1}: {len(patent_links)}")
            print(f"New patents found: {len(new_patents)}")
            for i, link in enumerate(new_patents, 1):
                print(f"{i}. {link}")
            
            # Save new patents to file
            save_new_patents(new_patents, existing_patents)
            existing_patents.update(new_patents)
            
            # Add to master list
            all_patent_links.extend(new_patents)  # Only extend with new patents
            
            # Save current state
            save_scraping_state(start_date, page_num)
            
            # Move to next page with increased delay
            page_num += 1
            time.sleep(BETWEEN_PAGES_DELAY)
            
    except KeyboardInterrupt:
        print("\nScraping interrupted by user. Progress has been saved.")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
    finally:
        driver.quit()
        print(f"\nScraping completed or interrupted.")
        print(f"Total new patents found: {len(all_patent_links)}")
        print(f"Total unique patents in {PATENTS_FILE}: {len(existing_patents)}")
        return all_patent_links

if __name__ == "__main__":
    getLinks()

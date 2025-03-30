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
CHUNK_DAYS = 10  # Number of days to process in each chunk

def get_date_chunks():
    """Generate date chunks from 1900 to present"""
    start = datetime(1900, 1, 1)
    end = datetime.now()
    current = start
    
    while current < end:
        chunk_end = min(current + timedelta(days=CHUNK_DAYS-1), end)
        yield current, chunk_end
        current = chunk_end + timedelta(days=1)

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
                print(f"Saved new unique patent: {patent}")

def save_progress(date):
    """Save the last processed date to resume later"""
    with open("scraping_progress.txt", "w") as f:
        f.write(date.strftime("%Y-%m-%d"))

def load_progress():
    """Load the last processed date"""
    try:
        with open("scraping_progress.txt", "r") as f:
            date_str = f.read().strip()
            return datetime.strptime(date_str, "%Y-%m-%d")
    except FileNotFoundError:
        return datetime(1900, 1, 1)

def construct_url(page_num, start_date, end_date):
    formatted_start_date = start_date.strftime("%Y%m%d")
    formatted_end_date = end_date.strftime("%Y%m%d")
    return f"https://patents.google.com/?country=US&before=publication:{formatted_end_date}&after=publication:{formatted_start_date}&language=ENGLISH&type=PATENT&num={no_of_results}&dups=language&page={page_num}"

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--remote-debugging-port=9222")
chrome_options.binary_location = "/snap/bin/chromium"  # Path to Chromium binary from snap

def scrape_date_range(driver, start_date, end_date, existing_patents):
    """Scrape patents for a specific date range"""
    all_patent_links = []
    page_num = 0
    
    while True:
        current_url = construct_url(page_num, start_date, end_date)
        print(f"\nFetching page {page_num + 1} for date range: {start_date.date()} to {end_date.date()}")
        print(f"URL: {current_url}")
        
        try:
            driver.get(current_url)
            time.sleep(15)  # Wait for content to load
            
            html_content = driver.page_source
            patent_numbers = re.findall(r"US\d{1,11}", html_content)
            
            if not patent_numbers:
                print(f"No more results found after page {page_num + 1}")
                break
            
            patent_numbers = list(dict.fromkeys(patent_numbers))
            patent_links = [f"https://patents.google.com/patent/{patent_number}" for patent_number in patent_numbers]
            new_patents = [link for link in patent_links if link not in existing_patents]
            
            print(f"Patents found on page {page_num + 1}: {len(patent_links)}")
            print(f"New patents found: {len(new_patents)}")
            
            save_new_patents(new_patents, existing_patents)
            existing_patents.update(new_patents)
            all_patent_links.extend(new_patents)
            
            page_num += 1
            time.sleep(15)  # Delay between pages
            
        except Exception as e:
            print(f"Error processing page {page_num + 1}: {str(e)}")
            break
    
    return all_patent_links

def getLinks():
    # Initialize the driver with specific ChromeDriver path
    driver = webdriver.Chrome(
        service=Service("/snap/chromium/current/usr/lib/chromium-browser/chromedriver"),
        options=chrome_options
    )
    existing_patents = load_existing_patents()
    print(f"Found {len(existing_patents)} existing patents in {PATENTS_FILE}")
    
    # Load progress
    start_from = load_progress()
    print(f"Resuming scraping from: {start_from.date()}")
    
    total_new_patents = 0
    
    try:
        for start_date, end_date in get_date_chunks():
            # Skip chunks before our resume point
            if start_date < start_from:
                continue
                
            print(f"\nProcessing date chunk: {start_date.date()} to {end_date.date()}")
            
            new_patents = scrape_date_range(driver, start_date, end_date, existing_patents)
            total_new_patents += len(new_patents)
            
            # Save progress after each chunk
            save_progress(end_date)
            
            print(f"Completed chunk. Total patents so far: {len(existing_patents)}")
            
            # Add a delay between chunks to avoid rate limiting
            time.sleep(15)
    
    except KeyboardInterrupt:
        print("\nScraping interrupted by user. Progress has been saved.")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
    finally:
        driver.quit()
        print(f"\nScraping completed or interrupted.")
        print(f"Total new patents found: {total_new_patents}")
        print(f"Total unique patents in {PATENTS_FILE}: {len(existing_patents)}")
        return total_new_patents

if __name__ == "__main__":
    getLinks()

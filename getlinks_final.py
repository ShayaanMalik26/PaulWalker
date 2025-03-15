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

def get_date_range():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=20)
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

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

def getLinks():
    # Get dynamic date range
    start_date, end_date = get_date_range()
    print(f"\nScraping patents from {start_date.date()} to {end_date.date()}")
    
    # Initialize the driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    all_patent_links = []
    page_num = 0
    
    # Load existing patents
    existing_patents = load_existing_patents()
    print(f"Found {len(existing_patents)} existing patents in {PATENTS_FILE}")
    
    try:
        while True:
            # Load the page
            current_url = construct_url(page_num, start_date, end_date)
            print(f"\nFetching page {page_num + 1}")
            print(f"URL: {current_url}")
            
            driver.get(current_url)
            time.sleep(15)  # Wait for content to load
            
            # Get the page source after JavaScript execution
            html_content = driver.page_source
            
            # Use regex to find all patent numbers
            patent_numbers = re.findall(r"US\d{1,11}", html_content)
            
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
            
            # Move to next page
            page_num += 1
            
            # Optional: Add a delay between pages to be respectful to the server
            time.sleep(2)
            
        # Print final summary
        print(f"\nTotal new patents found: {len(all_patent_links)}")
        print(f"Total unique patents in {PATENTS_FILE}: {len(existing_patents)}")
        return all_patent_links

    finally:
        # Always close the driver
        driver.quit()

if __name__ == "__main__":
    getLinks()
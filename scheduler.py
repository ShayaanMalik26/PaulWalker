import schedule
import time
import subprocess
import sys
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

# Set up logging with UTF-8 encoding
logging.basicConfig(
    filename='patent_scraper_scheduler.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    encoding='utf-8'
)

# Load environment variables
load_dotenv()

# Set USER_AGENT if not present
if not os.getenv('USER_AGENT'):
    os.environ['USER_AGENT'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

def run_process_with_output(command, env=None):
    """Run a process and show output in real-time"""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
        env=env
    )
    
    while True:
        output = process.stdout.readline()
        if output:
            print(output.strip())
            logging.info(output.strip())
        if process.poll() is not None:
            break
    
    return process.returncode

def run_scraper():
    try:
        logging.info("Starting patent scraping process...")
        print(f"\n{'='*50}")
        print(f"Running patent scraper at {datetime.now()}")
        print(f"{'='*50}\n")
        
        # Check if IPFS daemon is running
        ipfs_check = subprocess.run(['ipfs', 'id'], capture_output=True)
        if ipfs_check.returncode != 0:
            logging.error("IPFS daemon not running. Starting daemon...")
            print("IPFS daemon not running. Starting daemon...")
            subprocess.Popen(['ipfs', 'daemon'])
            time.sleep(30)  # Wait for daemon to start
        
        # Run getlinks_final.py with real-time output
        print("\nRunning getlinks_final.py to fetch new patents...")
        print(f"{'='*50}")
        getlinks_result = run_process_with_output(
            [sys.executable, 'getlinks_final.py'],
            env=os.environ.copy()
        )
        
        if getlinks_result != 0:
            logging.error("Error running getlinks_final.py")
            print("Error running getlinks_final.py")
            return
            
        # Run working.py with real-time output
        print("\nRunning working.py to process new patents...")
        print(f"{'='*50}")
        working_result = run_process_with_output(
            [sys.executable, 'working.py'],
            env=os.environ.copy()
        )
        
        if working_result == 0:
            logging.info("Patent processing completed successfully")
            print("\nSuccess: Patent processing completed successfully")
        else:
            logging.error("Error processing patents")
            print("\nError processing patents")
            
        print(f"\n{'='*50}")
            
    except Exception as e:
        logging.error(f"Error in scheduler: {str(e)}")
        print(f"\nScheduler error: {str(e)}")
        print(f"{'='*50}\n")

def main():
    print(f"\n{'='*50}")
    print("Patent Scraper Scheduler Starting...")
    print(f"{'='*50}\n")
    logging.info("Scheduler started")
    
    # Schedule the job every 6 hours
    schedule.every(6).hours.do(run_scraper)
    
    # Run immediately on start
    run_scraper()
    
    # Keep the script running and show next run time
    while True:
        next_run = schedule.next_run()
        print(f"\rNext run scheduled for: {next_run}", end='', flush=True)
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main() 
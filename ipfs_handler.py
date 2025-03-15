import requests
import json
import os
from typing import Dict, Any
import logging
from datetime import datetime

class IPFSHandler:
    def __init__(self, ipfs_api_url: str = "http://127.0.0.1:5001/api/v0"):
        self.ipfs_api_url = ipfs_api_url
        self.output_dir = "patent_json"
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        self.logger = self._setup_logger()
        
        # Initialize MFS directory structure
        self.init_mfs_directory()

    def _setup_logger(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename=f'ipfs_handler_{datetime.now().strftime("%Y%m%d")}.log'
        )
        return logging.getLogger(__name__)

    def init_mfs_directory(self):
        """Initialize the MFS directory structure"""
        try:
            # Create /patents directory if it doesn't exist
            mkdir_response = requests.post(
                f"{self.ipfs_api_url}/files/mkdir",
                params={
                    'arg': '/patents',
                    'parents': 'true'
                }
            )
            if mkdir_response.status_code == 200:
                self.logger.info("MFS patents directory initialized")
                print("IPFS patents directory ready")
            else:
                self.logger.warning(f"Failed to create MFS directory: {mkdir_response.text}")
                print("Failed to initialize IPFS directory structure")
        except Exception as e:
            self.logger.error(f"Error initializing MFS directory: {str(e)}")
            print(f"Error setting up IPFS directory structure")

    def add_to_ipfs(self, data: Dict[str, Any]) -> str:
        """
        Add data to IPFS and return the hash
        """
        try:
            # Convert data to JSON string
            json_data = json.dumps(data)
            
            # Prepare the file for IPFS
            files = {
                'file': ('patent.json', json_data)
            }
            
            # Add to IPFS
            response = requests.post(
                f"{self.ipfs_api_url}/add",
                files=files
            )
            
            if response.status_code == 200:
                ipfs_hash = response.json()['Hash']
                self.logger.info(f"Successfully added to IPFS with hash: {ipfs_hash}")
                return ipfs_hash
            else:
                self.logger.error(f"Failed to add to IPFS: {response.text}")
                return ""
                
        except Exception as e:
            self.logger.error(f"Error adding to IPFS: {str(e)}")
            return ""

    def get_from_ipfs(self, ipfs_hash: str) -> Dict[str, Any]:
        """
        Retrieve data from IPFS using the hash
        """
        try:
            response = requests.post(
                f"{self.ipfs_api_url}/cat",
                params={'arg': ipfs_hash}
            )
            
            if response.status_code == 200:
                return json.loads(response.text)
            else:
                self.logger.error(f"Failed to get from IPFS: {response.text}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting from IPFS: {str(e)}")
            return {}

    def save_and_upload(self, patent_data: Dict[str, Any], patent_number: str) -> str:
        """
        Save patent data as JSON and upload to IPFS
        """
        try:
            # Format the data according to the required structure
            formatted_data = {
                "patent_title": patent_data.get('patent_title', ''),
                "abstract": patent_data.get('abstract', ''),
                "inventions": patent_data.get('inventions', []),
                "publication_number": patent_number,
                "filing_date": patent_data.get('filing_date', ''),
                "assignee_name": patent_data.get('assignee_name', ''),
                "inventor_name": patent_data.get('inventor_name', ''),
                "patent_url": patent_data.get('patent_url', ''),
                "patent_text": patent_data.get('patent_text', '')
            }

            # First upload to get the hash
            files = {
                'file': ('patent.json', json.dumps(formatted_data, indent=2))
            }
            
            # Add to IPFS first time to get hash
            response = requests.post(
                f"{self.ipfs_api_url}/add",
                files=files
            )
            
            if response.status_code == 200:
                ipfs_hash = response.json()['Hash']
                
                # Add the hash to the formatted data
                formatted_data["ipfs_hash"] = ipfs_hash
                
                # Upload again with the hash included
                files_with_hash = {
                    'file': ('patent.json', json.dumps(formatted_data, indent=2))
                }
                
                final_response = requests.post(
                    f"{self.ipfs_api_url}/add",
                    files=files_with_hash
                )
                
                if final_response.status_code == 200:
                    final_hash = final_response.json()['Hash']
                    
                    # Save locally
                    json_path = os.path.join(self.output_dir, f"{patent_number}.json")
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(formatted_data, f, indent=2, ensure_ascii=False)
                    
                    # Pin the file
                    pin_response = requests.post(
                        f"{self.ipfs_api_url}/pin/add",
                        params={'arg': final_hash}
                    )
                    
                    # Add to MFS (this will make it visible in WebUI)
                    mfs_path = f"/patents/{patent_number}.json"
                    
                    # First ensure the file doesn't already exist
                    try:
                        requests.post(
                            f"{self.ipfs_api_url}/files/rm",
                            params={'arg': mfs_path, 'force': 'true'}
                        )
                    except:
                        pass  # Ignore if file doesn't exist
                    
                    # Write to MFS using files/write
                    try:
                        json_content = json.dumps(formatted_data, indent=2)
                        
                            # Try alternative method using files/cp
                        print("Trying alternative upload method...")
                        cp_response = requests.post(
                            f"{self.ipfs_api_url}/files/cp",
                            params=[
                                ('arg', f"/ipfs/{final_hash}"),
                                ('arg', mfs_path)
                            ]
                        )
                        
                        if cp_response.status_code == 200:
                            print("Successfully added using alternative method")
                        else:
                            print(f"Alternative method also failed: {cp_response.text}")
                    
                    except Exception as e:
                        self.logger.error(f"Error writing to MFS: {str(e)}")
                        print(f"Error during MFS write: {str(e)}")
                    
                    # Verify the file exists in MFS
                    verify_response = requests.post(
                        f"{self.ipfs_api_url}/files/stat",
                        params={'arg': mfs_path}
                    )
                    
                    if verify_response.status_code == 200:
                        print(f"Verified file in MFS: {mfs_path}")
                        print("File details:", verify_response.json())
                    else:
                        print(f"Could not verify file in MFS: {mfs_path}")
                        print("Verification error:", verify_response.text)
                    
                    self.verify_ipfs_upload(final_hash)
                    return final_hash
                
            return ""

        except Exception as e:
            self.logger.error(f"Error in save_and_upload: {str(e)}")
            print(f"Upload error: {str(e)}")
            return ""

    def verify_ipfs_upload(self, ipfs_hash: str) -> bool:
        """
        Verify that a file was successfully uploaded to IPFS
        """
        try:
            # Try to retrieve the file from IPFS
            data = self.get_from_ipfs(ipfs_hash)
            if data:
                self.logger.info(f"Successfully verified IPFS hash: {ipfs_hash}")
                print("\n=== IPFS File Access Information ===")
                print(f"File successfully uploaded to IPFS with hash: {ipfs_hash}")
                print("\nYou can access your file through any of these methods:")
                print(f"1. Local Gateway: http://127.0.0.1:8080/ipfs/{ipfs_hash}")
                print(f"2. Direct Gateway: http://localhost:8080/ipfs/{ipfs_hash}")
                print(f"3. Command Line: ipfs cat /ipfs/{ipfs_hash}")
                print(f"4. WebUI: Files/patents/{data.get('publication_number', 'unknown')}.json")
                
                # # Verify the file is pinned and in MFS
                # pin_check = requests.post(f"{self.ipfs_api_url}/pin/ls", 
                #                         params={'arg': ipfs_hash})
                mfs_check = requests.post(f"{self.ipfs_api_url}/files/ls",
                                        params={'arg': '/patents'})
                
                # if pin_check.status_code == 200:
                #     print("\nFile is pinned locally")
                if mfs_check.status_code == 200:
                    print("File is visible in WebUI")
                
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error verifying IPFS upload: {str(e)}")
            return False 

    def verify_mfs_file(self, patent_number: str) -> bool:
        """Verify file exists in MFS"""
        try:
            mfs_path = f"/patents/{patent_number}.json"
            response = requests.post(
                f"{self.ipfs_api_url}/files/stat",
                params={'arg': mfs_path}
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Error verifying MFS file: {str(e)}")
            return False 
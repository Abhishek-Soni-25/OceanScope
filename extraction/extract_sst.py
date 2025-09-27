import os
import requests
from bs4 import BeautifulSoup
from config.settings import SST_DIR, SST_URL
from utils.downloader import download_file

def fetch_sst_data():
    response = requests.get(SST_URL)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find all .nc files
        links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.nc')]
        if links:
            latest_file = sorted(links)[-1]  # latest file
            url = SST_URL + latest_file
            save_path = os.path.join(SST_DIR, latest_file)
            success, msg = download_file(url, save_path)
            print(msg)
        else:
            print("No SST files found")
    else:
        print(f"Failed to access {SST_URL}")

if __name__ == "__main__":
    fetch_sst_data()

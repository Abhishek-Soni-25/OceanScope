import os
import requests
from bs4 import BeautifulSoup
from config.settings import ARGO_DIR, ARGO_URL
from utils.downloader import download_file

def fetch_argo_data():
    response = requests.get(ARGO_URL)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find all links ending with _prof.nc
        links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('_prof.nc')]
        latest_files = sorted(links)[-5:]  # latest 5 files
        for file_name in latest_files:
            url = ARGO_URL + file_name
            save_path = os.path.join(ARGO_DIR, file_name)
            success, msg = download_file(url, save_path)
            print(msg)
    else:
        print(f"Failed to access {ARGO_URL}")

if __name__ == "__main__":
    fetch_argo_data()

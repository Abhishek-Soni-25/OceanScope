import os
import requests
from bs4 import BeautifulSoup
from config.settings import BGC_DIR, BGC_URL
from utils.downloader import download_file

def fetch_bgc_data(limit=3):
    response = requests.get(BGC_URL)
    if response.status_code != 200:
        print(f"Failed to access {BGC_URL}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    # List all directories
    dirs = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('/')]
    
    target_dirs = []
    
    # Loop until we find 'limit' directories with _Sprof.nc
    for d in sorted(dirs, reverse=True):  # Start from newest
        dir_url = BGC_URL + d
        dir_resp = requests.get(dir_url)
        if dir_resp.status_code != 200:
            continue
        dir_soup = BeautifulSoup(dir_resp.text, 'html.parser')
        
        # Check if _Sprof.nc exists in this directory
        has_sprof = any(a['href'].endswith('_Sprof.nc') for a in dir_soup.find_all('a', href=True))
        if has_sprof:
            target_dirs.append(d)
        if len(target_dirs) >= limit:
            break

    print(f"Found {len(target_dirs)} directories with _Sprof.nc files: {target_dirs}")

    # Download _Sprof.nc from each target directory
    for d in target_dirs:
        dir_url = BGC_URL + d
        dir_resp = requests.get(dir_url)
        if dir_resp.status_code != 200:
            continue
        dir_soup = BeautifulSoup(dir_resp.text, 'html.parser')
        for a in dir_soup.find_all('a', href=True):
            if a['href'].endswith('_Sprof.nc'):
                file_url = dir_url + a['href']
                save_path = os.path.join(BGC_DIR, a['href'])
                success, msg = download_file(file_url, save_path)
                print(msg)

if __name__ == "__main__":
    fetch_bgc_data()

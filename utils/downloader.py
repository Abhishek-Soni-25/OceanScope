import requests
from utils.file_manager import save_file

def download_file(url: str, save_path: str):
    """Download a file from URL and save it."""
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        save_file(save_path, response.content)
        return True, f"Saved to {save_path}"
    else:
        return False, f"Failed to download {url}"

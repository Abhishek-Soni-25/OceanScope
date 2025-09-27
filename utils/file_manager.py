import os

def save_file(file_path: str, content: bytes):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)

def file_exists(file_path: str) -> bool:
    return os.path.exists(file_path)

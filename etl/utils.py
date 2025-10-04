import os
import logging

# Setup logger
def get_logger(log_file="logs/pipeline.log"):
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger("ETL-Pipeline")
    logger.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # Avoid duplicate handlers
    if not logger.handlers:
        logger.addHandler(ch)
        logger.addHandler(fh)

    return logger

def delete_file(file_path: str, logger=None):
    """Delete file safely after processing"""
    try:
        os.remove(file_path)
        if logger:
            logger.info(f"Deleted file: {file_path}")
        else:
            print(f"Deleted file: {file_path}")
    except Exception as e:
        if logger:
            logger.error(f"Could not delete {file_path}: {e}")
        else:
            print(f"Could not delete {file_path}: {e}")

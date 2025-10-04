import os
from pathlib import Path
from etl.data_loader import load_nc_to_db
from etl.utils import get_logger

DATA_PATHS = {
    "argo_data": Path("data/argo"),
    "bgc_data": Path("data/bgc"),
    "sst_data": Path("data/sst")
}

def run_pipeline():
    logger = get_logger()
    logger.info("Starting ETL Pipeline")

    for table_name, folder in DATA_PATHS.items():
        logger.info(f"Scanning {folder} for files...")
        if not folder.exists():
            logger.warning(f"Folder {folder} does not exist, skipping...")
            continue

        for file in folder.glob("*.nc"):
            logger.info(f"Processing {file} for {table_name}")
            load_nc_to_db(str(file), table_name, logger)

    logger.info("ETL Pipeline finished successfully")

if __name__ == "__main__":
    run_pipeline()

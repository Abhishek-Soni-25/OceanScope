# Commands

This folder contains command-line scripts for data management operations.

## Files

### `data_scraper.py`
Main data scraping script that downloads data from:
- Argo Core Data (https://data-argo.ifremer.fr/geo/indian_ocean/)
- BGC Argo Data (https://data-argo.ifremer.fr/dac/incois/)
- Satellite SST Data (https://osi-saf.ifremer.fr/sst/l3c/indian/meteosat/)

### `run_scraper.py`
Example script to run monthly data scraping. Can be scheduled via:
- Windows Task Scheduler
- Linux cron jobs
- Manual execution

### `run_ingestion.py`
Runs the data ingestion pipeline to process downloaded NetCDF files and store them in PostgreSQL database.

## Usage

### Monthly Data Scraping
```bash
cd commands
python run_scraper.py
```

### Data Ingestion
```bash
cd commands
python run_ingestion.py
```

### Custom Scraping
```bash
cd commands
python data_scraper.py --help
```

## Workflow

1. **Scrape**: Download new data files to `../data/` directory
2. **Ingest**: Process files and store in PostgreSQL database
3. **Cleanup**: Local NetCDF files are automatically deleted after successful ingestion

## Notes

- All scripts automatically create the `../data/` directory structure
- Database connection details are configured in `run_ingestion.py`
- Processed files are tracked to avoid re-processing
- Logs are written to `../data_ingestion.log`

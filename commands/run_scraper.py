#!/usr/bin/env python3
"""
Example script to run the OceanScope data scraper.
This can be scheduled to run monthly via Windows Task Scheduler or cron.
"""

from data_scraper import DataScraper
from datetime import datetime, timedelta
import logging

def monthly_scrape():
    """Run monthly data scraping for all sources."""
    
    # Calculate date ranges
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    # For Argo core: get current month's data
    argo_start_year = current_year
    argo_end_year = current_year
    
    # For SST: get last 30 days
    sst_start_date = (now - timedelta(days=30)).strftime('%Y%m%d')
    sst_end_date = now.strftime('%Y%m%d')
    sst_start_year = (now - timedelta(days=30)).year
    sst_end_year = current_year
    
    print(f"Starting monthly scrape for {current_year}-{current_month:02d}")
    print(f"Argo core: {argo_start_year}")
    print(f"BGC: All available folders")
    print(f"SST: {sst_start_date} to {sst_end_date}")
    
    # Initialize scraper
    scraper = DataScraper("data")
    
    # Scrape all sources
    results = scraper.scrape_all(
        argo_years=(argo_start_year, argo_end_year),
        sst_years=(sst_start_year, sst_end_year),
        sst_dates=(sst_start_date, sst_end_date)
    )
    
    # Print summary
    print("\n" + "="*50)
    print("MONTHLY SCRAPING COMPLETE")
    print("="*50)
    total_files = 0
    for source, files in results.items():
        print(f"{source.upper()}: {len(files)} files")
        total_files += len(files)
    
    print(f"TOTAL: {total_files} files downloaded")
    
    return results

if __name__ == "__main__":
    monthly_scrape()

#!/usr/bin/env python3
"""
OceanScope Data Scraper
Downloads data from three sources:
1. Argo Core Data (https://data-argo.ifremer.fr/geo/indian_ocean/)
2. BGC Argo Data (https://data-argo.ifremer.fr/dac/incois/)
3. Satellite SST Data (https://osi-saf.ifremer.fr/sst/l3c/indian/meteosat/)
"""

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
from pathlib import Path
import logging
from typing import List, Dict, Optional
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataScraper:
    """Main scraper class for oceanographic data sources."""
    
    def __init__(self, base_dir: str = "data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.base_dir / "argo_core").mkdir(exist_ok=True)
        (self.base_dir / "bgc").mkdir(exist_ok=True)
        (self.base_dir / "sst").mkdir(exist_ok=True)
        
        # Data source URLs
        self.ARGO_CORE_URL = "https://data-argo.ifremer.fr/geo/indian_ocean/"
        self.BGC_URL = "https://data-argo.ifremer.fr/dac/incois/"
        self.SST_URL = "https://osi-saf.ifremer.fr/sst/l3c/indian/meteosat/"
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Get page content with error handling."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def download_file(self, url: str, filepath: Path) -> bool:
        """Download file with progress tracking."""
        try:
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\rDownloading {filepath.name}: {progress:.1f}%", end='', flush=True)
            
            print(f"\n✅ Downloaded: {filepath.name}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to download {url}: {e}")
            if filepath.exists():
                filepath.unlink()  # Remove partial file
            return False
    
    def scrape_argo_core_data(self, start_year: int = None, end_year: int = None) -> List[str]:
        """Scrape Argo core data from geo/indian_ocean/"""
        logger.info("Starting Argo core data scraping...")
        
        if start_year is None:
            start_year = datetime.now().year
        if end_year is None:
            end_year = datetime.now().year
            
        downloaded_files = []
        
        for year in range(start_year, end_year + 1):
            year_url = f"{self.ARGO_CORE_URL}{year}/"
            soup = self.get_page_content(year_url)
            
            if not soup:
                continue
                
            logger.info(f"Processing year {year}...")
            
            # Find month folders
            month_links = soup.find_all('a', href=True)
            months = [link['href'].strip('/') for link in month_links 
                     if link['href'].strip('/').isdigit() and len(link['href'].strip('/')) == 2]
            
            for month in months:
                month_url = f"{year_url}{month}/"
                month_soup = self.get_page_content(month_url)
                
                if not month_soup:
                    continue
                    
                # Find .nc files
                nc_links = month_soup.find_all('a', href=True)
                nc_files = [link['href'] for link in nc_links 
                           if link['href'].endswith('.nc')]
                
                for nc_file in nc_files:
                    file_url = f"{month_url}{nc_file}"
                    local_path = self.base_dir / "argo_core" / f"{year}" / f"{month}" / nc_file
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if not local_path.exists():
                        if self.download_file(file_url, local_path):
                            downloaded_files.append(str(local_path))
                        time.sleep(1)  # Be respectful to the server
                    else:
                        logger.info(f"File already exists: {local_path}")
        
        logger.info(f"Argo core scraping complete. Downloaded {len(downloaded_files)} files.")
        return downloaded_files
    
    def scrape_bgc_data(self) -> List[str]:
        """Scrape BGC data from dac/incois/ (only folders with _Sprof.nc files)"""
        logger.info("Starting BGC data scraping...")
        
        soup = self.get_page_content(self.BGC_URL)
        if not soup:
            return []
        
        # Extract folder names (float IDs)
        folder_links = soup.find_all('a', href=True)
        folders = [link['href'].strip('/') for link in folder_links 
                  if link['href'].strip('/').isdigit()]
        
        valid_folders = []
        downloaded_files = []
        
        logger.info(f"Found {len(folders)} BGC folders to check...")
        
        for folder in folders:
            folder_url = f"{self.BGC_URL}{folder}/"
            folder_soup = self.get_page_content(folder_url)
            
            if not folder_soup:
                continue
                
            # Check if folder contains _Sprof.nc file
            sprof_files = [link['href'] for link in folder_soup.find_all('a', href=True)
                          if link['href'].endswith('_Sprof.nc')]
            
            if sprof_files:
                valid_folders.append(folder)
                logger.info(f"Found BGC folder with Sprof: {folder}")
                
                # Download the _Sprof.nc file
                for sprof_file in sprof_files:
                    file_url = f"{folder_url}{sprof_file}"
                    local_path = self.base_dir / "bgc" / folder / sprof_file
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if not local_path.exists():
                        if self.download_file(file_url, local_path):
                            downloaded_files.append(str(local_path))
                        time.sleep(1)
                    else:
                        logger.info(f"BGC file already exists: {local_path}")
        
        logger.info(f"BGC scraping complete. Found {len(valid_folders)} valid folders, downloaded {len(downloaded_files)} files.")
        return downloaded_files
    
    def scrape_sst_data(self, start_year: int = None, end_year: int = None, 
                       start_date: str = None, end_date: str = None) -> List[str]:
        """Scrape SST data from osi-saf (year/date/hour.nc structure)"""
        logger.info("Starting SST data scraping...")
        
        if start_year is None:
            start_year = 2024  # SST data starts from 2017, default to recent
        if end_year is None:
            end_year = datetime.now().year
            
        downloaded_files = []
        
        for year in range(start_year, end_year + 1):
            year_url = f"{self.SST_URL}{year}/"
            soup = self.get_page_content(year_url)
            
            if not soup:
                continue
                
            logger.info(f"Processing SST year {year}...")
            
            # Find date folders (YYYYMMDD format)
            date_links = soup.find_all('a', href=True)
            dates = [link['href'].strip('/') for link in date_links 
                    if link['href'].strip('/').isdigit() and len(link['href'].strip('/')) == 8]
            
            for date_str in dates:
                # Parse date and check if within range
                try:
                    date_obj = datetime.strptime(date_str, '%Y%m%d')
                    if start_date and date_obj < datetime.strptime(start_date, '%Y%m%d'):
                        continue
                    if end_date and date_obj > datetime.strptime(end_date, '%Y%m%d'):
                        continue
                except ValueError:
                    continue
                
                date_url = f"{year_url}{date_str}/"
                date_soup = self.get_page_content(date_url)
                
                if not date_soup:
                    continue
                
                # Find hourly .nc files
                nc_links = date_soup.find_all('a', href=True)
                nc_files = [link['href'] for link in nc_links 
                           if link['href'].endswith('.nc')]
                
                for nc_file in nc_files:
                    file_url = f"{date_url}{nc_file}"
                    local_path = self.base_dir / "sst" / f"{year}" / date_str / nc_file
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if not local_path.exists():
                        if self.download_file(file_url, local_path):
                            downloaded_files.append(str(local_path))
                        time.sleep(0.5)  # SST files are smaller, shorter delay
                    else:
                        logger.info(f"SST file already exists: {local_path}")
        
        logger.info(f"SST scraping complete. Downloaded {len(downloaded_files)} files.")
        return downloaded_files
    
    def scrape_all(self, argo_years: tuple = None, sst_years: tuple = None, 
                   sst_dates: tuple = None) -> Dict[str, List[str]]:
        """Scrape all data sources."""
        results = {}
        
        # Scrape Argo core data
        if argo_years:
            results['argo_core'] = self.scrape_argo_core_data(argo_years[0], argo_years[1])
        
        # Scrape BGC data
        results['bgc'] = self.scrape_bgc_data()
        
        # Scrape SST data
        if sst_years:
            results['sst'] = self.scrape_sst_data(
                sst_years[0], sst_years[1], 
                sst_dates[0] if sst_dates else None,
                sst_dates[1] if sst_dates else None
            )
        
        return results

def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description='OceanScope Data Scraper')
    parser.add_argument('--data-dir', default='data', help='Base directory for data storage')
    parser.add_argument('--argo-years', nargs=2, type=int, metavar=('START', 'END'), 
                       help='Argo core data years (e.g., --argo-years 2024 2025)')
    parser.add_argument('--sst-years', nargs=2, type=int, metavar=('START', 'END'),
                       help='SST data years (e.g., --sst-years 2024 2025)')
    parser.add_argument('--sst-dates', nargs=2, metavar=('START', 'END'),
                       help='SST date range in YYYYMMDD format')
    parser.add_argument('--source', choices=['argo', 'bgc', 'sst', 'all'], default='all',
                       help='Data source to scrape')
    
    args = parser.parse_args()
    
    scraper = DataScraper(args.data_dir)
    
    if args.source == 'all':
        results = scraper.scrape_all(args.argo_years, args.sst_years, args.sst_dates)
        
        print("\n" + "="*50)
        print("SCRAPING SUMMARY")
        print("="*50)
        for source, files in results.items():
            print(f"{source.upper()}: {len(files)} files downloaded")
        
    elif args.source == 'argo':
        if args.argo_years:
            results = scraper.scrape_argo_core_data(args.argo_years[0], args.argo_years[1])
            print(f"Argo core: {len(results)} files downloaded")
        else:
            print("Please specify --argo-years for Argo data scraping")
    
    elif args.source == 'bgc':
        results = scraper.scrape_bgc_data()
        print(f"BGC: {len(results)} files downloaded")
    
    elif args.source == 'sst':
        if args.sst_years:
            results = scraper.scrape_sst_data(
                args.sst_years[0], args.sst_years[1],
                args.sst_dates[0] if args.sst_dates else None,
                args.sst_dates[1] if args.sst_dates else None
            )
            print(f"SST: {len(results)} files downloaded")
        else:
            print("Please specify --sst-years for SST data scraping")

if __name__ == "__main__":
    main()

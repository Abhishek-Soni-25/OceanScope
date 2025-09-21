#!/usr/bin/env python3
"""
OceanScope Data Ingestion Pipeline
Processes scraped NetCDF files from data/ folder and ingests into PostgreSQL.
Supports three data sources: Argo Core, BGC, and SST.
Files are deleted after successful ingestion.
"""

import os
import xarray as xr
import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
import logging
from datetime import datetime
from typing import List, Dict, Optional
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataIngestionPipeline:
    """Main ingestion pipeline for oceanographic data."""
    
    def __init__(self, database_url: str, data_dir: str = "data"):
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.data_dir = Path(data_dir)
        
        # Column mappings for each data source
        self.ARGO_CORE_COLS = [
            "PLATFORM_NUMBER", "CYCLE_NUMBER", "N_PROF", "JULD",
            "LATITUDE", "LONGITUDE", "PRES", "TEMP", "PSAL",
            "TEMP_ADJUSTED", "PSAL_ADJUSTED", "PRES_ADJUSTED",
        ]
        
        self.BGC_COLS = [
            "PLATFORM_NUMBER", "CYCLE_NUMBER", "N_PROF", "JULD",
            "LATITUDE", "LONGITUDE", "PRES", "TEMP", "PSAL",
            "DOXY", "CHLA", "BBP700", "CHLA_FLUORESCENCE",
            "DOXY_ADJUSTED", "CHLA_ADJUSTED", "BBP700_ADJUSTED", "CHLA_FLUORESCENCE_ADJUSTED",
        ]
        
        self.SST_COLS = [
            "time", "lat", "lon", "sea_surface_temperature",
            "quality_level", "l2p_flags", "sses_bias", "sses_standard_deviation",
            "wind_speed", "sea_ice_fraction"
        ]
        
        # Ensure tables exist
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        try:
            with self.engine.begin() as conn:
                # Create processed_files table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS processed_files (
                        filename TEXT PRIMARY KEY,
                        data_type TEXT NOT NULL,
                        processed_at TIMESTAMPTZ DEFAULT now(),
                        file_size_bytes BIGINT,
                        records_inserted INT
                    )
                """))
                
                # Create argo_profiles table (without PostGIS for now)
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS argo_profiles (
                        id BIGSERIAL PRIMARY KEY,
                        platform_number TEXT NOT NULL,
                        cycle_number INT,
                        n_prof INT,
                        time TIMESTAMPTZ,
                        lat DOUBLE PRECISION,
                        lon DOUBLE PRECISION,
                        pres DOUBLE PRECISION,
                        temp DOUBLE PRECISION,
                        psal DOUBLE PRECISION,
                        temp_adjusted DOUBLE PRECISION,
                        psal_adjusted DOUBLE PRECISION,
                        pres_adjusted DOUBLE PRECISION,
                        filename TEXT,
                        year INT,
                        month INT,
                        profile_id TEXT GENERATED ALWAYS AS (platform_number || '_' || cycle_number || '_' || n_prof) STORED
                    )
                """))
                
                # Create bgc_profiles table (without PostGIS for now)
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS bgc_profiles (
                        id BIGSERIAL PRIMARY KEY,
                        platform_number TEXT NOT NULL,
                        cycle_number INT,
                        n_prof INT,
                        time TIMESTAMPTZ,
                        lat DOUBLE PRECISION,
                        lon DOUBLE PRECISION,
                        pres DOUBLE PRECISION,
                        temp DOUBLE PRECISION,
                        psal DOUBLE PRECISION,
                        doxy DOUBLE PRECISION,
                        chla DOUBLE PRECISION,
                        bbp700 DOUBLE PRECISION,
                        chla_fluorescence DOUBLE PRECISION,
                        doxy_adjusted DOUBLE PRECISION,
                        chla_adjusted DOUBLE PRECISION,
                        bbp700_adjusted DOUBLE PRECISION,
                        chla_fluorescence_adjusted DOUBLE PRECISION,
                        filename TEXT,
                        year INT,
                        month INT,
                        profile_id TEXT GENERATED ALWAYS AS (platform_number || '_' || cycle_number || '_' || n_prof) STORED
                    )
                """))
                
                # Create sst_data table (without PostGIS for now)
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS sst_data (
                        id BIGSERIAL PRIMARY KEY,
                        sst_time TIMESTAMPTZ,
                        sst_lat DOUBLE PRECISION,
                        sst_lon DOUBLE PRECISION,
                        sst DOUBLE PRECISION,
                        sst_quality INT,
                        sst_flags INT,
                        sst_bias DOUBLE PRECISION,
                        sst_std DOUBLE PRECISION,
                        wind_speed DOUBLE PRECISION,
                        sea_ice_fraction DOUBLE PRECISION,
                        filename TEXT,
                        year INT,
                        month INT,
                        day INT,
                        hour INT
                    )
                """))
                
                # Create basic indexes (without PostGIS)
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_argo_platform ON argo_profiles (platform_number)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_argo_time ON argo_profiles (time)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_argo_lat_lon ON argo_profiles (lat, lon)"))
                
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_bgc_platform ON bgc_profiles (platform_number)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_bgc_time ON bgc_profiles (time)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_bgc_lat_lon ON bgc_profiles (lat, lon)"))
                
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sst_time ON sst_data (sst_time)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sst_lat_lon ON sst_data (sst_lat, sst_lon)"))
                
                logger.info("Database tables created successfully")
                
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def _convert_juld_to_datetime(self, juld_values):
        """Convert Argo JULD values to datetime."""
        try:
            # JULD is days since 1950-01-01
            base_date = pd.Timestamp('1950-01-01')
            return base_date + pd.to_timedelta(juld_values, unit='D')
        except Exception as e:
            logger.warning(f"Error converting JULD to datetime: {e}")
            return None
    
    def _get_processed_files(self) -> set:
        """Get list of already processed files."""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT filename FROM processed_files"))
            return {row[0] for row in result}
    
    def _mark_file_processed(self, filename: str, data_type: str, file_size: int, records_count: int):
        """Mark file as processed in database."""
        with self.engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO processed_files (filename, data_type, file_size_bytes, records_inserted)
                VALUES (:filename, :data_type, :file_size, :records)
                ON CONFLICT (filename) DO NOTHING
            """), {
                "filename": filename,
                "data_type": data_type,
                "file_size": file_size,
                "records": records_count
            })
    
    def process_argo_core_file(self, file_path: Path) -> bool:
        """Process Argo core NetCDF file."""
        try:
            logger.info(f"Processing Argo core file: {file_path.name}")
            
            # Load NetCDF
            ds = xr.open_dataset(file_path)
            
            # Filter to available columns only
            available_cols = [col for col in self.ARGO_CORE_COLS if col in ds.variables]
            if not available_cols:
                logger.error(f"No matching columns found in {file_path.name}")
                return False
            
            # Handle multi-dimensional data properly
            # LATITUDE/LONGITUDE are per-profile, PRES/TEMP/PSAL are per-level
            data_dict = {}
            
            # Add profile-level data (scalars)
            for col in ['LATITUDE', 'LONGITUDE', 'PLATFORM_NUMBER', 'CYCLE_NUMBER', 'N_PROF']:
                if col in ds.variables:
                    data_dict[col.lower()] = ds[col].values
            
            # Add level-level data (arrays) - replicate profile data for each level
            n_profiles = ds.sizes.get('N_PROF', 1)
            n_levels = ds.sizes.get('N_LEVELS', 1)
            
            # Replicate profile-level data for each depth level
            for col in ['LATITUDE', 'LONGITUDE', 'PLATFORM_NUMBER', 'CYCLE_NUMBER', 'N_PROF']:
                if col in ds.variables:
                    col_lower = col.lower()
                    if col_lower in data_dict:
                        # Replicate each profile value for all its depth levels
                        replicated = []
                        for i in range(n_profiles):
                            replicated.extend([data_dict[col_lower][i]] * n_levels)
                        data_dict[col_lower] = replicated
            
            # Add level-level data (arrays)
            for col in ['PRES', 'TEMP', 'PSAL', 'TEMP_ADJUSTED', 'PSAL_ADJUSTED', 'PRES_ADJUSTED']:
                if col in ds.variables:
                    data_dict[col.lower()] = ds[col].values.flatten()
            
            # Handle JULD separately
            if 'JULD' in ds.variables:
                juld_values = ds['JULD'].values
                if juld_values.ndim == 1:
                    # Replicate JULD for each level
                    juld_repeated = []
                    for i, juld_val in enumerate(juld_values):
                        juld_repeated.extend([juld_val] * n_levels)
                    data_dict['juld'] = juld_repeated
                else:
                    data_dict['juld'] = juld_values.flatten()
            
            # Create DataFrame
            df = pd.DataFrame(data_dict)
            
            # Convert JULD to datetime (handle both numeric and datetime JULD)
            if 'juld' in df.columns:
                if df['juld'].dtype == 'object' or 'datetime' in str(df['juld'].dtype):
                    # JULD is already datetime
                    df['time'] = pd.to_datetime(df['juld'])
                else:
                    # JULD is numeric (days since 1950-01-01)
                    df['time'] = self._convert_juld_to_datetime(df['juld'])
                df = df.drop('juld', axis=1)
            
            # Extract metadata from filename (e.g., 20250101_prof.nc)
            filename = file_path.name
            base = os.path.splitext(filename)[0]  # "20250101_prof"
            year = int(base[:4])
            month = int(base[4:6])
            
            # Add metadata columns
            df['filename'] = filename
            df['year'] = year
            df['month'] = month
            
            # Clean data - remove NaN rows and validate coordinates
            df = df.dropna(subset=['latitude', 'longitude', 'pres'])
            
            # Validate coordinate ranges
            df = df[(df['latitude'] >= -90) & (df['latitude'] <= 90)]
            df = df[(df['longitude'] >= -180) & (df['longitude'] <= 180)]
            df = df[df['pres'] >= 0]  # Pressure should be positive
            
            if df.empty:
                logger.warning(f"No valid data in {file_path.name}")
                return False
            
            # Ensure data types are correct
            numeric_cols = ['latitude', 'longitude', 'pres', 'temp', 'psal', 'temp_adjusted', 'psal_adjusted', 'pres_adjusted']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove any rows that became NaN after conversion
            df = df.dropna(subset=['latitude', 'longitude', 'pres'])
            
            if df.empty:
                logger.warning(f"No valid numeric data in {file_path.name}")
                return False
            
            # Rename columns to match database schema
            df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
            
            # Insert into database
            df.to_sql("argo_profiles", self.engine, if_exists="append", index=False)
            
            # Mark as processed
            file_size = file_path.stat().st_size
            self._mark_file_processed(filename, "argo_core", file_size, len(df))
            
            logger.info(f"[SUCCESS] Processed {file_path.name}: {len(df)} records")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error processing Argo core file {file_path.name}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def process_bgc_file(self, file_path: Path) -> bool:
        """Process BGC NetCDF file."""
        try:
            logger.info(f"Processing BGC file: {file_path.name}")
            
            # Load NetCDF
            ds = xr.open_dataset(file_path)
            
            # Filter to available columns only
            available_cols = [col for col in self.BGC_COLS if col in ds.variables]
            if not available_cols:
                logger.error(f"No matching columns found in {file_path.name}")
                return False
            
            # Handle multi-dimensional data properly
            # LATITUDE/LONGITUDE are per-profile, PRES/TEMP/PSAL are per-level
            data_dict = {}
            
            # Add profile-level data (scalars)
            for col in ['LATITUDE', 'LONGITUDE', 'PLATFORM_NUMBER', 'CYCLE_NUMBER', 'N_PROF']:
                if col in ds.variables:
                    data_dict[col.lower()] = ds[col].values
            
            # Add level-level data (arrays) - replicate profile data for each level
            n_profiles = ds.sizes.get('N_PROF', 1)
            n_levels = ds.sizes.get('N_LEVELS', 1)
            
            # Replicate profile-level data for each depth level
            for col in ['LATITUDE', 'LONGITUDE', 'PLATFORM_NUMBER', 'CYCLE_NUMBER', 'N_PROF']:
                if col in ds.variables:
                    col_lower = col.lower()
                    if col_lower in data_dict:
                        # Replicate each profile value for all its depth levels
                        replicated = []
                        for i in range(n_profiles):
                            replicated.extend([data_dict[col_lower][i]] * n_levels)
                        data_dict[col_lower] = replicated
            
            # Add level-level data (arrays)
            for col in ['PRES', 'TEMP', 'PSAL', 'DOXY', 'CHLA', 'BBP700', 'CHLA_FLUORESCENCE', 
                       'TEMP_ADJUSTED', 'PSAL_ADJUSTED', 'DOXY_ADJUSTED', 'CHLA_ADJUSTED', 
                       'BBP700_ADJUSTED', 'CHLA_FLUORESCENCE_ADJUSTED']:
                if col in ds.variables:
                    data_dict[col.lower()] = ds[col].values.flatten()
            
            # Handle JULD separately
            if 'JULD' in ds.variables:
                juld_values = ds['JULD'].values
                if juld_values.ndim == 1:
                    # Replicate JULD for each level
                    juld_repeated = []
                    for i, juld_val in enumerate(juld_values):
                        juld_repeated.extend([juld_val] * n_levels)
                    data_dict['juld'] = juld_repeated
                else:
                    data_dict['juld'] = juld_values.flatten()
            
            # Create DataFrame
            df = pd.DataFrame(data_dict)
            
            # Convert JULD to datetime (handle both numeric and datetime JULD)
            if 'juld' in df.columns:
                if df['juld'].dtype == 'object' or 'datetime' in str(df['juld'].dtype):
                    # JULD is already datetime
                    df['time'] = pd.to_datetime(df['juld'])
                else:
                    # JULD is numeric (days since 1950-01-01)
                    df['time'] = self._convert_juld_to_datetime(df['juld'])
                df = df.drop('juld', axis=1)
            
            # Extract metadata from filename (e.g., 7901136_Sprof.nc)
            filename = file_path.name
            platform_number = filename.split('_')[0]
            
            # Add metadata columns
            df['filename'] = filename
            df['year'] = datetime.now().year  # BGC files don't have date in filename
            df['month'] = datetime.now().month
            
            # Clean data - remove NaN rows and validate coordinates
            df = df.dropna(subset=['latitude', 'longitude', 'pres'])
            
            # Validate coordinate ranges
            df = df[(df['latitude'] >= -90) & (df['latitude'] <= 90)]
            df = df[(df['longitude'] >= -180) & (df['longitude'] <= 180)]
            df = df[df['pres'] >= 0]  # Pressure should be positive
            
            if df.empty:
                logger.warning(f"No valid data in {file_path.name}")
                return False
            
            # Ensure data types are correct
            numeric_cols = ['latitude', 'longitude', 'pres', 'temp', 'psal', 'doxy', 'chla', 'bbp700', 'chla_fluorescence']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove any rows that became NaN after conversion
            df = df.dropna(subset=['latitude', 'longitude', 'pres'])
            
            if df.empty:
                logger.warning(f"No valid numeric data in {file_path.name}")
                return False
            
            # Rename columns to match database schema
            df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
            
            # Insert into database
            df.to_sql("bgc_profiles", self.engine, if_exists="append", index=False)
            
            # Mark as processed
            file_size = file_path.stat().st_size
            self._mark_file_processed(filename, "bgc", file_size, len(df))
            
            logger.info(f"[SUCCESS] Processed {file_path.name}: {len(df)} records")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error processing BGC file {file_path.name}: {e}")
            return False
    
    def process_sst_file(self, file_path: Path) -> bool:
        """Process SST NetCDF file."""
        try:
            logger.info(f"Processing SST file: {file_path.name}")
            
            # Load NetCDF
            ds = xr.open_dataset(file_path)
            
            # Filter to available columns only
            available_cols = [col for col in self.SST_COLS if col in ds.variables]
            if not available_cols:
                logger.error(f"No matching columns found in {file_path.name}")
                return False
            
            df = ds[available_cols].to_dataframe().reset_index()
            df.columns = [c.lower() for c in df.columns]
            
            # Rename columns to match database schema
            column_mapping = {
                'time': 'sst_time',
                'lat': 'sst_lat',
                'lon': 'sst_lon',
                'sea_surface_temperature': 'sst',
                'quality_level': 'sst_quality',
                'l2p_flags': 'sst_flags',
                'sses_bias': 'sst_bias',
                'sses_standard_deviation': 'sst_std'
            }
            df = df.rename(columns=column_mapping)
            
            # Extract metadata from filename (e.g., 20250921000000-OSISAF-L3C_GHRSST-SSTsubskin-SEVIRI_IO_SST-ssteqc_meteosat09_20250921_000000-v02.0-fv01.0.nc)
            filename = file_path.name
            try:
                # Extract date and time from filename
                date_part = filename[:8]  # 20250921
                time_part = filename[8:14]  # 000000
                
                year = int(date_part[:4])
                month = int(date_part[4:6])
                day = int(date_part[6:8])
                hour = int(time_part[:2])
                
                df['filename'] = filename
                df['year'] = year
                df['month'] = month
                df['day'] = day
                df['hour'] = hour
                
            except (ValueError, IndexError):
                logger.warning(f"Could not parse date from filename: {filename}")
                df['filename'] = filename
                df['year'] = datetime.now().year
                df['month'] = datetime.now().month
                df['day'] = datetime.now().day
                df['hour'] = 0
            
            # Clean data - remove NaN rows
            df = df.dropna(subset=['sst_lat', 'sst_lon', 'sst'])
            
            if df.empty:
                logger.warning(f"No valid data in {file_path.name}")
                return False
            
            # Insert into database
            df.to_sql("sst_data", self.engine, if_exists="append", index=False)
            
            # Mark as processed
            file_size = file_path.stat().st_size
            self._mark_file_processed(filename, "sst", file_size, len(df))
            
            logger.info(f"[SUCCESS] Processed {file_path.name}: {len(df)} records")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error processing SST file {file_path.name}: {e}")
            return False
    
    def process_data_source(self, data_type: str) -> Dict[str, int]:
        """Process all files for a specific data source."""
        processed_files = self._get_processed_files()
        stats = {"processed": 0, "skipped": 0, "errors": 0}
        
        if data_type == "argo_core":
            source_dir = self.data_dir / "argo_core"
            if not source_dir.exists():
                logger.warning("Argo core data directory not found")
                return stats
            
            # Find all .nc files recursively
            nc_files = list(source_dir.rglob("*.nc"))
            
            for file_path in nc_files:
                if file_path.name in processed_files:
                    logger.info(f"[SKIP] Skipping {file_path.name}, already processed")
                    stats["skipped"] += 1
                    continue
                
                if self.process_argo_core_file(file_path):
                    stats["processed"] += 1
                    # Delete file after successful processing
                    file_path.unlink()
                    logger.info(f"[DELETED] Deleted {file_path.name}")
                else:
                    stats["errors"] += 1
        
        elif data_type == "bgc":
            source_dir = self.data_dir / "bgc"
            if not source_dir.exists():
                logger.warning("BGC data directory not found")
                return stats
            
            # Find all _Sprof.nc files recursively
            sprof_files = list(source_dir.rglob("*_Sprof.nc"))
            
            for file_path in sprof_files:
                if file_path.name in processed_files:
                    logger.info(f"[SKIP] Skipping {file_path.name}, already processed")
                    stats["skipped"] += 1
                    continue
                
                if self.process_bgc_file(file_path):
                    stats["processed"] += 1
                    # Delete file after successful processing
                    file_path.unlink()
                    logger.info(f"[DELETED] Deleted {file_path.name}")
                else:
                    stats["errors"] += 1
        
        elif data_type == "sst":
            source_dir = self.data_dir / "sst"
            if not source_dir.exists():
                logger.warning("SST data directory not found")
                return stats
            
            # Find all .nc files recursively
            nc_files = list(source_dir.rglob("*.nc"))
            
            for file_path in nc_files:
                if file_path.name in processed_files:
                    logger.info(f"[SKIP] Skipping {file_path.name}, already processed")
                    stats["skipped"] += 1
                    continue
                
                if self.process_sst_file(file_path):
                    stats["processed"] += 1
                    # Delete file after successful processing
                    file_path.unlink()
                    logger.info(f"[DELETED] Deleted {file_path.name}")
                else:
                    stats["errors"] += 1
        
        return stats
    
    def process_all(self) -> Dict[str, Dict[str, int]]:
        """Process all data sources."""
        logger.info("Starting data ingestion pipeline...")
        
        results = {}
        data_sources = ["argo_core", "bgc", "sst"]
        
        for source in data_sources:
            logger.info(f"Processing {source} data...")
            results[source] = self.process_data_source(source)
        
        # Print summary
        print("\n" + "="*60)
        print("DATA INGESTION SUMMARY")
        print("="*60)
        
        total_processed = 0
        total_skipped = 0
        total_errors = 0
        
        for source, stats in results.items():
            print(f"{source.upper()}:")
            print(f"  Processed: {stats['processed']} files")
            print(f"  Skipped: {stats['skipped']} files")
            print(f"  Errors: {stats['errors']} files")
            print()
            
            total_processed += stats['processed']
            total_skipped += stats['skipped']
            total_errors += stats['errors']
        
        print(f"TOTAL:")
        print(f"  Processed: {total_processed} files")
        print(f"  Skipped: {total_skipped} files")
        print(f"  Errors: {total_errors} files")
        
        return results

def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description='OceanScope Data Ingestion Pipeline')
    parser.add_argument('--database-url', 
                       default='postgresql+psycopg2://postgres:soni12341234@localhost:5432/oceanscope',
                       help='Database connection URL')
    parser.add_argument('--data-dir', default='data', help='Data directory path')
    parser.add_argument('--source', choices=['argo_core', 'bgc', 'sst', 'all'], default='all',
                       help='Data source to process')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = DataIngestionPipeline(args.database_url, args.data_dir)
    
    if args.source == 'all':
        results = pipeline.process_all()
    else:
        results = {args.source: pipeline.process_data_source(args.source)}
        
        print(f"\n{args.source.upper()} Processing Complete:")
        stats = results[args.source]
        print(f"  Processed: {stats['processed']} files")
        print(f"  Skipped: {stats['skipped']} files")
        print(f"  Errors: {stats['errors']} files")

if __name__ == "__main__":
    main()

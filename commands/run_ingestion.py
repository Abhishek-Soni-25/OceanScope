#!/usr/bin/env python3
"""
OceanScope Data Ingestion Runner
Simple script to run the data ingestion pipeline after scraping.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_ingestion import DataIngestionPipeline
import logging

def run_ingestion():
    """Run the complete data ingestion pipeline."""
    
    # Database connection (update with your credentials)
    DATABASE_URL = "postgresql+psycopg2://postgres:soni12341234@localhost:5432/oceanscope"
    
    # Initialize pipeline
    pipeline = DataIngestionPipeline(DATABASE_URL, "data")
    
    # Process all data sources
    results = pipeline.process_all()
    
    # Check if any files were processed
    total_processed = sum(stats['processed'] for stats in results.values())
    
    if total_processed > 0:
        print(f"\n🎉 Successfully processed {total_processed} files!")
        print("All processed files have been deleted from local storage.")
    else:
        print("\n📝 No new files to process.")
    
    return results

if __name__ == "__main__":
    run_ingestion()

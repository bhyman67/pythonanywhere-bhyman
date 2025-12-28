"""
Garmin Connect Activities Ingestion Script

This script fetches activity data from Garmin Connect API and either:
1. Writes the data to a MySQL database (default behavior)
2. Generates a schema analysis file for DDL creation (with --schema-only flag)

USAGE:
------
Default mode (fetch activities and write to database):
    python "01 - Ingest Garmin Connect Activities.py"

Schema generation mode (fetch activities and generate schema analysis only):
    python "01 - Ingest Garmin Connect Activities.py" --schema-only

REQUIREMENTS:
-------------
- Environment variables: GARMIN_EMAIL and GARMIN_PASSWORD must be set
- Database connection configured via db_connection module (for default mode)
- Required packages: sqlalchemy, pandas, garminconnect

OUTPUT:
-------
- Default mode: Writes activities to ingested_garmin_connect_activities table
- Schema mode: Creates activities_schema_analysis.txt in the current directory
"""

from sqlalchemy import text
import pandas as pd
import json
import sys
import os
import argparse

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectTooManyRequestsError,
    GarminConnectConnectionError
)

# ============================================================================
# CLI ARGUMENTS: Parse command line arguments
# ============================================================================
parser = argparse.ArgumentParser(description='Ingest Garmin Connect activities')
parser.add_argument('--schema-only', action='store_true',
                    help='Generate schema analysis file only, do not write to database')
args = parser.parse_args()

# ============================================================================
# SETUP: Add parent directory to path for custom db_connection module import
# ============================================================================
# Handle both script execution and interactive sessions
try:
    # When running as a script, __file__ is defined
    parent_dir = os.path.dirname(os.path.dirname(__file__))
except NameError:
    # When running interactively, use current working directory as parent
    parent_dir = os.path.dirname(os.getcwd())

sys.path.insert(0, parent_dir)
from db_connection import is_database_available, get_db_engine

# ============================================================================
# AUTHENTICATION: Setup Garmin Connect credentials and login
# ============================================================================
# Get credentials from environment variables
username = os.getenv('GARMIN_EMAIL')
password = os.getenv('GARMIN_PASSWORD')
print("Using environment variables for Garmin Connect authentication")

# Login to Garmin Connect
try:
    client = Garmin(username, password)
    client.login()
    print("Login successful!")
except GarminConnectAuthenticationError:
    print("Authentication error. Check your credentials.")
except GarminConnectTooManyRequestsError:
    print("Too many requests. Try again later.")
except GarminConnectConnectionError:
    print("Connection error. Check your internet connection.")

# ============================================================================
# DATA EXTRACTION: Retrieve activities from Garmin Connect Python Wrapper API
# ============================================================================
# Fetch up to 5,000 activities in batches of 1,000 (API limitation)
all_activities = []
batch_size = 1000
num_batches = 5

for i in range(num_batches):
    start_index = i * batch_size
    print(f"Fetching activities {start_index} to {start_index + batch_size - 1}...")
    try:
        batch_activities = client.get_activities(start_index, batch_size)
        all_activities.extend(batch_activities)
        print(f"Retrieved {len(batch_activities)} activities in batch {i+1}")
    except Exception as e:
        print(f"Error fetching batch {i+1}: {e}")
        break

print(f"Total activities retrieved: {len(all_activities)}")
activities_df = pd.DataFrame(all_activities)

# ============================================================================
# DATA TRANSFORMATION: Convert complex types to JSON strings
# ============================================================================
# Convert dict/list columns to JSON strings to avoid insertion errors
for col in activities_df.columns:
    if activities_df[col].apply(lambda x: isinstance(x, (dict, list))).any():
        activities_df[col] = activities_df[col].apply(
            lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x
        )

# ============================================================================
# SCHEMA INSPECTION: Analyze dataframe structure for DDL generation
# ============================================================================
if args.schema_only:
    output_file = "activities_schema_analysis.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("DATAFRAME STRUCTURE ANALYSIS\n")
        f.write("="*80 + "\n\n")
        f.write(f"Shape: {activities_df.shape}\n")
        f.write(f"Total Rows: {len(activities_df)}\n")
        f.write(f"Total Columns: {len(activities_df.columns)}\n\n")
        
        f.write("="*80 + "\n")
        f.write("COLUMN DATA TYPES\n")
        f.write("="*80 + "\n")
        f.write(str(activities_df.dtypes) + "\n\n")
        
        f.write("="*80 + "\n")
        f.write("DETAILED COLUMN ANALYSIS\n")
        f.write("="*80 + "\n\n")
        
        if len(activities_df) > 0:
            for col in activities_df.columns:
                f.write(f"\n{'='*80}\n")
                f.write(f"Column: {col}\n")
                f.write(f"{'='*80}\n")
                
                # Data type info
                sample_value = activities_df[col].iloc[0]
                value_type = type(sample_value).__name__
                f.write(f"Python Type: {value_type}\n")
                f.write(f"Pandas dtype: {activities_df[col].dtype}\n")
                
                # Null count
                null_count = activities_df[col].isnull().sum()
                f.write(f"Null Count: {null_count} ({null_count/len(activities_df)*100:.2f}%)\n")
                
                # Type-specific analysis
                if value_type in ['dict', 'list']:
                    f.write(f"Complex Type: {value_type}\n")
                    f.write(f"Sample Value:\n{json.dumps(sample_value, indent=2)}\n")
                elif value_type == 'str':
                    max_len = activities_df[col].astype(str).str.len().max()
                    f.write(f"Max Length: {max_len}\n")
                    f.write(f"Sample Value: {sample_value}\n")
                else:
                    f.write(f"Sample Value: {sample_value}\n")
                
                # Show a few unique values if reasonable
                unique_count = activities_df[col].nunique()
                f.write(f"Unique Values: {unique_count}\n")
                if unique_count <= 20 and value_type not in ['dict', 'list']:
                    f.write(f"Unique Values List: {list(activities_df[col].unique())}\n")
    
    print(f"\nSchema analysis written to: {output_file}")
    print("Exiting without writing to database (--schema-only flag was used)")
    sys.exit(0)

# ============================================================================
# DATABASE WRITE: Connect to MySQL database and write data
# ============================================================================
# Connect to MySQL database and write data
try:
    # Get database engine from shared module
    engine = get_db_engine()
    
    # Truncate the table before inserting new data
    with engine.begin() as connection:
        connection.execute(text('TRUNCATE TABLE ingested_garmin_connect_activities'))
        print("Table truncated successfully")
    
    # Write DataFrame to MySQL table
    activities_df.to_sql(
        name='ingested_garmin_connect_activities',
        con=engine,
        if_exists='append',
        index=False,
        chunksize=1000
    )
    
    print(f"Successfully wrote {len(activities_df)} records to MySQL database")
    
except Exception as e:
    print(f"Error writing to database: {e}")
    raise
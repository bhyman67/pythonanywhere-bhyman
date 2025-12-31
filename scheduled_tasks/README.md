# Garmin Connect ETL Pipeline - Scheduled Tasks

Automated ETL (Extract, Transform, Load) pipeline for ingesting Garmin Connect fitness activity data and loading it into a MySQL database for analysis and API consumption.

## Overview

This folder contains two sequential Python scripts that form a complete data pipeline:

1. **01 - Ingest Garmin Connect Activities.py**: Extracts raw activity data from Garmin Connect API
2. **02 - Transform and Load Garmin Activities.py**: Transforms and loads data into the analytics-ready table

Together, these scripts enable automated, scheduled data synchronization from Garmin Connect to a local database, supporting analytics, dashboards, and OData API endpoints.

## Pipeline Architecture

```
┌─────────────────────┐
│  Garmin Connect API │
└──────────┬──────────┘
           │ (Script 01: Ingest)
           ▼
┌──────────────────────────────────┐
│ ingested_garmin_connect_activities│
│      (Raw staging table)         │
└──────────┬───────────────────────┘
           │ (Script 02: Transform)
           ▼
┌──────────────────────────────────┐
│   garmin_connect_activities      │
│   (Clean analytics table)        │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  OData API / Analytics Tools     │
└──────────────────────────────────┘
```

## Scripts

### 1. Ingest Garmin Connect Activities (`01 - Ingest Garmin Connect Activities.py`)

**Purpose**: Fetches raw activity data from Garmin Connect and writes to staging database table.

**Features**:
- Authenticates with Garmin Connect API using environment credentials
- Fetches up to 5,000 activities in batches (API pagination limit: 1,000 per request)
- Converts complex data types (dicts/lists) to JSON strings for database compatibility
- Truncates staging table before loading fresh data
- Optional schema analysis mode for DDL generation

**Usage**:

```bash
# Standard mode: Fetch and load data to database
python "01 - Ingest Garmin Connect Activities.py"

# Schema analysis mode: Generate schema documentation without database write
python "01 - Ingest Garmin Connect Activities.py" --schema-only
```

**Environment Variables Required**:
```bash
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_password
```

**Database Table**: `ingested_garmin_connect_activities` (staging table)

**Output**:
- Standard mode: Writes to database and logs record count
- Schema mode: Creates `activities_schema_analysis.txt` with detailed schema information

**Key Functions**:
- Batch processing with error handling for network issues
- Automatic JSON serialization for nested data structures
- Full truncate-and-reload pattern for data freshness

---

### 2. Transform and Load Garmin Activities (`02 - Transform and Load Garmin Activities.py`)

**Purpose**: Transforms raw activity data and loads it into the analytics-ready table.

**Features**:
- Reads from staging table (`ingested_garmin_connect_activities`)
- Parses JSON string columns back to Python objects
- Applies comprehensive data transformations
- Enriches data with calculated metrics
- Writes to final analytics table

**Usage**:

```bash
python "02 - Transform and Load Garmin Activities.py"
```

**Database Tables**:
- **Input**: `ingested_garmin_connect_activities` (raw staging data)
- **Output**: `garmin_connect_activities` (transformed analytics data)

**Transformations Applied**:

#### Time Conversions
- Converts seconds to `HH:MM:SS.sss` format for duration fields
- Fields: `duration`, `elapsedDuration`, `movingDuration`

#### Unit Conversions
- **Distance**: Meters → Miles (× 0.000621371)
- **Temperature**: Celsius → Fahrenheit (× 9/5 + 32)
- **Weight/Volume**: Grams → Pounds (× 0.00220462)

#### Data Formatting
- **Activity Type**: Snake_case → Title Case (`running_treadmill` → `Running Treadmill`)
- **Complex Fields**: Extracts key values from nested JSON objects
  - `activityType`: Extracts `typeKey` property
  - `privacy`: Extracts `typeKey` property

#### Data Enrichment
- **Strength Training Metrics**:
  - Calculates average weight per rep from exercise sets
  - Normalizes exercise set data from JSON arrays
  - Extracts first exercise set details into flat columns
- **Dummy Rows**: Adds boundary date records for analytics continuity
  - Start: 2022-01-03
  - End: 2025-12-30

#### Column Renaming
Renames 60+ columns from camelCase API format to descriptive display names:

```python
'activityType' → 'Activity Type'
'distance' → 'Distance (miles)'
'duration' → 'Duration (HH:MM:SS.sss)'
'averageHR' → 'Average HR'
```

**Data Quality**:
- Handles null/NaN values with `fillna(0)` before calculations
- Preserves data types through transformations
- Validates list structures before accessing elements

---

## Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

**requirements.txt**:
```
pandas          # Data manipulation and analysis
sqlalchemy      # Database ORM and connectivity
garminconnect   # Garmin Connect API wrapper
pymysql         # MySQL database driver
```

## Database Configuration

Both scripts use the shared `db_connection` module from the parent directory for database connectivity.

**Module**: `db_connection.py` (located in project root)

**Functions Used**:
- `get_db_engine()`: Returns SQLAlchemy engine for MySQL connection
- `is_database_available()`: Checks database connectivity (optional validation)

**Database Connection Details**: Configured in `db_connection.py` (not in this folder)

## Scheduling & Automation

These scripts are designed to run as scheduled tasks. Recommended scheduling:

### Linux/Mac (cron)
```bash
# Run daily at 2:00 AM
0 2 * * * /usr/bin/python3 /path/to/scheduled_tasks/01\ -\ Ingest\ Garmin\ Connect\ Activities.py
5 2 * * * /usr/bin/python3 /path/to/scheduled_tasks/02\ -\ Transform\ and\ Load\ Garmin\ Activities.py
```

### Windows (Task Scheduler)
1. Create new task: "Garmin Connect Ingest"
2. Trigger: Daily at 2:00 AM
3. Action: Run Python script `01 - Ingest Garmin Connect Activities.py`
4. Create second task: "Garmin Connect Transform"
5. Trigger: Daily at 2:05 AM (5 minutes after ingest)
6. Action: Run Python script `02 - Transform and Load Garmin Activities.py`

### PythonAnywhere (Scheduled Tasks)
```
# Ingest task
02:00 - python3 /home/yourusername/scheduled_tasks/01\ -\ Ingest\ Garmin\ Connect\ Activities.py

# Transform task (5 min delay)
02:05 - python3 /home/yourusername/scheduled_tasks/02\ -\ Transform\ and\ Load\ Garmin\ Activities.py
```

## Execution Flow

### Full Pipeline Run

```bash
# Step 1: Fetch from Garmin Connect API
python "01 - Ingest Garmin Connect Activities.py"

# Output:
# Using environment variables for Garmin Connect authentication
# Login successful!
# Fetching activities 0 to 999...
# Retrieved 1000 activities in batch 1
# Fetching activities 1000 to 1999...
# Retrieved 1000 activities in batch 2
# ...
# Total activities retrieved: 2547
# Table truncated successfully
# Successfully wrote 2547 records to MySQL database

# Step 2: Transform and load analytics data
python "02 - Transform and Load Garmin Activities.py"

# Output:
# Loading activities from database...
# Loaded 2547 activities from ingested_garmin_connect_activities table
# JSON columns parsed successfully
# Table truncated successfully
# Successfully wrote 2549 records to MySQL database
```

## Data Flow Details

### Script 01: Data Extraction

**Input**: Garmin Connect API
- Endpoint: `client.get_activities(start, limit)`
- Authentication: Email/password via `garminconnect` library
- Rate limiting: Handled by batch processing with delays

**Processing**:
1. Login authentication
2. Batch fetching (5 batches × 1,000 records)
3. JSON serialization of complex fields
4. DataFrame construction

**Output**: `ingested_garmin_connect_activities` table
- Format: Raw JSON strings in text columns
- Structure: ~100 columns including nested data

### Script 02: Data Transformation

**Input**: `ingested_garmin_connect_activities` table
- Format: Text fields with JSON strings
- Size: Variable (typically 1,000-5,000 records)

**Processing**:
1. JSON parsing: Deserialize 8 complex columns
2. Time formatting: Convert seconds to timedelta strings
3. Unit conversion: Metric → Imperial units
4. Data enrichment: Calculate derived metrics
5. Normalization: Flatten nested exercise data
6. Column selection: Filter to 60 final columns
7. Renaming: Apply display-friendly column names

**Output**: `garmin_connect_activities` table
- Format: Clean, flat structure with proper data types
- Structure: 60 analytics-ready columns
- Ready for: OData API, Power BI, dashboards

## Schema Analysis Mode

The ingest script includes a schema analysis feature for DDL generation:

```bash
python "01 - Ingest Garmin Connect Activities.py" --schema-only
```

**Output File**: `activities_schema_analysis.txt`

**Contents**:
- DataFrame shape and dimensions
- Column data types (Python and Pandas)
- Null value analysis (count and percentage)
- String length statistics (max length per column)
- Unique value analysis
- Sample values for each column
- Complex type inspection (JSON structures)

**Use Case**: Database schema design and documentation

## Error Handling

Both scripts include robust error handling:

### Authentication Errors
```python
GarminConnectAuthenticationError → "Check your credentials"
GarminConnectTooManyRequestsError → "Try again later"
GarminConnectConnectionError → "Check internet connection"
```

### Database Errors
- Connection failures: Raised with stack trace
- Write errors: Logged and re-raised for visibility
- Truncate errors: Caught in transaction context

### Data Processing Errors
- Missing columns: Handled with conditional checks
- NaN values: Filled with 0 or preserved as None
- Type conversion errors: Caught in apply functions

## Performance Considerations

### Ingest Script (01)
- **API Rate Limiting**: Garmin Connect limits to 1,000 records per request
- **Network**: 5 sequential API calls (~5-30 seconds depending on connection)
- **Database Write**: Bulk insert with 1,000 record chunks
- **Total Runtime**: Typically 1-3 minutes for 5,000 activities

### Transform Script (02)
- **Database Read**: Single SELECT query (fast for typical dataset sizes)
- **JSON Parsing**: Iterative processing (1-2 seconds for 5,000 records)
- **Transformations**: Vectorized pandas operations (very fast)
- **Database Write**: Bulk insert with 1,000 record chunks
- **Total Runtime**: Typically 30-60 seconds

## Monitoring & Logging

Both scripts output progress to stdout/console:

### Key Log Messages
- `Login successful!` - Garmin authentication succeeded
- `Retrieved X activities in batch Y` - API fetch progress
- `Total activities retrieved: X` - Final extraction count
- `Table truncated successfully` - Database cleared
- `Successfully wrote X records to MySQL database` - Final load confirmation
- `Loaded X activities from ingested_garmin_connect_activities table` - Transform input
- `JSON columns parsed successfully` - Deserialization complete

### Error Messages
- Include full stack traces for debugging
- Database connection errors show connection string details
- API errors show specific error type

## Data Dictionary

### Final Table Columns (`garmin_connect_activities`)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Activity Type | String | Type of activity | "Running", "Cycling" |
| Activity Name | String | Custom activity name | "Morning Run" |
| Date | Datetime | Start time (local timezone) | "2025-12-28 06:30:00" |
| Distance (miles) | Float | Distance in miles | 5.2 |
| Duration (HH:MM:SS.sss) | String | Total duration | "00:45:32.000" |
| Calories | Integer | Active calories burned | 450 |
| Average HR | Integer | Average heart rate (bpm) | 145 |
| Max HR | Integer | Maximum heart rate (bpm) | 168 |
| Avg Stride Length | Float | Average stride length | 1.2 |
| Steps | Integer | Total step count | 7850 |
| Aerobic Training Effect | Float | Training effect score (0-5) | 3.2 |
| Elevation Gain - meters | Float | Total elevation gain | 125 |
| Reps | Integer | Total reps (strength training) | 120 |
| Sets | Integer | Total sets (strength training) | 5 |
| Volume | Integer | Total volume in pounds | 5400 |
| Avg Weight Per Rep | Float | Average weight per rep (lbs) | 45 |

*See full schema in OData endpoint metadata or `activities_schema_analysis.txt`*

## Troubleshooting

### "Authentication error. Check your credentials."
- Verify `GARMIN_EMAIL` and `GARMIN_PASSWORD` environment variables
- Check Garmin account status (not locked/suspended)
- Verify credentials work on Garmin Connect website

### "Table doesn't exist" error
- Create staging table: `ingested_garmin_connect_activities`
- Create final table: `garmin_connect_activities`
- Run `--schema-only` mode to generate DDL

### "Too many requests" error
- Garmin API rate limiting activated
- Wait 1 hour before retrying
- Consider reducing batch count or frequency

### Missing data transformations
- Verify Script 01 completed successfully
- Check staging table has data: `SELECT COUNT(*) FROM ingested_garmin_connect_activities`
- Review console output for errors

## Related Components

- **OData API**: [`pythonanywhere-app/garmin_connect_odata_endpoints/`](../pythonanywhere-app/garmin_connect_odata_endpoints/)
- **Database Connection**: [`db_connection.py`](../db_connection.py)
- **Web Server**: [`pythonanywhere-app/server.py`](../pythonanywhere-app/server.py)

## Future Enhancements

Potential improvements for this pipeline:

1. **Incremental Updates**: Only fetch new activities since last run (track last activity date)
2. **Delta Detection**: Compare with existing data and update only changed records
3. **Activity Details**: Fetch detailed GPS, lap, and split data for each activity
4. **Error Retry Logic**: Automatic retry with exponential backoff for transient errors
5. **Notification System**: Email/SMS alerts on pipeline success/failure
6. **Data Validation**: Schema validation and data quality checks
7. **Historical Backfill**: Batch processing for initial large datasets
8. **Configuration File**: Externalize column mappings and transformations to JSON/YAML

## Best Practices

### Running the Pipeline
1. Always run Script 01 before Script 02
2. Allow 5-minute gap between scripts for database writes
3. Monitor logs for successful completion
4. Validate record counts match expectations

### Scheduled Execution
1. Schedule during low-usage hours (2-4 AM)
2. Ensure environment variables are accessible to scheduler
3. Log output to files for troubleshooting: `>> /path/to/logfile.log 2>&1`
4. Set up monitoring/alerting for failures

### Data Management
1. Regularly backup the final analytics table
2. Archive old staging data if needed
3. Monitor database size and add indexes as needed
4. Document any custom transformations

## License

Part of the pythonanywhere-bhyman portfolio project.

## Author

Created as part of a data engineering portfolio demonstrating:
- ETL pipeline development
- API integration (Garmin Connect)
- Data transformation and enrichment
- Scheduled task automation
- Database design and optimization

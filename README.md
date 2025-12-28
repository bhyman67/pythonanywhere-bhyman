<h1>
    <p align="center">PythonAnywhere Portfolio & Data Services</p>
</h1>

<h1></h1>

<p align="center"> <big>Click <a href="https://bhyman.pythonanywhere.com/" target = "_blank">here</a> to view the live site</big> </p>

## Overview

This project is hosted on [PythonAnywhere](https://www.pythonanywhere.com) and serves as a centralized platform for:
- **Data visualization** - Interactive COVID-19 analytics by county
- **OData APIs** - RESTful data endpoints for BI tool integration (Tableau, Power BI, Excel)
- **Scheduled data ingestion and ETL** - Automated Garmin Connect activity tracking
- **MySQL database** - Persistent storage for processed fitness data

---

## Architecture

### Flask Application (`server.py`)
The main web server provides multiple endpoints for different use cases:

#### 1. Portfolio Landing Page
- **Route:** `/`
- **Description:** Homepage showcasing all available projects and data services

#### 2. COVID-19 by County Visualization
- **Route:** `/covid-by-county`
- **Description:** Interactive visualization of COVID-19 case trends by U.S. county
- **Data Source:** [Johns Hopkins CSSE COVID-19 Repository](https://github.com/CSSEGISandData/COVID-19)
- **Features:**
  - State and county selection dropdowns
  - Daily new cases line charts using Plotly
  - Real-time data fetching from GitHub

**Endpoints:**
- `GET /covid-by-county` - Shows the selection form
- `GET /covid-by-county/graph?county={county}&state={state}` - Displays chart for selected location

#### 3. Sample Data OData API
- **Base Route:** `/sample_data/`
- **Description:** OData v4 compliant demo endpoint with sample time-series data
- **Purpose:** Testing OData connections with BI tools

**Endpoints:**
- `GET /sample_data/$metadata` - OData metadata document
- `GET /sample_data/` - Service document
- `GET /sample_data/SampleData` - Sample dataset with OData query support

**Supported OData Parameters:**
- `$select` - Choose specific fields
- `$filter` - Filter data (basic equality)
- `$orderby` - Sort results (asc/desc)
- `$top` - Limit results
- `$skip` - Pagination offset
- `$count` - Include total count

#### 4. Garmin Activities OData API
- **Base Route:** `/garmin_activities/`
- **Description:** OData v4 endpoint serving personal fitness data from Garmin Connect
- **Data Source:** MySQL database populated by scheduled ingestion script

**Endpoints:**
- `GET /garmin_activities/$metadata` - OData metadata document
- `GET /garmin_activities/` - Service document
- `GET /garmin_activities/activities` - Full activities dataset from MySQL

**Data Fields Include:**
- Activity type, name, location, distance, duration
- Heart rate metrics (avg, max)
- Cadence, elevation, speed statistics
- Training effect, calories, steps
- Temperature, stress levels, VO2 max
- And 40+ additional fitness metrics

**Query Features:**
- All standard OData query parameters
- Pagination support (default 1000 records per page)
- `@odata.nextLink` for large datasets

---

## Database Layer

### `db_connection.py`
Centralized database connection module supporting both PythonAnywhere and local development.

**Features:**
- Automatic environment detection (PythonAnywhere vs. local)
- SSH tunnel support for local development
- Environment variable configuration
- Connection pooling via SQLAlchemy

**Environment Variables (PythonAnywhere):**
- `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`

**Environment Variables (Local with SSH):**
- `SSH_HOST`, `SSH_USERNAME`, `SSH_PASSWORD`
- `MYSQL_REMOTE_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`

---

## Scheduled Tasks

### Garmin Connect Activity Ingestion
**Script:** `Scheduled Tasks/Ingest Garmin Connect Activities.py`

**Purpose:** Automated daily sync of Garmin Connect fitness activities to MySQL database

**Features:**
- Authenticates with Garmin Connect API
- Fetches recent activities (configurable date range)
- Processes and normalizes data:
  - Time conversions (seconds → HH:MM:SS)
  - Unit conversions (meters → miles)
  - Weight calculations (volume/reps)
- Upserts data to MySQL (handles duplicates)
- Runs on PythonAnywhere scheduled task system

**Data Pipeline:**
1. Authenticate with Garmin Connect
2. Fetch activities via `garminconnect` library
3. Extract 50+ metrics per activity
4. Transform and clean data
5. Store in `garmin_connect_activities` table
6. Log execution results

---

## Tech Stack

- **Backend:** Flask (Python web framework)
- **Database:** MySQL (PythonAnywhere managed)
- **Data Processing:** Pandas, NumPy
- **Visualization:** Plotly
- **API:** OData v4 (REST)
- **Data Ingestion:** Garmin Connect API (`garminconnect` library)
- **ORM:** SQLAlchemy
- **Hosting:** PythonAnywhere

---

## Installation & Setup

### Requirements
```bash
pip install -r requirements.txt
```

### Environment Configuration
Set environment variables in PythonAnywhere `.bashrc` or local `.env`:
```bash
# Database
export MYSQL_HOST="your-mysql-host"
export MYSQL_USER="your-username"
export MYSQL_PASSWORD="your-password"
export MYSQL_DATABASE="your-database"

# Garmin Connect (for scheduled tasks)
export GARMIN_EMAIL="your-garmin-email"
export GARMIN_PASSWORD="your-garmin-password"
```

### Running Locally
```bash
python server.py
```
Access at `http://localhost:5000`

---

## Usage Examples

### Connecting from Tableau
1. Data → New Data Source → OData
2. Enter server URL: `https://bhyman.pythonanywhere.com/garmin_activities/`
3. Select "Activities" entity
4. Apply filters/aggregations as needed

### Connecting from Power BI
1. Get Data → OData feed
2. URL: `https://bhyman.pythonanywhere.com/garmin_activities/activities`
3. Load data and create visualizations

### Direct API Access
```bash
# Get all activities with count
curl "https://bhyman.pythonanywhere.com/garmin_activities/activities?$count=true&$top=10"

# Filter by activity type
curl "https://bhyman.pythonanywhere.com/sample_data/SampleData?$filter=Date eq '2025-12-20'"

# Select specific fields
curl "https://bhyman.pythonanywhere.com/garmin_activities/activities?$select=Date,ActivityType,DistanceMiles"
```

---

## Project Structure
```
pythonanywhere-bhyman/
├── pythonanywhere-app/          # Flask web application
│   ├── server.py                # Main Flask app with all endpoints
│   ├── requirements.txt         # Python dependencies
│   ├── templates/               # HTML templates
│   │   ├── portfolio.html       # Landing page
│   │   └── covid-by-county.html # COVID visualization
│   └── static/                  # State data files
├── Scheduled Tasks/             # Automation scripts
│   ├── Ingest Garmin Connect Activities.py
│   └── requirements.txt
└── db_connection.py             # Database connection module
```

---

## Future Enhancements
- Add authentication/API keys for OData endpoints
- Implement more advanced OData query features ($expand, $apply)
- Add caching layer for COVID data
- Create dashboards for Garmin data analysis
- Add more fitness data sources (Strava, Apple Health)

---

<p align="right">Click <a href="https://github.com/bhyman67/pythonanywhere-bhyman">here</a> to view this project's repository</p>

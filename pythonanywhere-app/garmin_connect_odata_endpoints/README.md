# Garmin Connect OData Endpoints

A Flask blueprint providing OData v4.0 compliant REST API endpoints for accessing Garmin Connect activity data stored in a MySQL database.

## Overview

This module exposes Garmin fitness activity data through standardized OData endpoints, enabling integration with Tableau, Excel, and other OData-compatible analytics tools. The service provides comprehensive activity metrics including distance, duration, heart rate, calories, elevation, and training effects.

**Live API Endpoint**: [https://bhyman.pythonanywhere.com/garmin_activities/activites](https://bhyman.pythonanywhere.com/garmin_activities/activities)

## Features

- **OData v4.0 Compliance**: Full support for OData protocol specification
- **Rich Activity Metrics**: 60+ data fields per activity including:
  - Basic metrics: activity type, name, date, location, description
  - Performance: distance, speed, duration, pace, elevation gain/loss
  - Health: heart rate (avg/max), calories (active + BMR), respiration rate, stress levels
  - Training: aerobic/anaerobic training effects, VO2 max, training load
  - Activity-specific: running cadence, stride length, steps, swimming reps/sets
- **Advanced Querying**: Support for OData query options:
  - `$select` - Choose specific fields
  - `$orderby` - Sort results (ascending/descending)
  - `$skip` and `$top` - Pagination support
  - `$count` - Get total record count
- **Automatic Pagination**: Default page size of 1,000 records with `@odata.nextLink` for subsequent pages
- **Metadata Discovery**: Service document and metadata endpoints for schema exploration

## API Endpoints

### Service Document
```
GET /garmin_activities/
```
Returns the OData service document listing available entity sets.

**Response Format**: JSON  
**Headers**: `OData-Version: 4.0`

### Metadata Document
```
GET /garmin_activities/$metadata
```
Returns the Entity Data Model (EDM) schema definition in XML format, describing all available properties and their types.

**Response Format**: XML  
**Headers**: `OData-Version: 4.0`

### Activities Collection
```
GET /garmin_activities/activities
```
Returns Garmin activity records from the `garmin_connect_activities` database table.

**Query Parameters** (OData query options):
- `$select=ActivityType,Date,DistanceMiles` - Select specific fields
- `$orderby=Date desc` - Sort by field (add `desc` for descending, `asc` for ascending)
- `$skip=100` - Skip first N records
- `$top=50` - Limit result count
- `$count=true` - Include total count in response

**Example Queries**:
```
# Get recent 10 running activities
/garmin_activities/activities?$filter=ActivityType eq 'Running'&$top=10&$orderby=Date desc

# Get basic metrics for all activities
/garmin_activities/activities?$select=Date,ActivityType,DistanceMiles,Duration,Calories

# Paginate through results
/garmin_activities/activities?$skip=0&$top=100&$count=true
```

## Data Schema

### Entity Type: Activity

Key field: `Date` (string, ISO 8601 format)

**Activity Information**:
- `ActivityType` (string) - Type of activity (e.g., "Running", "Cycling", "Strength Training")
- `ActivityName` (string) - Custom name for the activity
- `LocationName` (string) - Geographic location
- `Description` (string) - Activity description
- `Date` (string) - Activity start date/time (ISO 8601)

**Distance & Duration**:
- `DistanceMiles` (double) - Distance in miles
- `Duration` (string) - Total duration (HH:MM:SS.sss)
- `ElapsedDuration` (string) - Elapsed time (HH:MM:SS.sss)
- `MovingDuration` (string) - Moving time (HH:MM:SS.sss)

**Speed & Elevation**:
- `AverageSpeed` (double) - Average speed
- `MaxSpeed` (double) - Maximum speed
- `ElevationGainMeters` (double) - Elevation gain in meters
- `ElevationLossMeters` (double) - Elevation loss in meters
- `MinElevation` (double) - Minimum elevation
- `MaxElevation` (double) - Maximum elevation
- `AvgVerticalSpeed` (double) - Average vertical speed
- `MaxVerticalSpeed` (double) - Maximum vertical speed

**Health Metrics**:
- `Calories` (double) - Active calories burned
- `BMRCalories` (double) - Basal metabolic rate calories
- `AverageHR` (double) - Average heart rate (bpm)
- `MaxHR` (double) - Maximum heart rate (bpm)
- `MinRespirationRate` (double) - Minimum respiration rate
- `MaxRespirationRate` (double) - Maximum respiration rate
- `AvgRespirationRate` (double) - Average respiration rate

**Stress Metrics**:
- `AvgStress` (double) - Average stress level
- `StartStress` (double) - Starting stress level
- `EndStress` (double) - Ending stress level
- `DifferenceStress` (double) - Change in stress level
- `MaxStress` (double) - Maximum stress level

**Running Metrics**:
- `AverageRunningCadenceInStepsPerMinute` (double) - Average cadence
- `MaxRunningCadenceInStepsPerMinute` (double) - Maximum cadence
- `Steps` (double) - Total step count
- `AvgStrideLength` (double) - Average stride length
- `FastestSplit1000` (double) - Fastest 1000m split time
- `MaxDoubleCadence` (double) - Maximum double cadence

**Training Metrics**:
- `AerobicTrainingEffect` (double) - Aerobic training effect (0.0-5.0)
- `AnaerobicTrainingEffect` (double) - Anaerobic training effect (0.0-5.0)
- `TrainingEffectLabel` (string) - Training effect description
- `AerobicTrainingEffectMessage` (string) - Aerobic effect message
- `AnaerobicTrainingEffectMessage` (string) - Anaerobic effect message
- `ActivityTrainingLoad` (double) - Training load score
- `VO2MaxValue` (double) - VO2 max estimate

**Strength Training**:
- `Reps` (double) - Total repetitions
- `Sets` (double) - Total sets
- `Volume` (double) - Total volume (weight × reps)
- `AvgWeightPerRep` (double) - Average weight per repetition

**Other Metrics**:
- `LapCount` (double) - Number of laps
- `MinActivityLapDuration` (double) - Shortest lap duration
- `ModerateIntensityMinutes` (double) - Moderate intensity time
- `VigorousIntensityMinutes` (double) - Vigorous intensity time
- `WaterEstimated` (double) - Estimated water consumption
- `WaterConsumed` (double) - Actual water consumed
- `CaloriesConsumed` (double) - Calories consumed
- `MinTemperature` (double) - Minimum temperature
- `MaxTemperature` (double) - Maximum temperature

**Flags**:
- `PrivacySetting` (string) - Activity privacy setting
- `PR` (string) - Personal record indicator
- `ManualActivity` (string) - Manual entry indicator

## Integration

### Flask Application Setup

The blueprint is registered in the main Flask application:

```python
from garmin_connect_odata_endpoints.routes import garmin_bp

app = Flask(__name__)
app.register_blueprint(garmin_bp)
```

### Database Connection

This module requires the `db_connection` module from the parent directory to establish database connectivity:

```python
from db_connection import get_db_engine
```

The database engine is used to query the `garmin_connect_activities` table.

## Usage with Tableau

1. **Open Tableau Desktop**
2. **Connect to Data** → **To a Server** → **OData**
3. **Enter Server URL**: `https://bhyman.pythonanywhere.com/garmin_activities/`
4. **Authentication**: None (or configure as needed)
5. **Select**: "Activities" table
6. **Drag to canvas** to start building visualizations

Tableau will automatically detect the schema and load your activity data for analysis and visualization.

## Usage with Excel

1. **Data** tab → **Get Data** → **From Other Sources** → **From OData Feed**
2. **Enter URL**: `https://your-server.com/garmin_activities/`
3. **Select**: "Activities" table
4. **Load** data into worksheet

## Technical Details

### Data Type Handling

The module automatically handles:
- **NaN/None values**: Converted to JSON `null`
- **Pandas timestamps**: Converted to ISO 8601 strings
- **NumPy numeric types**: Converted to native Python types
- **Boolean fields**: Converted to strings for OData compatibility

### Column Mapping

Database column names with spaces and special characters are mapped to OData-compliant property names using PascalCase convention:

```python
"Activity Type" → "ActivityType"
"Distance (miles)" → "DistanceMiles"
"Duration (HH:MM:SS.sss)" → "Duration"
```

### Error Handling

All endpoints include comprehensive error handling with:
- Exception catching and logging
- Stack trace output for debugging
- HTTP 500 status codes with JSON error responses

## Dependencies

- **Flask**: Web framework and blueprint system
- **pandas**: Data manipulation and SQL querying
- **numpy**: Numerical operations and NaN handling
- **SQLAlchemy**: Database connectivity (via `db_connection` module)
- **PyMySQL**: MySQL database driver

## Database Requirements

The module expects a MySQL database table with the following structure:

**Table**: `garmin_connect_activities`

This table is populated by the scheduled ETL pipeline in the `scheduled_tasks` folder.

## Related Components

- **Data Ingestion**: [`scheduled_tasks/01 - Ingest Garmin Connect Activities.py`](../../scheduled_tasks/01%20-%20Ingest%20Garmin%20Connect%20Activities.py)
- **Data Transformation**: [`scheduled_tasks/02 - Transform and Load Garmin Activities.py`](../../scheduled_tasks/02%20-%20Transform%20and%20Load%20Garmin%20Activities.py)
- **Main Server**: [`pythonanywhere-app/server.py`](../server.py)

## Development & Debugging

Enable debug output by checking the console logs:
- Activity count logging: Shows records returned with pagination details
- Error logging: Prints exceptions with full stack traces

Example debug output:
```
Returning 100 records (skip=0, top=100, total=2547)
```

## API Response Format

### Standard Response
```json
{
  "@odata.context": "https://your-server.com/garmin_activities/$metadata#Activities",
  "value": [
    {
      "ActivityType": "Running",
      "ActivityName": "Morning Run",
      "Date": "2025-12-28T06:30:00",
      "DistanceMiles": 5.2,
      "Duration": "00:45:32.000",
      "Calories": 450,
      "AverageHR": 145,
      ...
    }
  ]
}
```

### With Count and Pagination
```json
{
  "@odata.context": "https://your-server.com/garmin_activities/$metadata#Activities",
  "@odata.count": 2547,
  "@odata.nextLink": "https://your-server.com/garmin_activities/activities?$skip=100&$top=100",
  "value": [ ... ]
}
```

## License

Part of the pythonanywhere-bhyman portfolio project.

## Author

Created as part of a data engineering and analytics portfolio demonstrating:
- RESTful API design
- OData protocol implementation
- ETL pipeline development
- Business intelligence integration

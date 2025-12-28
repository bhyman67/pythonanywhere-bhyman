# Garmin Activities OData Endpoints Blueprint
# This project provides OData v4 endpoints for Garmin Connect activity data from MySQL database

import json
import os
import sys
import pandas as pd
import numpy as np
from flask import Blueprint, request, Response

# Add parent directory to path to import db_connection module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from db_connection import get_db_engine

# Create blueprint
garmin_bp = Blueprint('garmin_activities', __name__, url_prefix='/garmin_activities')

@garmin_bp.route("/$metadata")
def metadata():
    """OData v4 metadata document describing the Garmin Activities entity"""
    metadata_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">
  <edmx:DataServices>
    <Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="GarminActivitiesService">
      <EntityType Name="Activity">
        <Key>
          <PropertyRef Name="Date"/>
        </Key>
        <Property Name="ActivityType" Type="Edm.String"/>
        <Property Name="ActivityName" Type="Edm.String"/>
        <Property Name="LocationName" Type="Edm.String"/>
        <Property Name="Description" Type="Edm.String"/>
        <Property Name="Date" Type="Edm.String" Nullable="false"/>
        <Property Name="DistanceMiles" Type="Edm.Double"/>
        <Property Name="Duration" Type="Edm.String"/>
        <Property Name="ElapsedDuration" Type="Edm.String"/>
        <Property Name="MovingDuration" Type="Edm.String"/>
        <Property Name="ElevationGainMeters" Type="Edm.Double"/>
        <Property Name="ElevationLossMeters" Type="Edm.Double"/>
        <Property Name="AverageSpeed" Type="Edm.Double"/>
        <Property Name="MaxSpeed" Type="Edm.Double"/>
        <Property Name="Calories" Type="Edm.Double"/>
        <Property Name="BMRCalories" Type="Edm.Double"/>
        <Property Name="AverageHR" Type="Edm.Double"/>
        <Property Name="MaxHR" Type="Edm.Double"/>
        <Property Name="AverageRunningCadenceInStepsPerMinute" Type="Edm.Double"/>
        <Property Name="MaxRunningCadenceInStepsPerMinute" Type="Edm.Double"/>
        <Property Name="Steps" Type="Edm.Double"/>
        <Property Name="PrivacySetting" Type="Edm.String"/>
        <Property Name="AerobicTrainingEffect" Type="Edm.Double"/>
        <Property Name="AnaerobicTrainingEffect" Type="Edm.Double"/>
        <Property Name="AvgStrideLength" Type="Edm.Double"/>
        <Property Name="MinTemperature" Type="Edm.Double"/>
        <Property Name="MaxTemperature" Type="Edm.Double"/>
        <Property Name="MinElevation" Type="Edm.Double"/>
        <Property Name="MaxElevation" Type="Edm.Double"/>
        <Property Name="MaxDoubleCadence" Type="Edm.Double"/>
        <Property Name="MaxVerticalSpeed" Type="Edm.Double"/>
        <Property Name="LapCount" Type="Edm.Double"/>
        <Property Name="WaterEstimated" Type="Edm.Double"/>
        <Property Name="TrainingEffectLabel" Type="Edm.String"/>
        <Property Name="ActivityTrainingLoad" Type="Edm.Double"/>
        <Property Name="MinActivityLapDuration" Type="Edm.Double"/>
        <Property Name="AerobicTrainingEffectMessage" Type="Edm.String"/>
        <Property Name="AnaerobicTrainingEffectMessage" Type="Edm.String"/>
        <Property Name="ModerateIntensityMinutes" Type="Edm.Double"/>
        <Property Name="VigorousIntensityMinutes" Type="Edm.Double"/>
        <Property Name="FastestSplit1000" Type="Edm.Double"/>
        <Property Name="PR" Type="Edm.String"/>
        <Property Name="ManualActivity" Type="Edm.String"/>
        <Property Name="VO2MaxValue" Type="Edm.Double"/>
        <Property Name="Reps" Type="Edm.Double"/>
        <Property Name="Volume" Type="Edm.Double"/>
        <Property Name="Sets" Type="Edm.Double"/>
        <Property Name="AvgWeightPerRep" Type="Edm.Double"/>
        <Property Name="AvgVerticalSpeed" Type="Edm.Double"/>
        <Property Name="CaloriesConsumed" Type="Edm.Double"/>
        <Property Name="WaterConsumed" Type="Edm.Double"/>
        <Property Name="MinRespirationRate" Type="Edm.Double"/>
        <Property Name="MaxRespirationRate" Type="Edm.Double"/>
        <Property Name="AvgRespirationRate" Type="Edm.Double"/>
        <Property Name="AvgStress" Type="Edm.Double"/>
        <Property Name="StartStress" Type="Edm.Double"/>
        <Property Name="EndStress" Type="Edm.Double"/>
        <Property Name="DifferenceStress" Type="Edm.Double"/>
        <Property Name="MaxStress" Type="Edm.Double"/>
      </EntityType>
      <EntityContainer Name="Container">
        <EntitySet Name="Activities" EntityType="GarminActivitiesService.Activity"/>
      </EntityContainer>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>'''
    return Response(metadata_xml, mimetype='application/xml', headers={'OData-Version': '4.0'})

@garmin_bp.route("/")
def service_doc():
    """OData v4 service document"""
    service_doc = {
        "@odata.context": f"{request.url_root}garmin_activities/$metadata",
        "value": [
            {
                "name": "Activities",
                "kind": "EntitySet",
                "url": "Activities"
            }
        ]
    }
    return Response(
        json.dumps(service_doc),
        mimetype='application/json',
        headers={
            'OData-Version': '4.0',
            'Content-Type': 'application/json; odata.metadata=minimal'
        }
    )

@garmin_bp.route("/activities")
def activities_data():
    """Fetch Garmin activities from MySQL database and return as OData JSON"""
    try:
        # Get database engine
        engine = get_db_engine()
        
        # Query all data from garmin_connect_activities table
        query = "SELECT * FROM garmin_connect_activities"
        df = pd.read_sql(query, engine)
        
        # Replace NaN/None values with None for proper JSON serialization
        df = df.replace({pd.NA: None, pd.NaT: None, np.nan: None})
        
        # Map database column names to OData-compliant property names
        column_mapping = {
            'Activity Type': 'ActivityType',
            'Activity Name': 'ActivityName',
            'Location Name': 'LocationName',
            'Distance (miles)': 'DistanceMiles',
            'Duration (HH:MM:SS.sss)': 'Duration',
            'Elapsed Duration (H:MM:SS.sss)': 'ElapsedDuration',
            'Moving Duration (HH:MM:SS.sss)': 'MovingDuration',
            'Elevation Gain - meters': 'ElevationGainMeters',
            'Elevation Loss - meters': 'ElevationLossMeters',
            'Average Speed': 'AverageSpeed',
            'Max Speed': 'MaxSpeed',
            'BMR Calories': 'BMRCalories',
            'Average HR': 'AverageHR',
            'Max HR': 'MaxHR',
            'Average Running Cadence In Steps Per Minute': 'AverageRunningCadenceInStepsPerMinute',
            'Max Running Cadence In Steps Per Minute': 'MaxRunningCadenceInStepsPerMinute',
            'Privacy Setting': 'PrivacySetting',
            'Aerobic Training Effect': 'AerobicTrainingEffect',
            'Anaerobic Training Effect': 'AnaerobicTrainingEffect',
            'Avg Stride Length': 'AvgStrideLength',
            'Min Temperature': 'MinTemperature',
            'Max Temperature': 'MaxTemperature',
            'Min Elevation': 'MinElevation',
            'Max Elevation': 'MaxElevation',
            'Max Double Cadence': 'MaxDoubleCadence',
            'Max Vertical Speed': 'MaxVerticalSpeed',
            'Lap Count': 'LapCount',
            'Water Estimated': 'WaterEstimated',
            'Training Effect Label': 'TrainingEffectLabel',
            'Activity Training Load': 'ActivityTrainingLoad',
            'Min Activity Lap Duration': 'MinActivityLapDuration',
            'Aerobic Training Effect Message': 'AerobicTrainingEffectMessage',
            'Anaerobic Training Effect Message': 'AnaerobicTrainingEffectMessage',
            'Moderate Intensity Minutes': 'ModerateIntensityMinutes',
            'Vigorous Intensity Minutes': 'VigorousIntensityMinutes',
            'Fastest Split 1000': 'FastestSplit1000',
            'Manual Activity': 'ManualActivity',
            'VO2 Max Value': 'VO2MaxValue',
            'Avg Weight Per Rep': 'AvgWeightPerRep',
            'Avg Vertical Speed': 'AvgVerticalSpeed',
            'Calories Consumed': 'CaloriesConsumed',
            'Water Consumed': 'WaterConsumed',
            'Min Respiration Rate': 'MinRespirationRate',
            'Max Respiration Rate': 'MaxRespirationRate',
            'Avg Respiration Rate': 'AvgRespirationRate',
            'Avg Stress': 'AvgStress',
            'Start Stress': 'StartStress',
            'End Stress': 'EndStress',
            'Difference Stress': 'DifferenceStress',
            'Max Stress': 'MaxStress'
        }
        
        # Rename columns to OData-compliant names
        df = df.rename(columns=column_mapping)
        
        # Convert DataFrame to list of dictionaries
        data = df.to_dict('records')
        
        # Convert any remaining problematic types to strings
        for record in data:
            for key, value in record.items():
                if pd.isna(value) if hasattr(value, '__iter__') and not isinstance(value, str) else value is None:
                    record[key] = None
                elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
                    record[key] = str(value)
                elif isinstance(value, (np.integer, np.floating)):
                    record[key] = value.item()
            
            # Convert Boolean-like fields to strings (PR, ManualActivity)
            if 'PR' in record and record['PR'] is not None:
                record['PR'] = str(record['PR'])
            if 'ManualActivity' in record and record['ManualActivity'] is not None:
                record['ManualActivity'] = str(record['ManualActivity'])
        
        # Apply OData query parameters
        args = request.args
        
        # $select - select specific fields
        if '$select' in args:
            fields = [f.strip() for f in args['$select'].split(',')]
            data = [{k: v for k, v in item.items() if k in fields} for item in data]
        
        # $orderby - sort data
        if '$orderby' in args:
            orderby = args['$orderby']
            reverse = False
            if ' desc' in orderby:
                orderby = orderby.replace(' desc', '').strip()
                reverse = True
            elif ' asc' in orderby:
                orderby = orderby.replace(' asc', '').strip()
            data = sorted(data, key=lambda x: x.get(orderby, ''), reverse=reverse)
        
        # Handle pagination with $skip and $top
        skip = int(args.get('$skip', 0))
        top = int(args.get('$top', 1000))  # Default page size of 1000
        
        # Get total count before pagination
        total_count = len(data)
        
        # Apply skip and top
        data = data[skip:skip + top]
        
        # Build OData response
        odata_response = {
            "@odata.context": f"{request.url_root}garmin_activities/$metadata#Activities"
        }
        
        # Add count if requested
        if '$count' in args and args['$count'].lower() == 'true':
            odata_response["@odata.count"] = total_count
        
        # Add nextLink if there are more records
        if skip + top < total_count:
            next_skip = skip + top
            # Build next link preserving other query parameters
            next_params = dict(args)
            next_params['$skip'] = str(next_skip)
            next_params['$top'] = str(top)
            param_string = '&'.join([f"{k}={v}" for k, v in next_params.items()])
            odata_response["@odata.nextLink"] = f"{request.url}?{param_string}"
        
        odata_response["value"] = data
        
        print(f"Returning {len(data)} records (skip={skip}, top={top}, total={total_count})")  # Debug log
        
        return Response(
            json.dumps(odata_response, default=str),  # default=str handles datetime conversion
            mimetype='application/json',
            headers={
                'OData-Version': '4.0',
                'Content-Type': 'application/json; odata.metadata=minimal'
            }
        )
        
    except Exception as e:
        print(f"Error in garmin_activities endpoint: {str(e)}")  # Debug log
        import traceback
        traceback.print_exc()
        return Response(
            json.dumps({"error": str(e)}),
            status=500,
            mimetype='application/json'
        )

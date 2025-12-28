# Standard Library Imports
import json
import os
import sys
import io

# Add parent directory to path to import db_connection module
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db_connection import get_db_engine, is_database_available

# Needed Libraries
from flask import Flask, render_template, request, Response
import plotly.express as px
from flask import jsonify
import pandas as pd
import numpy as np
import requests
import plotly
from sqlalchemy import text

# pull data
def pull_data():

    url = (
        "https://raw.githubusercontent.com"
        "/CSSEGISandData/COVID-19/master"
        "/csse_covid_19_data/csse_covid_19_time_series"
        "/time_series_covid19_confirmed_US.csv"
    )
    download = requests.get(url).content
    df = pd.read_csv(io.StringIO(download.decode('utf-8')))

    df.drop(columns=["UID","iso2","iso3","code3","FIPS","Country_Region","Lat","Long_"], inplace=True)
    df.rename(columns = {"Admin2":"County","Province_State":"State"}, inplace = True)

    return df

# +++++++++++++++++++++
#      Endpoints
# +++++++++++++++++++++

app = Flask(__name__)

# Portfolio landing page
@app.route("/")
def portfolio_landing_page():
    
    return render_template("portfolio_landing_page.html")

# Covid by County app routes
@app.route("/covid-by-county")
def covid_by_county():

    # Pull the data and list all locations
    df = pull_data()
    locations = df["Combined_Key"].to_list()
    states = list(df["State"].unique())

    # Return covid-by-county.html
    return render_template("covid-by-county.html", states = states, list = locations)

@app.route("/covid-by-county/graph")
def covid_by_county_graph():

    # Pull the data and list all locations
    df = pull_data()
    locations = df["Combined_Key"].to_list()
    states = list(df["State"].unique())

    # Filter data (based off of query string, args is a list of
    # parameters in the query string)
    args = request.args
    county = args["county"] # str(x).lstrip('[').rstrip(']'), where x is a python list
    state = args["state"]
    expr = f"County in ('{county}') and State == '{state}'"
    df.query(expr = expr, inplace = True)
    row_count = len(df.index)

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++

    #          +++++ All of this in a funct +++++

    # Format the dataframe
    df.drop(columns = ["County","State"],inplace = True)
    df = df.T
    new_header = df.iloc[0] # grab the first row for the header
    df = df[1:] # take the data less the header row
    df.columns = new_header # set the header row as the df header

    # Calculate the differences
    for i in range(row_count):

        df.iloc[:,i] = df.iloc[:,i].diff(1)

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # Graph
    fig = px.line(df)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Return template and data
    return render_template("covid-by-county.html", list=locations, states = states, graphJSON=graphJSON)

# OData v4 Metadata endpoint
@app.route("/sample_data/$metadata")
def sample_data_metadata():
    """OData v4 metadata document describing the SampleData entity"""
    metadata_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">
  <edmx:DataServices>
    <Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="SampleDataService">
      <EntityType Name="SampleDataItem">
        <Key>
          <PropertyRef Name="Date"/>
        </Key>
        <Property Name="Date" Type="Edm.String" Nullable="false"/>
        <Property Name="Value" Type="Edm.Int32" Nullable="false"/>
      </EntityType>
      <EntityContainer Name="Container">
        <EntitySet Name="SampleData" EntityType="SampleDataService.SampleDataItem"/>
      </EntityContainer>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>'''
    return Response(metadata_xml, mimetype='application/xml', headers={'OData-Version': '4.0'})

# OData v4 Service Document
@app.route("/sample_data/")
def sample_data_service_doc():
    """OData v4 service document"""
    service_doc = {
        "@odata.context": f"{request.url_root}sample_data/$metadata",
        "value": [
            {
                "name": "SampleData",
                "kind": "EntitySet",
                "url": "SampleData"
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

# OData v4 Data endpoint
@app.route("/sample_data/SampleData")
def sample_data():
    # Same data as sample_data - using ISO date format for Tableau compatibility
    data = [
        {"Date": "2025-12-15", "Value": 41},
        {"Date": "2025-12-16", "Value": 52},
        {"Date": "2025-12-17", "Value": 27},
        {"Date": "2025-12-18", "Value": 33},
        {"Date": "2025-12-19", "Value": 42},
        {"Date": "2025-12-20", "Value": 41}
    ]

    # Apply OData query parameters
    args = request.args

    # $filter - basic support for simple equality filters
    if '$filter' in args:
        filter_expr = args['$filter']
        # Simple parsing for "Date eq 'value'" or "Value eq number"
        if ' eq ' in filter_expr:
            field, value = filter_expr.split(' eq ')
            field = field.strip()
            value = value.strip().strip("'")
            if field == 'Value':
                value = int(value)
            data = [item for item in data if str(item.get(field)) == str(value)]

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

    # $top - limit number of results
    if '$top' in args:
        top = int(args['$top'])
        data = data[:top]

    # $skip - skip number of results
    if '$skip' in args:
        skip = int(args['$skip'])
        data = data[skip:]

    # $count - return count
    if '$count' in args and args['$count'].lower() == 'true':
        odata_response = {
            "@odata.context": f"{request.url_root}sample_data/$metadata#SampleData",
            "@odata.count": len(data),
            "value": data
        }
    else:
        # OData response format
        odata_response = {
            "@odata.context": f"{request.url_root}sample_data/$metadata#SampleData",
            "value": data
        }

    return Response(
        json.dumps(odata_response),
        mimetype='application/json',
        headers={
            'OData-Version': '4.0',
            'Content-Type': 'application/json; odata.metadata=minimal'
        }
    )

# ========================================
# Garmin Activities OData Endpoints
# ========================================

# OData v4 Metadata endpoint for Garmin Activities
@app.route("/garmin_activities/$metadata")
def garmin_activities_metadata():
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

# OData v4 Service Document for Garmin Activities
@app.route("/garmin_activities/")
def garmin_activities_service_doc():
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

# OData v4 Data endpoint for Garmin Activities
@app.route("/garmin_activities/activities")
def garmin_activities_data():
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

# define the graphs endpoint here (actually, maybe not... )

# Run app
if __name__ == "__main__":

    app.run(debug=True)

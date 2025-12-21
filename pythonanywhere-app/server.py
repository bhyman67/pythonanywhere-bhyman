
# Need to use a DB with this...

# Standard Library Imports
import json
import os
import io

# Needed Libraries
from flask import Flask, render_template, request, Response
import plotly.express as px
from flask import jsonify
import pandas as pd
import numpy as np
import requests
import plotly

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
def portfolio():
    return render_template("portfolio.html")

# Covid by County app routes
@app.route("/covid-by-county")
def covid_home():

    # Pull the data and list all locations
    df = pull_data()
    locations = df["Combined_Key"].to_list()
    states = list(df["State"].unique())

    # Return covid-by-county.html
    return render_template("covid-by-county.html", states = states, list = locations)

@app.route("/covid-by-county/graph")
def county_graph():

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

@app.route("/sample_data")
def sample_data():
    data = [
        {"Date": "12/15/2025", "Value": 41},
        {"Date": "12/16/2025", "Value": 22},
        {"Date": "12/17/2025", "Value": 27},
        {"Date": "12/18/2025", "Value": 33},
        {"Date": "12/19/2025", "Value": 42},
        {"Date": "12/20/2025", "Value": 41}
    ]
    return jsonify(data)

# OData v4 Metadata endpoint
@app.route("/sample_data_2/$metadata")
def sample_data_2_metadata():
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
@app.route("/sample_data_2/")
def sample_data_2_service_doc():
    """OData v4 service document"""
    service_doc = {
        "@odata.context": f"{request.url_root}sample_data_2/$metadata",
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
@app.route("/sample_data_2/SampleData")
def sample_data_2():
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
            "@odata.context": f"{request.url_root}sample_data_2/$metadata#SampleData",
            "@odata.count": len(data),
            "value": data
        }
    else:
        # OData response format
        odata_response = {
            "@odata.context": f"{request.url_root}sample_data_2/$metadata#SampleData",
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

# define the graphs endpoint here (actually, maybe not... )

# Run app
if __name__ == "__main__":

    app.run(debug=True)

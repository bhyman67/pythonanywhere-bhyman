# COVID by County Blueprint
# This project displays COVID-19 case data by county using data from Johns Hopkins CSSE

import io
import json
import requests
import pandas as pd
import plotly
import plotly.express as px
from flask import Blueprint, render_template, request

# Create blueprint
covid_bp = Blueprint('covid', __name__, url_prefix='/covid-by-county')

def pull_data():
    """Pull COVID-19 data from Johns Hopkins GitHub repository"""
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

@covid_bp.route("/")
def covid_by_county():
    """Main COVID by County page"""
    # Pull the data and list all locations
    df = pull_data()
    locations = df["Combined_Key"].to_list()
    states = list(df["State"].unique())

    # Return covid-by-county.html
    return render_template("covid-by-county.html", states = states, list = locations)

@covid_bp.route("/graph")
def covid_by_county_graph():
    """Generate COVID graph based on selected county and state"""
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

    # Format the dataframe
    df.drop(columns = ["County","State"],inplace = True)
    df = df.T
    new_header = df.iloc[0] # grab the first row for the header
    df = df[1:] # take the data less the header row
    df.columns = new_header # set the header row as the df header

    # Calculate the differences
    for i in range(row_count):
        df.iloc[:,i] = df.iloc[:,i].diff(1)

    # Graph
    fig = px.line(df)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Return template and data
    return render_template("covid-by-county.html", list=locations, states = states, graphJSON=graphJSON)


# Need to use a DB with this... 

# Standard Library Imports
import json
import os 
import io

# Needed Libraries
from flask import Flask, render_template, request
import plotly.express as px
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

    # Return index.html
    return render_template("index.html", states = states, list = locations)

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
    return render_template("index.html", list=locations, states = states, graphJSON=graphJSON)

# define the graphs endpoint here (actually, maybe not... )

# Run app
if __name__ == "__main__":

    app.run(debug=True)
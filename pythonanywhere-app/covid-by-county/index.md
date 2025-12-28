<h1>
    <p align="center">COVID-19 by County Visualization</p>
</h1>

<h1></h1>

<p align="center"> <big>Click <a href="https://bhyman.pythonanywhere.com/covid-by-county" target = "_blank">here</a> to view the live application</big> </p>

## Overview

This Flask-based web application provides interactive COVID-19 case visualization by U.S. county. The application fetches real-time data from the Johns Hopkins CSSE COVID-19 repository and displays daily new cases using dynamic Plotly charts.

---

## Endpoints

### 1. COVID-19 Selection Form
**Route:** `GET /covid-by-county`

**Description:** Renders the main interface for county selection.

**Response:** HTML page with:
- State dropdown (populated with all U.S. states)
- County dropdown (filtered by selected state)
- Form to submit location selection

**Data Source:** 
- [Johns Hopkins CSSE COVID-19 Time Series Data](https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv)

**Template:** `covid-by-county.html`

---

### 2. COVID-19 Graph Display
**Route:** `GET /covid-by-county/graph`

**Description:** Displays an interactive line chart showing daily new COVID-19 cases for the selected county.

**Query Parameters:**
- `county` (required) - County name (e.g., "Los Angeles")
- `state` (required) - State name (e.g., "California")

**Example Request:**
```
GET /covid-by-county/graph?county=Los Angeles&state=California
```

**Response:** HTML page with:
- State and county selection form (pre-populated with current selection)
- Interactive Plotly line chart showing daily new cases over time
- Legend with county name

**Data Processing:**
1. Fetches latest time series data from Johns Hopkins repository
2. Filters data for specified county and state
3. Transposes data to convert date columns into rows
4. Calculates daily differences to show new cases per day
5. Generates interactive Plotly chart

**Template:** `covid-by-county.html` (with `graphJSON` parameter)

---

## Features

- **Real-time Data:** Pulls latest COVID-19 data directly from Johns Hopkins GitHub repository on each request
- **Interactive Charts:** Plotly-powered visualizations with zoom, pan, and hover capabilities
- **Daily New Cases:** Automatically calculates day-over-day differences to show new cases
- **State/County Filtering:** Dropdown-based selection for easy location browsing
- **Dynamic Rendering:** Same template used for both selection form and graph display

---

## Tech Stack

- **Backend:** Flask (Python web framework)
- **Data Processing:** Pandas, NumPy
- **Visualization:** Plotly
- **Data Source:** Johns Hopkins CSSE COVID-19 Time Series (GitHub)
- **Hosting:** PythonAnywhere

---

## Installation & Setup

### Requirements
```bash
pip install flask pandas numpy plotly requests
```

### Running Locally
```bash
python server.py
```
Access at `http://localhost:5000/covid-by-county`

---

<p align="right">Click <a href="https://github.com/bhyman67/pythonanywhere-bhyman">here</a> to view this project's repository</p>

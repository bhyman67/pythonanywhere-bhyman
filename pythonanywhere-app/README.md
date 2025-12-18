<h1>
    <p align="center">Covid by County Flask App</p>
</h1>

<h1></h1>

<p align="center"> <big>Click <a href="https://bhyman.pythonanywhere.com/" target = "_blank">here</a> to run the app</big> </p>

### Description
If you want to monitor the US numbers on Coronavirus, you could simply just google [state by state coronavirus cases](https://www.google.com/search?q=state+by+state+coronavirus+cases). I also really like the analysis in [covid19-projections.com](https://covid19-projections.com/). And of course, there's the [Johns Hopkins University heat map](https://www.arcgis.com/apps/opsdashboard/index.html#/bda7594740fd40299423467b48e9ecf6). I couldn't easily find line charts on daily new cases by county in the US (at the start...). So I decided to build them on on my own.

The user can select both a state and county and then generate a line graph of daily confirmed cases. 

### Data

I used data from the COVID-19 [repository](https://github.com/CSSEGISandData/COVID-19) owned by the CSSE at Johns Hopkins University.

### Code

This application has two endpoints. Both endpoints show the state and county dropdowns. The user can select a location and then hit submit to pull up the graph. Hitting the submit button in both endpoints will take you to the graph endpoint with a query string specifying the selected location.

* The root endpoint shows only the location web form.
  * GET: ``` / ```
* The graph endpoint will show both the location web form and the time series chart of the location specified in the query string.
  * GET: ``` /graph/ ```
  * **Requires** a query string with two parameters:
    * State
    * County
  * The data pull from the CSSEGISandData COVID-19 repo happens every time this endpoint gets requested. Not ideal...  

There's only one function:

* pull_data()
  * makes a web request (GET) to the CSSEGISandData COVID-19 repo and uses the pandas read_csv funct to read in time_series_covid19_confirmed_US.csv. 
  * Some columns also get dropped and renamed

<p align="right">Click <a href="https://github.com/bhyman67/Covid-by-County">here</a> to view this project's repository<p>

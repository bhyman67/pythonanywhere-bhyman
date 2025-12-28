# Flask App - Portfolio Project Server
# This server hosts multiple data visualization and API projects using Flask Blueprints

from flask import Flask, render_template

# Import project blueprints
from covid_by_county.routes import covid_bp
from sample_data_odata_endpoints.routes import sample_data_bp
from garmin_connect_odata_endpoints.routes import garmin_bp

# Initialize Flask app
app = Flask(__name__)

# Register blueprints for each project
app.register_blueprint(covid_bp)
app.register_blueprint(sample_data_bp)
app.register_blueprint(garmin_bp)

# Portfolio landing page
@app.route("/")
def portfolio_landing_page():
    return render_template("landing_page.html")

# Run app
if __name__ == "__main__":

    app.run(debug=True)

import numpy as np
import pandas as pd
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to the tables
Measurement = Base.classes.measurement
Station = Base.classes.station


#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def home():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        "Enter your start date in the api route below, between 2010-01-01 and 2017-08-23<br/>"
        f"/api/v1.0/2016-04-22<br/>"
        "Enter your start and end dates in the api route below, between 2010-01-01 and 2017-08-23<br/>"
        f"/api/v1.0/2016-04-22/2016-05-04"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Convert the query results to a dictionary using date as the key and prcp as the value."""      
    
    # query to retrieve the last 12 months of precipitation data
    
    # Calculate the date 1 year ago from the last data point in the database
    # determine date of last data point
    latest_date = session.query(func.max(Measurement.date)).one()
    # convert string to a date
    latest_date_as_date = pd.to_datetime(latest_date)
    # subtract a year
    a_year_prior = latest_date_as_date - dt.timedelta(days = 365)
    # convert back to a string
    a_year_earlier = a_year_prior.strftime('%Y-%m-%d')
    
    # Perform a query to retrieve the date and precipitation scores
    precip = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date>=a_year_earlier[0]).all()

    session.close()

    # Create a dictionary from the row data and append to a list of precip_date
    precip_date = []
    for date, prcp in precip:
        precip_dict = {}
        precip_dict["date"] = date
        precip_dict["prcp"] = prcp
        precip_date.append(precip_dict)

    """Return the JSON representation of your dictionary."""
    return jsonify(precip_date)


@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a JSON list of stations from the dataset."""
    # Query all stations
    results = session.query(Station.station).all()

    session.close()

    # Convert list of tuples into normal list
    all_stations = list(np.ravel(results))

    return jsonify(all_stations)

@app.route("/api/v1.0/tobs")
def tobs_year():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Query the dates and temperature observations of the most active station for the last year of data."""
    """Return a JSON list of temperature observations (TOBS) for the previous year."""
    # Calculate the date 1 year ago from the last data point in the database
    # determine date of last data point
    latest_date = session.query(func.max(Measurement.date)).one()
    # convert string to a date
    latest_date_as_date = pd.to_datetime(latest_date)
    # subtract a year
    a_year_prior = latest_date_as_date - dt.timedelta(days = 365)
    # convert back to a string
    a_year_earlier = a_year_prior.strftime('%Y-%m-%d')
    
    # most active station
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
            order_by(func.count(Measurement.station).desc()).limit(1).all()

    # Query the last 12 months of temperature observation data for this station
    temp_data = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == 'USC00519281').\
        filter(Measurement.date>=a_year_earlier[0]).all()
    
    # temperature is the [1] element for each entry in the tuple temp_data
    # extract all the temperatures as a list
    temps = [obs[1] for obs in temp_data]

    session.close()

    # jsonify temperatures list
    return jsonify(temps)

@app.route("/api/v1.0/<start>")
def calc_temps(start):
    """TMIN, TAVG, and TMAX for a list of dates.
    
    Args:
        start (string): A date string in the format %Y-%m-%d
        
                
    Returns:
        TMIN, TAVE, and TMAX
    """
    # Create our session (link) from Python to the DB
    session = Session(engine)

    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start).all()

    session.close()

    named_results = {'tmin': results[0][0], 'tavg':results[0][1], 'tmax':results[0][2]}

    return jsonify(named_results)   

@app.route("/api/v1.0/<start>/<end>")
def calc_temps_2(start, end):
    """TMIN, TAVG, and TMAX for a list of dates.
    
    Args:
        start (string): A date string in the format %Y-%m-%d
        end (string): A date string in the format %Y-%m-%d
                
    Returns:
        TMIN, TAVE, and TMAX
    """
    # Create our session (link) from Python to the DB
    session = Session(engine)

    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start).filter(Measurement.date <= end).all()

    session.close()

    named_results = {'tmin': results[0][0], 'tavg':results[0][1], 'tmax':results[0][2]}

    return jsonify(named_results)       


if __name__ == '__main__':
    app.run(debug=True)

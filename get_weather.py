"""
Using the free weather API Open-Meteo (open-meteo.com) to get outdoor temperature for comfort evaluation.
Change it to any weather API you like if preferred.
Latitude & longitude have to be configured manually, just want to keep it simple!
You could easily get them on Google Map for example. Open-Meteo also has a search function: https://open-meteo.com/en/docs
"""

import openmeteo_requests

import requests_cache
import pandas as pd
from retry_requests import retry
import logging
from datetime import datetime, timedelta


# Use the latitude & longitude of your city
latitude = 50.7766
longitude = 6.0834
timezone = "Europe/Berlin"


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params_past1days = {
    "latitude": latitude,
    "longitude": longitude,
    "hourly": "temperature_2m",
    "timezone": timezone,
    "past_days": 1,
    "forecast_days": 1,
}
params_past7days = {
    "latitude": latitude,
    "longitude": longitude,
    "hourly": "temperature_2m",
    "timezone": timezone,
    "past_days": 7,
    "forecast_days": 1,
}
params_today = {
    "latitude": latitude,
    "longitude": longitude,
    "hourly": ["temperature_2m", "relative_humidity_2m"],
    "timezone": timezone,
    "forecast_days": 1,
}


def t_outdoor_6am() -> float:
    """
    Get local outdoor air temperature [°C] at 6 a.m. from weather API (for daily clothing prediction)

    Returns
    -------
    tout_6am: float
        Local outdoor air temperature at 6 a.m. in [°C]
    """
    responses = openmeteo.weather_api(url, params=params_past1days)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    logger.info(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    logger.info(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()

    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
    }

    hourly_data["temperature_2m"] = hourly_temperature_2m

    hourly_dataframe = pd.DataFrame(data=hourly_data)

    # get today's outdoor temperature at 6 a.m.
    tout_6am = hourly_dataframe[
        hourly_dataframe["date"] == "6:00:00"
    ].temperature_2m.item()

    return tout_6am


def t_outdoor_avg_past7days() -> list:
    """
    Get average daily outdoor temperature in descending order.
    Calculated using historical data (hourly values) obtained from the weather API.
    Used to calculate the running mean temperature for adaptive thermal comfort model.

    Returns
    -------
    tout_avg_past7days_ls: list
        list of the average daily outdoor air temperature in descending order (i.e. from newest/yesterday to oldest):
        t(day-1), t(day-2), ..., t(day-6), t(day-7)
    """
    responses = openmeteo.weather_api(url, params=params_past7days)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    logger.info(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    logger.info(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()

    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
    }

    hourly_data["temperature_2m"] = hourly_temperature_2m

    hourly_dataframe = pd.DataFrame(data=hourly_data)
    # get daily average air temperature for past 7 days
    date_now = datetime.now()
    date_7daysago = datetime.now() - timedelta(days=7)
    # create mask for past 7 days: t(day-7), t(day-6), ..., t(day-2), t(day-1)
    mask = (
        hourly_dataframe["date"] < f"{date_now.year}-{date_now.month}-{date_now.day}"
    ) & (
        hourly_dataframe["date"]
        >= f"{date_7daysago.year}-{date_7daysago.month}-{date_7daysago.day}"
    )
    tout_past7days = hourly_dataframe.loc[mask]

    # set index
    tout_avg_past7days = tout_past7days.set_index("date")
    # calculate daily average temperature and sort it in descending order: t(day-1), t(day-2), ..., t(day-6), t(day-7)
    tout_avg_past7days = tout_avg_past7days.resample("D").mean().sort_index(ascending=False)
    # convert to list
    tout_avg_past7days_ls = tout_avg_past7days["temperature_2m"].tolist()

    return tout_avg_past7days_ls

def th_outdoor_avg_today() -> list:
    """
    Get today's local average outdoor air temperature [°C] from weather API (for daily clothing suggestions)

    Returns
    -------
    tout_avg: float
        Today's local average outdoor air temperature [°C]
    hout_avg: float
        Today's local average outdoor relative humidty [%]
    """
    responses = openmeteo.weather_api(url, params=params_today)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    logger.info(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    logger.info(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()

    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
    }

    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m

    hourly_dataframe = pd.DataFrame(data=hourly_data)

    # create mask for today
    date_now = datetime.now()
    mask = (hourly_dataframe["date"] >= f"{date_now.year}-{date_now.month}-{date_now.day}")
    thout_today = hourly_dataframe.loc[mask]

    # set index
    thout_avg_today = thout_today.set_index("date")
    # calculate today's average temperature & humidity
    tout_avg_today = thout_avg_today.resample("D").mean().temperature_2m.item()
    hout_avg_today = thout_avg_today.resample("D").mean().relative_humidity_2m.item()

    return [tout_avg_today, hout_avg_today]

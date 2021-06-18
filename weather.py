#!/usr/bin/env python

import requests
import hashlib
import sqlite3
import yaml
from datetime import datetime

with open("config.yaml") as config_file:
    config = yaml.safe_load(config_file)

# associate values with config stuff

api_key = config["api_key"]
lat = config["lat"]
lon = config["lon"]
api_base = "api.openweathermap.org/data/2.5/onecall"
exclude = ",".join(config["exclude"])
alert_types = config["alerts"]
units = config["units"]

url = f"https://{api_base}?lat={lat}&lon={lon}&exclude={exclude}&units={units}&appid={api_key}"
weather = requests.get(url)
try:
    # if we don't have a key error, we have an alert
    alerts = weather.json()["alerts"]
except KeyError:
    alerts = None

active_alerts = []
if alerts:
    for alert in alerts:
        # NWS throws capitals everywhere, this is an attempt to normalize that
        if alert["event"].lower() in map(str.lower, alert_types):
            # compute a hash of the event name, start and stop times to prevent
            # sending alerts every time this runs
            alert_hash = hashlib.sha256(
                f"{alert['event']}+{alert['start']}+{alert['end']}".encode()
            )
            try:
                # Just try to cram the alert_hash into the DB
                # if it is already there, a unique contraint will be invalid
                # and we know we have already alerted on this particular
                # event
                db = sqlite3.connect("alerts.db")
                sql = f"insert into alerts values('{alert_hash.hexdigest()}',{int(datetime.now().timestamp())})"
                db.execute(sql)
                db.commit()
                active_alerts.append(alert["description"])
            except sqlite3.IntegrityError:
                pass
    if active_alerts:
        for alert in active_alerts:
            print(alert + "\n\n")
    else:
        print("No new alerts")
else:
    print("No alerts for your location")

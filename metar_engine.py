import requests
import pandas as pd
import os
from datetime import datetime, timezone

STATION_CODE = "WARR"
CSV_FILE = "metar_history.csv"
FONNTE_TOKEN = os.environ["FONNTE_TOKEN"]

def get_metar(station):
    url = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{station}.TXT"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        return r.text.strip().split("\n")[-1]
    return None

def send_whatsapp(message):
    url = "https://api.fonnte.com/send"
    headers = {"Authorization": FONNTE_TOKEN}
    data = {
        "target": "6282126910641",
        "message": message
    }
    requests.post(url, headers=headers, data=data)

metar_data = get_metar(STATION_CODE)

if not metar_data:
    print("No data from NOAA")
    exit()

if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=["station","time","metar"])

if df.empty or df.iloc[-1]["metar"] != metar_data:

    new_row = {
        "station": STATION_CODE,
        "time": datetime.now(timezone.utc),
        "metar": metar_data
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)

    send_whatsapp(f"METAR UPDATE\n\n{metar_data}")

    print("Updated & WA sent.")

else:
    print("No new METAR.")

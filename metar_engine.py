import requests
import pandas as pd
import os
import base64
from datetime import datetime

# =========================
# CONFIG
# =========================
STATION_CODE = "WARR"
CSV_FILE = "metar_history.csv"

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = os.environ["GITHUB_REPO"]
GITHUB_FILE_PATH = os.environ["GITHUB_FILE_PATH"]
FONNTE_TOKEN = os.environ["FONNTE_TOKEN"]


# =========================
# GET METAR
# =========================
def get_metar(station):
    url = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{station}.TXT"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        return r.text.strip().split("\n")[-1]
    return None


# =========================
# SEND WA
# =========================
def send_whatsapp(message):
    url = "https://api.fonnte.com/send"
    headers = {"Authorization": FONNTE_TOKEN}
    data = {
        "target": "6282126910641",
        "message": message
    }
    requests.post(url, headers=headers, data=data)


# =========================
# MAIN ENGINE
# =========================
metar_data = get_metar(STATION_CODE)

if not metar_data:
    exit()

# Load CSV
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=["station","time","metar"])

# Cek perubahan
if df.empty or df.iloc[-1]["metar"] != metar_data:

    new_row = {
        "station": STATION_CODE,
        "time": datetime.utcnow(),
        "metar": metar_data
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)

    # Kirim WA
    send_whatsapp(f"METAR UPDATE\n\n{metar_data}")

    print("Data updated & WA sent.")
else:
    print("No new METAR.")

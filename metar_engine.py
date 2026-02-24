import requests
import pandas as pd
import os
from datetime import datetime, timezone

STATION_CODE = "WARR"
CSV_FILE = "metar_history.csv"

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
# PARSE METAR
# =========================
def parse_metar(metar):
    data = {
        "station": None,
        "day": None,
        "hour": None,
        "minute": None,
        "wind_dir": None,
        "wind_speed_kt": None,
        "visibility_m": None,
        "weather": None,
        "cloud": None,
        "temperature_c": None,
        "dewpoint_c": None,
        "pressure_hpa": None,
        "trend": None
    }

    parts = metar.replace("=", "").split()

    for part in parts:
        if len(part) == 4 and part.isalpha():
            data["station"] = part

        if part.endswith("Z") and len(part) == 7:
            data["day"] = part[0:2]
            data["hour"] = part[2:4]
            data["minute"] = part[4:6]

        if part.endswith("KT"):
            data["wind_dir"] = part[0:3]
            data["wind_speed_kt"] = part[3:5]

        if part.isdigit() and len(part) == 4:
            data["visibility_m"] = int(part)

        if part.startswith(("FEW","SCT","BKN","OVC")):
            data["cloud"] = part

        if "/" in part and len(part) == 5:
            t, d = part.split("/")
            data["temperature_c"] = t
            data["dewpoint_c"] = d

        if part.startswith("Q"):
            data["pressure_hpa"] = part[1:]

        if part == "NOSIG":
            data["trend"] = part

    return data

# =========================
# GENERATE NARRATIVE
# =========================
def generate_narrative(parsed):
    return (
        f"Angin {parsed['wind_dir']} derajat "
        f"{parsed['wind_speed_kt']} knot. "
        f"Visibilitas {parsed['visibility_m']} meter. "
        f"Suhu {parsed['temperature_c']}°C. "
        f"Tekanan {parsed['pressure_hpa']} hPa."
    )

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
    print("No data from NOAA")
    exit()

if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=["station","time","metar"])

if df.empty or df.iloc[-1]["metar"] != metar_data:

    parsed = parse_metar(metar_data)
    narrative = generate_narrative(parsed)

    # FORMAT QAM
    date_str = f"{parsed['day']}/{datetime.utcnow().strftime('%m/%Y')}"
    time_str = f"{parsed['hour']}.{parsed['minute']}"

    wind = f"{parsed['wind_dir']}°/{parsed['wind_speed_kt']} KT"
    vis = f"{int(parsed['visibility_m']/1000)} KM"

    cloud = "-"
    if parsed["cloud"]:
        amount = parsed["cloud"][:3]
        height = int(parsed["cloud"][3:6]) * 100
        cloud = f"{amount} {height}FT"

    qam_report = f"""MET REPORT (QAM)
BANDARA JUANDA {STATION_CODE}
DATE : {date_str}
TIME : {time_str} UTC
========================
WIND    : {wind}
VIS     : {vis}
CLOUD   : {cloud}
TT/TD   : {parsed['temperature_c']}/{parsed['dewpoint_c']}
QNH     : {parsed['pressure_hpa']} MB
"""

    full_message = f"""📡 METAR UPDATE

{qam_report}

🧠 Interpretasi:
{narrative}
"""

    # SIMPAN CSV
    new_row = {
        "station": STATION_CODE,
        "time": datetime.now(timezone.utc),
        "metar": metar_data
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)

    send_whatsapp(full_message)

    print("Updated & WA sent.")

else:
    print("No new METAR.")

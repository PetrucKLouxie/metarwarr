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
def format_metar_time(parsed):
    if not parsed["day"]:
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    year = datetime.utcnow().year
    month = datetime.utcnow().month

    return f"{year}-{month:02d}-{parsed['day']} {parsed['hour']}:{parsed['minute']} UTC"
    
if df.empty or df.iloc[-1]["metar"] != metar_data:

    parsed = parse_metar(metar_data)

    # FORMAT WAKTU
    date_str = f"{parsed['day']}/{datetime.utcnow().strftime('%m/%Y')}"
    time_str = f"{parsed['hour']}.{parsed['minute']}"

    wind = f"{parsed['wind_dir']}°/{parsed['wind_speed_kt']} KT"
    vis = f"{int(parsed['visibility_m']/1000)} KM"

    cloud = "-"
    if parsed["cloud"]:
        amount = parsed["cloud"][:3]
        height = int(parsed["cloud"][3:6]) * 100
        cloud = f"{amount} {height}FT"

    # QAM FORMAT
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

    # INTERPRETASI
    narrative = (
        f"Angin dari {parsed['wind_dir']} derajat "
        f"{parsed['wind_speed_kt']} knot. "
        f"Visibilitas {parsed['visibility_m']} meter. "
        f"Suhu {parsed['temperature_c']}°C. "
        f"Tekanan {parsed['pressure_hpa']} hPa."
    )

    full_message = f"""📡 METAR UPDATE

{qam_report}

🧠 Interpretasi:
{narrative}
"""

    # SIMPAN CSV
    new_row = {
        "station": STATION_CODE,
        "time": format_metar_time(parsed),
        "metar": metar_data
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)

    send_whatsapp(full_message)

    print("Updated & WA sent.")

else:
    print("No new METAR.")

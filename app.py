import streamlit as st
import requests
import pandas as pd
import os
import re
from datetime import datetime, timezone
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="METAR Realtime Global", layout="wide")
st.title("🌍 METAR Real-Time Dashboard")

# =========================
# AUTO REFRESH 10 MENIT
# =========================
st_autorefresh(interval=600000, key="refresh")

# =========================
# INPUT ICAO
# =========================
station_code = st.text_input("Masukkan Kode ICAO", value="WARR")

# =========================
# GET METAR
# =========================
def get_metar(station_code):
    try:
        url = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{station_code.upper()}.TXT"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            lines = response.text.strip().split("\n")
            return lines[-1]  # ambil baris METAR terakhir

        return None
    except:
        return None

# =========================
# ROUND UTC TIME 00 / 30
# =========================
def get_rounded_utc_time():
    now = datetime.now(timezone.utc)
    minute = 30 if now.minute >= 30 else 0
    rounded = now.replace(minute=minute, second=0, microsecond=0)
    return rounded.strftime("%Y-%m-%d %H:%M UTC")

# =========================
# PARSE TEMPO
# =========================
def parse_tempo_section(metar):
    if " TEMPO " not in metar:
        return None

    tempo_part = metar.split(" TEMPO ")[1]
    parts = tempo_part.replace("=", "").split()

    tempo_data = {"until": None, "visibility": None, "weather": None}

    for part in parts:
        if part.startswith("TL"):
            tempo_data["until"] = part[2:]
        if part.isdigit() and len(part) == 4:
            tempo_data["visibility"] = part
        if part in ["TSRA","+TSRA","RA","+RA","-RA","HZ"]:
            tempo_data["weather"] = part

    return tempo_data

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

    clean_metar = metar.replace("=", "")
    parts = clean_metar.split()

    for part in parts:

        if len(part) == 4 and part.isalpha():
            data["station"] = part

        if part.endswith("Z") and len(part) == 7:
            data["day"] = part[0:2]
            data["hour"] = part[2:4]
            data["minute"] = part[4:6]

        if part.endswith("KT") and len(part) >= 7:
            data["wind_dir"] = part[0:3]
            data["wind_speed_kt"] = part[3:5]

        if part.isdigit() and len(part) == 4:
            data["visibility_m"] = int(part)

        if part in ["HZ","RA","+RA","-RA","TSRA","+TSRA"]:
            data["weather"] = part

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
# GENERATE TEXT
# =========================

def generate_metar_narrative(parsed, tempo=None):

    if not parsed["station"]:
        return "Data METAR tidak valid."

    text = []

    # Intro
    text.append(
        f"Observasi cuaca di Bandara {parsed['station']} "
        f"pada tanggal {parsed['day']} pukul {parsed['hour']}:{parsed['minute']} UTC menunjukkan kondisi berikut:"
    )

    # Wind
    if parsed["wind_dir"] and parsed["wind_speed_kt"]:
        text.append(
            f"Angin bertiup dari arah {parsed['wind_dir']} derajat "
            f"dengan kecepatan {parsed['wind_speed_kt']} knot."
        )

    # Visibility
    if parsed["visibility_m"]:
        km = parsed["visibility_m"] / 1000
        text.append(f"Jarak pandang tercatat sekitar {km:.1f} kilometer.")

    # Weather
    weather_map = {
        "HZ": "kabut asap (haze)",
        "RA": "hujan",
        "+RA": "hujan lebat",
        "-RA": "hujan ringan",
        "TSRA": "badai petir disertai hujan",
        "+TSRA": "badai petir kuat disertai hujan"
    }

    if parsed["weather"]:
        weather_desc = weather_map.get(parsed["weather"], parsed["weather"])
        text.append(f"Terdapat fenomena cuaca berupa {weather_desc}.")

    # Cloud
    if parsed["cloud"]:
        amount = parsed["cloud"][:3]
        height = int(parsed["cloud"][3:6]) * 100

        cloud_map = {
            "FEW": "awan sedikit",
            "SCT": "awan tersebar",
            "BKN": "awan pecah",
            "OVC": "awan mendung penuh"
        }

        cloud_desc = cloud_map.get(amount, "awan")
        text.append(f"{cloud_desc.capitalize()} terdeteksi pada ketinggian sekitar {height} kaki.")

    # Temperature
    if parsed["temperature_c"] and parsed["dewpoint_c"]:
        text.append(
            f"Suhu udara {parsed['temperature_c']}°C "
            f"dengan titik embun {parsed['dewpoint_c']}°C."
        )

    # Pressure
    if parsed["pressure_hpa"]:
        text.append(f"Tekanan udara tercatat {parsed['pressure_hpa']} hPa.")

    # Trend
    if tempo:
        text.append(
            f"Secara temporer hingga pukul {tempo['until']} UTC "
            f"diperkirakan jarak pandang {tempo['visibility']} meter "
            f"dengan kondisi {tempo['weather']}."
        )
    elif parsed["trend"] == "NOSIG":
        text.append("Tidak terdapat perubahan signifikan dalam waktu dekat.")

    return " ".join(text)

# =========================
# CSV SETUP
# =========================
CSV_FILE = "metar_history.csv"

if not os.path.exists(CSV_FILE):
    df_history = pd.DataFrame(columns=["station","time","metar"])
    df_history.to_csv(CSV_FILE, index=False)
else:
    df_history = pd.read_csv(CSV_FILE)

# =========================
# GET DATA
# =========================
metar_data = get_metar(station_code)

if metar_data:
    if len(df_history) == 0 or df_history.iloc[-1]["metar"] != metar_data:
        new_row = {
            "station": station_code.upper(),
            "time": get_rounded_utc_time(),
            "metar": metar_data
        }

        df_history = pd.concat([df_history, pd.DataFrame([new_row])], ignore_index=True)
        df_history.to_csv(CSV_FILE, index=False)

        st.success("Data baru ditambahkan ke histori")

# =========================
# DISPLAY LATEST
# =========================
if len(df_history) > 0:

    latest = df_history.iloc[-1]
    st.subheader(f"📡 METAR Terbaru - {latest['station']}")
    st.code(latest["metar"])

    parsed = parse_metar(latest["metar"])
    tempo = parse_tempo_section(latest["metar"])
    narrative = generate_metar_narrative(parsed, tempo)

    st.markdown("---")
    st.subheader("🧠 Interpretasi METAR (Narasi Otomatis)")
    st.write(narrative)

    # =========================
    # FORMAT QAM
    # =========================

    date_str = f"{parsed['day']}/{datetime.utcnow().strftime('%m/%Y')}" if parsed['day'] else "-"
    time_str = f"{parsed['hour']}.{parsed['minute']}" if parsed['hour'] else "-"

    wind = f"{parsed['wind_dir']}°/{parsed['wind_speed_kt']} KT" if parsed['wind_dir'] else "NIL"
    vis = f"{int(parsed['visibility_m']/1000)} KM" if parsed['visibility_m'] else "NIL"

    cloud = "-"
    if parsed["cloud"]:
        amount = parsed["cloud"][:3]
        height = int(parsed["cloud"][3:6]) * 100
        cloud = f"{amount} {height}FT"

    if tempo:
        trend_text = f"TEMPO TL{tempo['until']} {tempo['visibility']} {tempo['weather']}"
    else:
        trend_text = parsed["trend"] if parsed["trend"] else "NIL"

    qam_report = f"""MET REPORT (QAM)
BANDARA {latest['station']}
DATE : {date_str}
TIME : {time_str} UTC
========================
WIND    : {wind}
VIS     : {vis}
WEATHER : {parsed['weather'] if parsed['weather'] else 'NIL'}
CLOUD   : {cloud}
TT/TD   : {parsed['temperature_c']}/{parsed['dewpoint_c']}
QNH     : {parsed['pressure_hpa']} MB
QFE     : {parsed['pressure_hpa']} MB
REMARKS : NIL
TREND   : {trend_text}
"""

    st.markdown("---")
    st.subheader("🧾 Format QAM (Siap Copy)")
    st.text_area("QAM Output", qam_report, height=300)

    st.download_button(
        label="⬇ Download QAM TXT",
        data=qam_report,
        file_name=f"QAM_{latest['station']}.txt",
        mime="text/plain"
    )

    # =========================
    # METRICS
    # =========================
    st.markdown("### 📊 Detail Cuaca")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🌡 Suhu (°C)", parsed["temperature_c"])
        st.metric("💧 Dew Point (°C)", parsed["dewpoint_c"])

    with col2:
        st.metric("💨 Wind Direction (°)", parsed["wind_dir"])
        st.metric("💨 Wind Speed (KT)", parsed["wind_speed_kt"])

    with col3:
        st.metric("👁 Visibility (m)", parsed["visibility_m"])
        st.metric("📊 Pressure (hPa)", parsed["pressure_hpa"])

# =========================
# HISTORY TABLE
# =========================
st.markdown("---")
st.subheader("📜 Histori METAR (CSV)")
st.dataframe(df_history.tail(20), use_container_width=True)

if os.path.exists(CSV_FILE):
    with open(CSV_FILE, "rb") as file:
        st.download_button(
            label="⬇ Download CSV",
            data=file,
            file_name="metar_history.csv",
            mime="text/csv"
        )



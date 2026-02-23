import streamlit as st
import requests
import pandas as pd
import os
import re
import json
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="METAR Realtime Global", layout="wide")


st.title("🌍 METAR Real-Time Dashboard")

# =========================
# AUTO REFRESH 1 MENIT
# =========================
st_autorefresh(interval=600000, key="refresh")

# INPUT ICAO
# =========================
station_code = st.text_input(
    "Masukkan Kode ICAO",
    value="WARR"
)
def get_metar(station_code):
    try:
        url = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{station_code.upper()}.TXT"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            lines = response.text.strip().split("\n")
            
            # Biasanya baris terakhir adalah METAR
            if len(lines) >= 2:
                return lines[-1]
        
        return None

    except Exception as e:
        return None

# =========================
# FILE CSV
# =========================
CSV_FILE = "metar_history.csv"

# =========================
# Pastikan file ada
# =========================
if not os.path.exists(CSV_FILE):
    df_history = pd.DataFrame(columns=["station", "time", "metar"])
    df_history.to_csv(CSV_FILE, index=False)
else:
    df_history = pd.read_csv(CSV_FILE)

# =========================
# Tambah data baru jika berbeda
# =========================
metar_data = get_metar(station_code)

if metar_data:
    if len(df_history) == 0 or df_history.iloc[-1]["metar"] != metar_data:

        new_row = {
            "station": station_code.upper(),
            "time": datetime.now(),
            "metar": metar_data
        }

        df_history = pd.concat([df_history, pd.DataFrame([new_row])], ignore_index=True)
        df_history.to_csv(CSV_FILE, index=False)

        st.success("Data baru ditambahkan ke CSV")

# =========================

def parse_metar(metar):
    data = {
        "wind_dir": None,
        "wind_speed_kt": None,
        "visibility_m": None,
        "temperature_c": None,
        "dewpoint_c": None,
        "pressure_hpa": None
    }

    try:
        # WIND 09005KT
        wind_match = re.search(r'(\d{3})(\d{2})KT', metar)
        if wind_match:
            data["wind_dir"] = int(wind_match.group(1))
            data["wind_speed_kt"] = int(wind_match.group(2))

        # VISIBILITY 8000
        vis_match = re.search(r'\s(\d{4})\s', metar)
        if vis_match:
            data["visibility_m"] = int(vis_match.group(1))

        # TEMP / DEWPOINT 31/24
        temp_match = re.search(r'(\d{2})/(\d{2})', metar)
        if temp_match:
            data["temperature_c"] = int(temp_match.group(1))
            data["dewpoint_c"] = int(temp_match.group(2))

        # PRESSURE Q1010
        press_match = re.search(r'Q(\d{4})', metar)
        if press_match:
            data["pressure_hpa"] = int(press_match.group(1))

    except:
        pass

    return data

# =========================

# =========================
# LOAD CSV JIKA ADA
# =========================
if os.path.exists(CSV_FILE):
    df_history = pd.read_csv(CSV_FILE)
else:
    df_history = pd.DataFrame(columns=["station", "time", "metar"])

# =========================
# AMBIL DATA TERBARU
# =========================
metar_data = get_metar(station_code)

if metar_data:

    # Cek apakah data terakhir sama
    if len(df_history) == 0 or df_history.iloc[-1]["metar"] != metar_data:

        new_row = {
            "station": station_code.upper(),
            "time": datetime.now(),
            "metar": metar_data
        }

        df_history = pd.concat([df_history, pd.DataFrame([new_row])], ignore_index=True)

        # Simpan ke CSV
        df_history.to_csv(CSV_FILE, index=False)

        st.success("Data baru ditambahkan ke histori")

# =========================
# TAMPILKAN METAR TERBARU
# =========================
if len(df_history) > 0:
    latest = df_history.iloc[-1]

    st.subheader(f"📡 METAR Terbaru - {latest['station']}")
    st.code(latest["metar"])
    parsed = parse_metar(latest["metar"])
    # =========================
# FORMAT QAM STYLE
# =========================

def extract_metar_datetime(metar):
    # Format contoh: WARR 230530Z
    match = re.search(r'(\d{2})(\d{2})(\d{2})Z', metar)
    if match:
        day = match.group(1)
        hour = match.group(2)
        minute = match.group(3)
        return day, hour, minute
    return None, None, None


def generate_qam_format(station, parsed, raw_metar):

    day, hour, minute = extract_metar_datetime(raw_metar)

    if day:
        now = datetime.utcnow()
        date_str = f"{day}/{now.strftime('%m/%Y')}"
        time_str = f"{hour}.{minute}"
    else:
        date_str = "-"
        time_str = "-"

    wind = f"{parsed['wind_dir']}°/{parsed['wind_speed_kt']} KT" if parsed['wind_dir'] else "NIL"
    vis_km = f"{int(parsed['visibility_m']/1000)} KM" if parsed['visibility_m'] else "NIL"
    temp_td = f"{parsed['temperature_c']}/{parsed['dewpoint_c']}" if parsed['temperature_c'] else "NIL"
    pressure = f"{parsed['pressure_hpa']} MB" if parsed['pressure_hpa'] else "NIL"

    qam_text = f"""MET REPORT (QAM)
BANDARA {station.upper()}
DATE : {date_str}
TIME : {time_str} UTC
========================
WIND    : {wind}
VIS     : {vis_km}
WEATHER : NIL
CLOUD   : -
TT/TD   : {temp_td}
QNH     : {pressure}
QFE     : {pressure}
REMARKS : NIL
TREND   : NOSIG"""

    return qam_text


qam_report = generate_qam_format(
    latest["station"],
    parsed,
    latest["metar"]
)

st.markdown("---")
st.subheader("🧾 Format QAM (Siap Copy)")

st.text_area("QAM Output", qam_report, height=300)

# Tombol COPY


# Tombol Download TXT
st.download_button(
    label="⬇ Download QAM TXT",
    data=qam_report,
    file_name=f"QAM_{latest['station']}.txt",
    mime="text/plain"
)

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
# TAMPILKAN HISTORI
# =========================
st.markdown("---")
st.subheader("📜 Histori METAR (CSV)")

st.dataframe(df_history.tail(20), use_container_width=True)

# Tombol download CSV
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, "rb") as file:
        st.download_button(
            label="⬇ Download CSV",
            data=file,
            file_name="metar_history.csv",
            mime="text/csv"
        )
    st.info(f"🕒 Waktu Simpan: {latest['time']}")


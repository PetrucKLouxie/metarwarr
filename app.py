import streamlit as st
import requests
import pandas as pd
import os
import re
from datetime import datetime

st.set_page_config(page_title="METAR Monitor WARR", layout="wide")

CSV_FILE = "metar_history.csv"
STATION = "WARR"

# ==============================
# GET METAR NOAA
# ==============================

def get_metar(station):
    url = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{station}.TXT"
    r = requests.get(url, timeout=10)

    if r.status_code == 200:
        text = r.text.strip().split("\n")
        return text[-1]

    return None


# ==============================
# PARSE METAR
# ==============================

def parse_metar(metar):

    data = {}

    wind = re.search(r"(\d{3})(\d{2})KT", metar)
    if wind:
        data["wind_dir"] = wind.group(1)
        data["wind_speed"] = wind.group(2)

    vis = re.search(r" (\d{4}) ", metar)
    if vis:
        data["vis"] = vis.group(1)

    temp = re.search(r" (\d{2})/(\d{2}) ", metar)
    if temp:
        data["temp"] = temp.group(1)
        data["dew"] = temp.group(2)

    qnh = re.search(r"Q(\d{4})", metar)
    if qnh:
        data["qnh"] = qnh.group(1)

    cloud = re.search(r"(FEW|SCT|BKN|OVC)\d{3}", metar)
    if cloud:
        data["cloud"] = cloud.group()

    if "NOSIG" in metar:
        data["trend"] = "NOSIG"
    else:
        data["trend"] = "-"

    return data


# ==============================
# LOAD HISTORY
# ==============================

if os.path.exists(CSV_FILE):
    df_history = pd.read_csv(CSV_FILE)
else:
    df_history = pd.DataFrame(columns=["time", "metar"])
    
@st.cache_data(ttl=60)
def get_latest_metar():
    return update_metar()


metar = get_latest_metar()

parsed = parse_metar(metar)
# ==============================
# WA
# ==============================
def send_whatsapp(message):

    token = st.secrets["FONNTE_TOKEN"]
    target = st.secrets["TARGET_WA"]

    url = "https://api.fonnte.com/send"

    payload = {
        "target": target,
        "message": message
    }

    headers = {
        "Authorization": token
    }

    requests.post(url, data=payload, headers=headers)
    
def format_wa_message(metar, parsed):
    time_now = datetime.utcnow()
    
    return f"""
MET REPORT (QAM)

BANDARA JUANDA WARR
DATE : {time_now.strftime("%d/%m/%Y")}
TIME : {time_now.strftime("%H:%M")} UTC

=========================

WIND    : {parsed.get("wind_dir","-")}/{parsed.get("wind_speed","-")} KT
VIS     : {parsed.get("vis","-")} M
WEATHER : NIL
CLOUD   : {parsed.get("cloud","-")}
T/Td    : {parsed.get("temp","-")}/{parsed.get("dew","-")}
QNH     : {parsed.get("qnh","-")} MB
QFE     : {parsed.get("qnh","-")} MB
REMARKS : NIL
TREND   : {parsed.get("trend","-")}
"""
# ==============================
# UPDATE METAR
# ==============================

def update_metar():

    global df_history

    metar = get_metar(STATION)

    if metar is None:
        return None

    if len(df_history) == 0 or metar != df_history.iloc[-1]["metar"]:

        parsed = parse_metar(metar)

        new = {
            "time": datetime.utcnow(),
            "metar": metar
        }

        df_history.loc[len(df_history)] = new
        df_history.to_csv(CSV_FILE, index=False)

        # KIRIM WHATSAPP
        message = format_wa_message(metar, parsed)
        send_whatsapp(message)

    return metar

# ==============================
# HEADER
# ==============================

st.markdown(
"""
# ✈️ METAR REAL-TIME MONITORING SYSTEM
### 📍 JUANDA INTERNATIONAL AIRPORT (WARR)
Surabaya – Indonesia
""")

st.write("🟢 **MODE: PUBLIC VIEW**")

# ==============================
# METAR TEXT
# ==============================

st.subheader("📡 METAR Terbaru - WARR")

st.code(metar)

st.success("● STATUS: OPERATIONAL")

# ==============================
# DETAIL CUACA
# ==============================

st.subheader("📊 Detail Cuaca")

col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)

col1.metric("🌡️ Suhu (°C)", parsed.get("temp","-"))
col2.metric("🧭 Wind Direction", parsed.get("wind_dir","-"))
col3.metric("👁 Visibility (m)", parsed.get("vis","-"))

col4.metric("💧 Dew Point (°C)", parsed.get("dew","-"))
col5.metric("💨 Wind Speed (KT)", parsed.get("wind_speed","-"))
col6.metric("📈 Pressure (hPa)", parsed.get("qnh","-"))

st.divider()

# ==============================
# FORMAT QAM
# ==============================

st.subheader("📄 Format QAM")

time_now = datetime.utcnow()

qam = f"""
MET REPORT (QAM)

BANDARA JUANDA WARR
DATE : {time_now.strftime("%d/%m/%Y")}
TIME : {time_now.strftime("%H:%M")} UTC

=========================

WIND    : {parsed.get("wind_dir","-")}/{parsed.get("wind_speed","-")} KT
VIS     : {parsed.get("vis","-")} M
WEATHER : NIL
CLOUD   : {parsed.get("cloud","-")}
T/Td    : {parsed.get("temp","-")}/{parsed.get("dew","-")}
QNH     : {parsed.get("qnh","-")} MB
QFE     : {parsed.get("qnh","-")} MB
REMARKS : NIL
TREND   : {parsed.get("trend","-")}
"""

st.code(qam)

st.download_button(
"📥 Copy QAM",
qam,
file_name="QAM.txt"
)

st.divider()

# ==============================
# INTERPRETASI
# ==============================

st.subheader("🧠 Interpretasi METAR")

interpretasi = f"""
Observasi cuaca di Bandara WARR pada waktu {time_now.strftime("%H:%M")} UTC menunjukkan kondisi berikut:
Angin dari arah {parsed.get("wind_dir","-")}° dengan kecepatan {parsed.get("wind_speed","-")} knot.
Jarak pandang sekitar {parsed.get("vis","-")} meter.
Awan {parsed.get("cloud","-")}.
Suhu {parsed.get("temp","-")}°C dengan titik embun {parsed.get("dew","-")}°C.
Tekanan udara {parsed.get("qnh","-")} hPa.
"""

if parsed.get("trend") == "NOSIG":
    interpretasi += "Tidak ada perubahan signifikan dalam waktu dekat."

st.write(interpretasi)

st.divider()

# ==============================
# HISTORY
# ==============================

st.subheader("📜 METAR History")

st.dataframe(df_history)

st.download_button(
"⬇ Download METAR Record (CSV)",
df_history.to_csv(index=False),
file_name="metar_history.csv"
)

# ==============================
# AUTO REFRESH
# ==============================

st.autorefresh(interval=60000)



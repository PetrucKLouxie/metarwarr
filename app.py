import streamlit as st
import pandas as pd
import requests
import re
import os
import time
from datetime import datetime
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="METAR Monitoring", layout="wide")

STATION = "WARR"
CSV_FILE = "metar_history.csv"

# ==========================
# WHATSAPP
# ==========================

def send_whatsapp(msg):

    token = st.secrets["FONNTE_TOKEN"]
    target = st.secrets["TARGET_WA"]

    url = "https://api.fonnte.com/send"

    payload = {
        "target": target,
        "message": msg
    }

    headers = {"Authorization": token}

    try:
        requests.post(url, data=payload, headers=headers)
    except:
        pass


# ==========================
# GET METAR
# ==========================

def get_metar(station):

    url = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{station}.TXT"

    r = requests.get(url, timeout=10)

    if r.status_code == 200:
        text = r.text.strip().split("\n")
        return text[-1]

    return None


# ==========================
# PARSE METAR
# ==========================

def parse_metar(metar):

    data = {}

    wind = re.search(r"(\d{3})(\d{2})KT", metar)
    if wind:
        data["wind_dir"] = int(wind.group(1))
        data["wind_speed"] = int(wind.group(2))

    vis = re.search(r" (\d{4}) ", metar)
    if vis:
        data["vis"] = int(vis.group(1))

    temp = re.search(r" (\d{2})/(\d{2}) ", metar)
    if temp:
        data["temp"] = int(temp.group(1))
        data["dew"] = int(temp.group(2))

    qnh = re.search(r"Q(\d{4})", metar)
    if qnh:
        data["qnh"] = int(qnh.group(1))

    cloud = re.search(r"(FEW|SCT|BKN|OVC)\d{3}", metar)
    if cloud:
        data["cloud"] = cloud.group()

    data["ts"] = "TS" in metar or "CB" in metar

    return data


# ==========================
# LOAD HISTORY
# ==========================

if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=[
        "time","metar","wind_dir","wind_speed",
        "vis","temp","dew","qnh"
    ])


# ==========================
# UPDATE METAR
# ==========================

def update_metar():

    global df

    metar = get_metar(STATION)

    if metar is None:
        return None

    if len(df) == 0 or metar != df.iloc[-1]["metar"]:

        parsed = parse_metar(metar)

        new = {
            "time": datetime.utcnow(),
            "metar": metar,
            "wind_dir": parsed.get("wind_dir"),
            "wind_speed": parsed.get("wind_speed"),
            "vis": parsed.get("vis"),
            "temp": parsed.get("temp"),
            "dew": parsed.get("dew"),
            "qnh": parsed.get("qnh")
        }

        df.loc[len(df)] = new
        df.to_csv(CSV_FILE, index=False)

        alert = ""

        if parsed.get("vis",9999) < 3000:
            alert += "⚠ Visibility rendah\n"

        if parsed.get("wind_speed",0) > 20:
            alert += "⚠ Wind >20 kt\n"

        if parsed.get("ts"):
            alert += "⚠ Thunderstorm detected\n"

        # HOLDING DETECTION
        if parsed.get("vis",9999) < 5000 and parsed.get("wind_speed",0) > 15:
            alert += "✈ Potensi HOLDING\n"

        msg = f"""
METAR UPDATE {STATION}

{metar}

Wind : {parsed.get('wind_dir')}/{parsed.get('wind_speed')} kt
Vis  : {parsed.get('vis')} m
Temp : {parsed.get('temp')}/{parsed.get('dew')}
QNH  : {parsed.get('qnh')}

{alert}
"""

        send_whatsapp(msg)

    return metar


@st.cache_data(ttl=60)
def get_latest():
    return update_metar()


metar = get_latest()
parsed = parse_metar(metar)


# ==========================
# HEADER
# ==========================

st.title("✈ METAR REAL-TIME MONITORING SYSTEM")
st.caption("JUANDA INTERNATIONAL AIRPORT (WARR)")

st.write("🟢 MODE: PUBLIC VIEW")


# ==========================
# METAR TEXT
# ==========================

st.subheader("METAR Terbaru")

st.code(metar)


# ==========================
# DETAIL CUACA
# ==========================

c1,c2,c3 = st.columns(3)
c4,c5,c6 = st.columns(3)

c1.metric("Temperature", parsed.get("temp"))
c2.metric("Wind Dir", parsed.get("wind_dir"))
c3.metric("Visibility", parsed.get("vis"))

c4.metric("Dew Point", parsed.get("dew"))
c5.metric("Wind Speed", parsed.get("wind_speed"))
c6.metric("Pressure", parsed.get("qnh"))


# ==========================
# ALERT
# ==========================

st.subheader("Weather Alert")

alerts = []

if parsed.get("vis",9999) < 3000:
    alerts.append("Visibility rendah")

if parsed.get("wind_speed",0) > 20:
    alerts.append("Wind kuat")

if parsed.get("ts"):
    alerts.append("Thunderstorm / CB")

if parsed.get("vis",9999) < 5000 and parsed.get("wind_speed",0) > 15:
    alerts.append("Potensi holding")

if alerts:
    for a in alerts:
        st.warning(a)
else:
    st.success("No significant weather")


# ==========================
# GRAPH 24 JAM
# ==========================

st.subheader("Trend Cuaca")

if len(df) > 5:

    fig = px.line(
        df,
        x="time",
        y="temp",
        title="Temperature Trend"
    )

    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.line(
        df,
        x="time",
        y="qnh",
        title="Pressure Trend"
    )

    st.plotly_chart(fig2, use_container_width=True)


# ==========================
# HISTORY
# ==========================

st.subheader("METAR History")

st.dataframe(df)

st.download_button(
    "Download CSV",
    df.to_csv(index=False),
    file_name="metar_history.csv"
)


# ==========================
# AUTO REFRESH
# ==========================

st.autorefresh(interval=60000)


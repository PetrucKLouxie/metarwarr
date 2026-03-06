import streamlit as st
import pandas as pd
import requests
import re
import os
import base64
from datetime import datetime
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="METAR WARR Monitor", layout="wide")

STATION = "WARR"
CSV_FILE = "metar_history.csv"


# =========================
# GET METAR NOAA
# =========================

def get_metar():

    url = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{STATION}.TXT"

    r = requests.get(url, timeout=10)

    if r.status_code == 200:
        text = r.text.strip().split("\n")
        return text[-1]

    return None


# =========================
# PARSE METAR
# =========================

def parse_metar(metar):

    data = {}

    wind = re.search(r"(\d{3})(\d{2})KT", metar)
    if wind:
        data["wind_dir"] = wind.group(1)
        data["wind_speed"] = wind.group(2)

    vis = re.search(r" (\d{4}) ", metar)
    if vis:
        data["vis"] = vis.group(1)

    wx = re.search(r" (\+TSRA|-TSRA|TSRA|RA|SHRA|TS|HZ|BR|FG) ", metar)
    data["weather"] = wx.group(1) if wx else "NIL"

    cloud = re.search(r"(FEW|SCT|BKN|OVC)(\d{3})", metar)
    if cloud:
        height = int(cloud.group(2)) * 100
        data["cloud"] = f"{cloud.group(1)} {height}FT"

    temp = re.search(r" (\d{2})/(\d{2}) ", metar)
    if temp:
        data["temp"] = temp.group(1)
        data["dew"] = temp.group(2)

    qnh = re.search(r"Q(\d{4})", metar)
    if qnh:
        data["qnh"] = qnh.group(1)
    
    trend = re.search(r"(NOSIG|TEMPO.*)", metar)
    data["trend"] = trend.group(1) if trend else "NIL"
    
    time_match = re.search(r" (\d{2})(\d{2})(\d{2})Z ", metar)
    if time_match:
        data["day"] = time_match.group(1)
        data["hour"] = time_match.group(2)
        data["minute"] = time_match.group(3)

    return data


# =========================
# FORMAT QAM
# =========================

def get_metar_datetime(parsed):

    now = datetime.utcnow()

    day = int(parsed["day"])
    hour = int(parsed["hour"])
    minute = int(parsed["minute"])

    return metar_time
    
def format_qam(parsed):

    metar_time = get_metar_datetime(parsed)

    vis_km = float(parsed.get("vis", 0)) / 1000

    qam = f"""
📡 METAR UPDATE

MET REPORT (QAM)
BANDARA JUANDA WARR
DATE : {metar_time.strftime("%d/%m/%Y")}
TIME : {metar_time.strftime("%H.%M")} UTC
========================
WIND    : {parsed.get("wind_dir","-")}°/{parsed.get("wind_speed","-")} KT
VIS     : {vis_km} KM
WEATHER : {parsed.get("weather","NIL")}
CLOUD   : {parsed.get("cloud","-")}
TT/TD   : {parsed.get("temp","-")}/{parsed.get("dew","-")}
QNH     : {parsed.get("qnh","-")} MB
QFE     : {parsed.get("qnh","-")} MB
REMARKS : NIL
TREND   : {parsed.get("trend","-")}
"""

    return qam


# =========================
# INTERPRETASI
# =========================

def interpret(parsed):

    vis_km = float(parsed.get("vis",0))/1000

    wx_map = {
        "+TSRA":"badai petir kuat disertai hujan",
        "TSRA":"badai petir disertai hujan",
        "-TSRA":"badai petir ringan disertai hujan",
        "RA":"hujan",
        "SHRA":"hujan lokal",
        "FG":"kabut",
        "BR":"kabut tipis"
    }

    weather = wx_map.get(parsed.get("weather"),"tidak ada fenomena cuaca signifikan")

    return f"""
🧠 Interpretasi:
Observasi cuaca di Bandara WARR menunjukkan kondisi berikut:
Angin dari arah {parsed.get("wind_dir")}° dengan kecepatan {parsed.get("wind_speed")} knot.
Jarak pandang sekitar {vis_km} kilometer.
Fenomena cuaca berupa {weather}.
Terdapat awan {parsed.get("cloud")}.
Suhu {parsed.get("temp")}°C dengan titik embun {parsed.get("dew")}°C.
Tekanan udara {parsed.get("qnh")} hPa.
"""


# =========================
# WHATSAPP
# =========================

def send_whatsapp(message):

    token = st.secrets["FONNTE_TOKEN"]
    target = st.secrets["TARGET_WA"]

    url = "https://api.fonnte.com/send"

    payload = {
        "target": target,
        "message": message
    }

    headers = {"Authorization": token}

    requests.post(url, data=payload, headers=headers)


# =========================
# PUSH GITHUB
# =========================

def push_to_github():

    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]
    path = "metar_history.csv"

    with open(path, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    url = f"https://api.github.com/repos/{repo}/contents/{path}"

    headers = {"Authorization": f"token {token}"}

    r = requests.get(url, headers=headers)

    sha = None
    if r.status_code == 200:
        sha = r.json()["sha"]

    data = {
        "message": "METAR history update",
        "content": content,
        "branch": "main"
    }

    if sha:
        data["sha"] = sha

    requests.put(url, json=data, headers=headers)


# =========================
# LOAD HISTORY
# =========================

if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=["time","metar","temp","qnh"])


# =========================
# UPDATE METAR
# =========================

def update_metar():

    global df

    metar = get_metar()

    if metar is None:
        return None

    if len(df)==0 or metar != df.iloc[-1]["metar"]:

        parsed = parse_metar(metar)

        qam = format_qam(parsed)
        interp = interpret(parsed)

        msg = f"{qam}\n{interp}\n\n> _Sent via fonnte.com_"

        send_whatsapp(msg)

        new = {
            "time": datetime.utcnow(),
            "metar": metar,
            "temp": parsed.get("temp"),
            "qnh": parsed.get("qnh")
        }

        df.loc[len(df)] = new
        df.to_csv(CSV_FILE,index=False)

        push_to_github()

    return metar


@st.cache_data(ttl=60)
def get_latest():
    return update_metar()


# =========================
# RUN APP
# =========================

metar = get_latest()
parsed = parse_metar(metar)

st.title("✈ METAR REAL-TIME MONITORING SYSTEM")
st.caption("JUANDA INTERNATIONAL AIRPORT (WARR)")

st.subheader("METAR Terbaru")

st.code(metar)


# =========================
# METRICS
# =========================

c1,c2,c3 = st.columns(3)

c1.metric("Temperature", parsed.get("temp"))
c2.metric("Wind", f"{parsed.get('wind_dir')} / {parsed.get('wind_speed')} KT")
c3.metric("Pressure", parsed.get("qnh"))


# =========================
# QAM
# =========================

st.subheader("Format QAM")

st.code(format_qam(parsed))


# =========================
# INTERPRETASI
# =========================

st.subheader("Interpretasi")

st.write(interpret(parsed))


# =========================
# GRAPH
# =========================

st.subheader("Trend Cuaca")

df["time"] = pd.to_datetime(df["time"], errors="coerce")

fig = px.line(df, x="time", y="temp", title="Temperature Trend")

st.plotly_chart(fig, use_container_width=True)


# =========================
# HISTORY
# =========================

st.subheader("METAR History")

st.dataframe(df)

st.download_button(
    "Download CSV",
    df.to_csv(index=False),
    file_name="metar_history.csv"
)


# =========================
# AUTO REFRESH
# =========================

st.markdown(
"""
<meta http-equiv="refresh" content="60">
""",
unsafe_allow_html=True
)


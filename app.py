import streamlit as st
import pandas as pd
import requests
import re
import os
import base64
import math
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="METAR WARR Monitor", layout="wide")

STATION = "WARR"
RUNWAY_HEADING = 280
CSV_FILE = "metar_history.csv"


# =========================
# GET METAR NOAA
# =========================

def get_metar():

    url = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{STATION}.TXT"

    try:
        r = requests.get(url, timeout=10)

        if r.status_code == 200:
            text = r.text.strip().split("\n")
            return text[-1]

    except:
        return None


# =========================
# METAR PARSER (UPGRADED)
# =========================

def parse_metar(metar):

    data = {}

    # station
    data["station"] = metar.split()[0]

    # time
    t = re.search(r"(\d{2})(\d{2})(\d{2})Z", metar)
    if t:
        data["day"] = t.group(1)
        data["hour"] = t.group(2)
        data["minute"] = t.group(3)

    # wind
    wind = re.search(r"(\d{3}|VRB)(\d{2})(G\d{2})?KT", metar)
    if wind:

        data["wind_dir"] = wind.group(1)
        data["wind_speed"] = int(wind.group(2))

        if wind.group(3):
            data["gust"] = int(wind.group(3).replace("G",""))
        else:
            data["gust"] = None

    # visibility
    vis = re.search(r" (\d{4}) ", metar)

    if vis:
        data["vis"] = int(vis.group(1))

    if "9999" in metar:
        data["vis"] = 10000

    # weather
    wx = re.findall(r"(\+TSRA|-TSRA|TSRA|\+RA|-RA|RA|BR|FG|HZ|TS)", metar)

    data["weather"] = " ".join(wx) if wx else "NIL"

    # cloud
    cloud = re.findall(r"(FEW|SCT|BKN|OVC)(\d{3})(CB|TCU)?", metar)

    if cloud:
        c = cloud[0]
        height = int(c[1]) * 100
        data["cloud"] = f"{c[0]} {height}FT {c[2] if c[2] else ''}"

    # temperature
    temp = re.search(r" (\d{2})/(\d{2}) ", metar)

    if temp:
        data["temp"] = int(temp.group(1))
        data["dew"] = int(temp.group(2))

    # pressure
    qnh = re.search(r"Q(\d{4})", metar)

    if qnh:
        data["qnh"] = int(qnh.group(1))

    # trend
    trend = re.search(r"(NOSIG|TEMPO.*)", metar)

    data["trend"] = trend.group(1) if trend else "NIL"

    return data


# =========================
# CROSSWIND CALC
# =========================

def calculate_crosswind(wind_dir, wind_speed):

    try:

        angle = abs(wind_dir - RUNWAY_HEADING)

        angle_rad = math.radians(angle)

        cross = wind_speed * math.sin(angle_rad)

        return round(cross,1)

    except:
        return None


# =========================
# WEATHER ALERT
# =========================

def get_alert(parsed):

    alerts = []

    if "TS" in parsed.get("weather",""):
        alerts.append("⛈ THUNDERSTORM ALERT")

    if parsed.get("vis",10000) < 2000:
        alerts.append("⚠ LOW VISIBILITY")

    if parsed.get("gust"):
        alerts.append("🌬 WIND GUST")

    return alerts


# =========================
# HOLDING RISK
# =========================

def holding_risk(parsed):

    vis = parsed.get("vis",10000)

    wx = parsed.get("weather","")

    if vis < 1000 or "TS" in wx:
        return "HIGH"

    if vis < 3000:
        return "MEDIUM"

    return "LOW"


# =========================
# FORMAT QAM
# =========================

def format_qam(parsed):

    vis_km = parsed.get("vis",0) / 1000

    wind = f"{parsed.get('wind_dir')}°/{parsed.get('wind_speed')}KT"

    if parsed.get("gust"):
        wind += f"G{parsed.get('gust')}"

    qam = f"""
MET REPORT (QAM)
BANDARA JUANDA {STATION}

DATE : {parsed.get("day")}/{datetime.utcnow().strftime("%m/%Y")}
TIME : {parsed.get("hour")}.{parsed.get("minute")} UTC

========================

WIND    : {wind}
VIS     : {vis_km} KM
WEATHER : {parsed.get("weather")}
CLOUD   : {parsed.get("cloud")}
TT/TD   : {parsed.get("temp")}/{parsed.get("dew")}
QNH     : {parsed.get("qnh")} MB
TREND   : {parsed.get("trend")}
"""

    return qam

# =========================
# INTERPRETASI METAR
# =========================

def interpret_metar(parsed):

    text = []

    vis = parsed.get("vis",10000)
    weather = parsed.get("weather","NIL")
    cloud = parsed.get("cloud","NIL")
    wind_speed = parsed.get("wind_speed",0)

    # VISIBILITY
    if vis >= 8000:
        text.append("Visibilitas sangat baik dan tidak terdapat pembatas signifikan.")
    elif vis >= 3000:
        text.append("Visibilitas cukup baik namun terdapat sedikit reduksi jarak pandang.")
    else:
        text.append("Visibilitas rendah yang dapat mempengaruhi operasi penerbangan.")

    # WEATHER
    if "TS" in weather:
        text.append("Terdapat aktivitas thunderstorm di sekitar bandara yang berpotensi menimbulkan hujan lebat dan gusty wind.")
    elif "RA" in weather:
        text.append("Terdapat hujan yang dapat menyebabkan runway basah dan penurunan visibilitas.")
    elif "BR" in weather or "FG" in weather:
        text.append("Kabut atau mist terdeteksi yang dapat mengurangi jarak pandang horizontal.")
    else:
        text.append("Tidak terdapat fenomena cuaca signifikan.")

    # CLOUD
    if "BKN" in cloud or "OVC" in cloud:
        text.append("Tutupan awan cukup signifikan yang dapat mempengaruhi ceiling penerbangan.")
    else:
        text.append("Tutupan awan relatif ringan.")

    # WIND
    if wind_speed > 20:
        text.append("Kecepatan angin cukup kuat dan perlu diperhatikan pada saat takeoff maupun landing.")
    else:
        text.append("Kecepatan angin relatif normal untuk operasi penerbangan.")

    return " ".join(text)
    
# =========================
# WHATSAPP ALERT
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

    requests.post(url,data=payload,headers=headers)


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

        msg = f"{qam}\n\nSent via METAR Bot"

        send_whatsapp(msg)

        new = {

            "time": datetime.utcnow(),

            "metar": metar,

            "temp": parsed.get("temp"),

            "qnh": parsed.get("qnh")

        }

        df.loc[len(df)] = new

        df.to_csv(CSV_FILE,index=False)

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


st.code(metar)


# =========================
# ALERT
# =========================

alerts = get_alert(parsed)

for a in alerts:

    st.error(a)


# =========================
# METRICS
# =========================

c1,c2,c3,c4 = st.columns(4)

c1.metric("Temperature", parsed.get("temp"))

c2.metric("Pressure", parsed.get("qnh"))

wind_text = f"{parsed.get('wind_dir')} / {parsed.get('wind_speed')}KT"

if parsed.get("gust"):

    wind_text += f"G{parsed.get('gust')}"

c3.metric("Wind", wind_text)


cross = calculate_crosswind(int(parsed.get("wind_dir",0)), parsed.get("wind_speed",0))

c4.metric("Crosswind RWY28", f"{cross} KT")


# =========================
# HOLDING RISK
# =========================

risk = holding_risk(parsed)

if risk == "HIGH":

    st.error("🛬 HOLDING RISK HIGH")

elif risk == "MEDIUM":

    st.warning("⚠ HOLDING RISK MEDIUM")

else:

    st.success("✔ HOLDING RISK LOW")


# =========================
# QAM
# =========================

st.subheader("METAR QAM")

st.code(format_qam(parsed))

# =========================
# INTERPRETASI CUACA
# =========================

st.subheader("Interpretasi Kondisi Cuaca")

interpretasi = interpret_metar(parsed)

st.info(interpretasi)

# =========================
# GRAPH
# =========================

st.subheader("Trend Cuaca")

df["time"] = pd.to_datetime(df["time"],errors="coerce")

fig = px.line(df,x="time",y="temp",title="Temperature Trend")

st.plotly_chart(fig,use_container_width=True)


fig2 = px.line(df,x="time",y="qnh",title="Pressure Trend")

st.plotly_chart(fig2,use_container_width=True)


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


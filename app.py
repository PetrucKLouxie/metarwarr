import streamlit as st
import pandas as pd
import requests
import re
import os
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="METAR Aviation Monitor", layout="wide")

STATION="WARR"
CSV_FILE="metar_history.csv"

# =====================
# GET METAR
# =====================

def get_metar():

    url=f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{STATION}.TXT"

    r=requests.get(url,timeout=10)

    if r.status_code==200:
        text=r.text.strip().split("\n")
        return text[-1]

    return None


# =====================
# PARSE METAR
# =====================

def parse_metar(metar):

    data={}

    wind=re.search(r"(\d{3})(\d{2})KT",metar)
    if wind:
        data["wind_dir"]=int(wind.group(1))
        data["wind_speed"]=int(wind.group(2))

    vis=re.search(r" (\d{4}) ",metar)
    if vis:
        data["vis"]=int(vis.group(1))

    temp=re.search(r" (\d{2})/(\d{2}) ",metar)
    if temp:
        data["temp"]=int(temp.group(1))
        data["dew"]=int(temp.group(2))

    qnh=re.search(r"Q(\d{4})",metar)
    if qnh:
        data["qnh"]=int(qnh.group(1))

    wx=re.search(r" (\+TSRA|TSRA|-TSRA|RA|SHRA|TS|HZ|FG|BR) ",metar)
    data["weather"]=wx.group(1) if wx else "NIL"

    cloud=re.search(r"(FEW|SCT|BKN|OVC)(\d{3})",metar)
    if cloud:
        data["cloud"]=cloud.group(1)
        data["cloud_base"]=int(cloud.group(2))*100

    data["thunderstorm"]="TS" in metar or "CB" in metar

    return data


# =====================
# QAM FORMAT
# =====================

def format_qam(parsed):

    now=datetime.utcnow()

    vis_km=parsed.get("vis",0)/1000

    return f"""
📡 METAR UPDATE

MET REPORT (QAM)
BANDARA JUANDA WARR
DATE : {now.strftime("%d/%m/%Y")}
TIME : {now.strftime("%H.%M")} UTC
========================
WIND    : {parsed.get("wind_dir","-")}°/{parsed.get("wind_speed","-")} KT
VIS     : {vis_km} KM
WEATHER : {parsed.get("weather")}
CLOUD   : {parsed.get("cloud")} {parsed.get("cloud_base")}FT
TT/TD   : {parsed.get("temp")}/{parsed.get("dew")}
QNH     : {parsed.get("qnh")} MB
QFE     : {parsed.get("qnh")} MB
REMARKS : NIL
"""


# =====================
# INTERPRETASI
# =====================

def interpret(parsed):

    vis_km=parsed.get("vis",0)/1000

    wx_map={
        "+TSRA":"badai petir kuat disertai hujan",
        "TSRA":"badai petir disertai hujan",
        "-TSRA":"badai petir ringan disertai hujan",
        "RA":"hujan",
        "SHRA":"hujan lokal",
        "FG":"kabut"
    }

    weather=wx_map.get(parsed.get("weather"),"tidak ada fenomena cuaca signifikan")

    return f"""
🧠 Interpretasi:

Angin dari arah {parsed.get("wind_dir")}° dengan kecepatan {parsed.get("wind_speed")} knot.
Jarak pandang sekitar {vis_km} km.
Fenomena cuaca: {weather}.
Awan {parsed.get("cloud")} pada ketinggian {parsed.get("cloud_base")} kaki.
Suhu {parsed.get("temp")}°C dengan titik embun {parsed.get("dew")}°C.
Tekanan udara {parsed.get("qnh")} hPa.
"""


# =====================
# WHATSAPP
# =====================

def send_whatsapp(message):

    token=st.secrets["FONNTE_TOKEN"]
    target=st.secrets["TARGET_WA"]

    url="https://api.fonnte.com/send"

    headers={"Authorization":token}

    data={
        "target":target,
        "message":message
    }

    requests.post(url,data=data,headers=headers)


# =====================
# HISTORY
# =====================

if os.path.exists(CSV_FILE):
    df=pd.read_csv(CSV_FILE)
else:
    df=pd.DataFrame(columns=["time","metar","temp","vis","wind_speed","qnh"])


# =====================
# UPDATE
# =====================

def update_metar():

    global df

    metar=get_metar()

    if metar is None:
        return None

    if len(df)==0 or metar!=df.iloc[-1]["metar"]:

        parsed=parse_metar(metar)

        qam=format_qam(parsed)
        interp=interpret(parsed)

        msg=f"{qam}\n{interp}\n\n> _Sent via fonnte.com_"

        send_whatsapp(msg)

        new={
            "time":datetime.utcnow(),
            "metar":metar,
            "temp":parsed.get("temp"),
            "vis":parsed.get("vis"),
            "wind_speed":parsed.get("wind_speed"),
            "qnh":parsed.get("qnh")
        }

        df.loc[len(df)]=new
        df.to_csv(CSV_FILE,index=False)

    return metar


@st.cache_data(ttl=60)
def get_latest():
    return update_metar()


metar=get_latest()
parsed=parse_metar(metar)

st.title("✈ METAR AVIATION MONITOR")
st.caption("Juanda International Airport (WARR)")

st.code(metar)

# =====================
# METRICS
# =====================

c1,c2,c3,c4=st.columns(4)

c1.metric("Temperature",parsed.get("temp"))
c2.metric("Visibility",parsed.get("vis"))
c3.metric("Wind",parsed.get("wind_speed"))
c4.metric("Pressure",parsed.get("qnh"))

# =====================
# ALERT
# =====================

alerts=[]

if parsed.get("vis",9999)<3000:
    alerts.append("⚠ LOW VISIBILITY")

if parsed.get("wind_speed",0)>20:
    alerts.append("⚠ STRONG WIND")

if parsed.get("thunderstorm"):
    alerts.append("⛈ THUNDERSTORM DETECTED")

if alerts:
    for a in alerts:
        st.warning(a)
else:
    st.success("No significant weather")

# =====================
# GRAPH
# =====================

st.subheader("Weather Trend")

df["time"]=pd.to_datetime(df["time"])

fig=px.line(df,x="time",y="temp",title="Temperature Trend")

st.plotly_chart(fig,use_container_width=True)

# =====================
# HISTORY
# =====================

st.subheader("METAR History")

st.dataframe(df)

st.download_button("Download CSV",df.to_csv(index=False),"metar_history.csv")

# =====================
# AUTO REFRESH
# =====================

st.markdown(
"""
<meta http-equiv="refresh" content="60">
""",
unsafe_allow_html=True
)

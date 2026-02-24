import streamlit as st
import requests
import pandas as pd
import os
import base64
import streamlit.components.v1 as components
from datetime import datetime, timezone
from streamlit_autorefresh import st_autorefresh

# =========================
# CONFIG PAGE
# =========================
st.set_page_config(page_title="METAR Realtime Global", layout="wide")

st.markdown("""
<h1 style='text-align: center; color: #00FFAA;'>🛫 METAR REAL-TIME MONITORING SYSTEM</h1>
<h3 style='text-align:center; color:#DCDCDC;'>📍 JUANDA INTERNATIONAL AIRPORT (WARR)</h3>
<p style='text-align:center; color:#AAAAAA;'>Surabaya – Indonesia</p>
""", unsafe_allow_html=True)

# =========================
# DARK THEME (TETAP)
# =========================
st.markdown("""
<style>
.stApp { background-color: #0E1117; }
h1,h2,h3,h4 { color:#00FFAA; }
p,label,div { color:#E5E7EB; }
[data-testid="stMetric"] {
    background: linear-gradient(135deg,#1E293B,#0F172A);
    border:1px solid #1F2937;
    padding:20px;
    border-radius:15px;
}
div.stButton > button {
    background: linear-gradient(90deg,#00FFAA,#00CC88);
    color:black;
    border-radius:12px;
    font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

# =========================
# LOGIN ADMIN ONLY
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.subheader("🔐 Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if (
            username == st.secrets["ADMIN_USERNAME"]
            and password == st.secrets["ADMIN_PASSWORD"]
        ):
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Username atau password salah")

if not st.session_state.logged_in:
    login()
    st.stop()

with st.sidebar:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# =========================
# AUTO REFRESH
# =========================
st_autorefresh(interval=60000, key="refresh")

STATION_CODE = "WARR"
CSV_FILE = "metar_history.csv"

# =========================
# GET METAR
# =========================
def get_metar(station):
    try:
        url = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{station}.TXT"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.text.strip().split("\n")[-1]
    except:
        return None

# =========================
# PARSE METAR
# =========================
def parse_metar(metar):

    data = {
        "station":None,"day":None,"hour":None,"minute":None,
        "wind_dir":None,"wind_speed_kt":None,"visibility_m":None,
        "weather":None,"cloud":None,"temperature_c":None,
        "dewpoint_c":None,"pressure_hpa":None,"trend":None
    }

    parts = metar.replace("=", "").split()

    for part in parts:
        if len(part)==4 and part.isalpha():
            data["station"]=part
        if part.endswith("Z") and len(part)==7:
            data["day"]=part[0:2]
            data["hour"]=part[2:4]
            data["minute"]=part[4:6]
        if part.endswith("KT"):
            data["wind_dir"]=part[0:3]
            data["wind_speed_kt"]=part[3:5]
        if part.isdigit() and len(part)==4:
            data["visibility_m"]=int(part)
        if part.startswith(("FEW","SCT","BKN","OVC")):
            data["cloud"]=part
        if "/" in part and len(part)==5:
            t,d=part.split("/")
            data["temperature_c"]=t
            data["dewpoint_c"]=d
        if part.startswith("Q"):
            data["pressure_hpa"]=part[1:]
        if part=="NOSIG":
            data["trend"]=part

    return data

# =========================
# GENERATIVE TEXT
# =========================
def generate_narrative(p):
    text=[]
    text.append(f"Observasi cuaca di {p['station']} pukul {p['hour']}:{p['minute']} UTC.")
    text.append(f"Angin {p['wind_dir']} derajat dengan kecepatan {p['wind_speed_kt']} knot.")
    text.append(f"Visibilitas {p['visibility_m']} meter.")
    text.append(f"Suhu {p['temperature_c']}°C dengan titik embun {p['dewpoint_c']}°C.")
    text.append(f"Tekanan udara {p['pressure_hpa']} hPa.")
    if p["trend"]=="NOSIG":
        text.append("Tidak ada perubahan signifikan dalam waktu dekat.")
    return " ".join(text)

# =========================
# CSV SETUP
# =========================
if not os.path.exists(CSV_FILE):
    df_history=pd.DataFrame(columns=["station","time","metar"])
    df_history.to_csv(CSV_FILE,index=False)
else:
    df_history=pd.read_csv(CSV_FILE)

# =========================
# ENGINE
# =========================
metar_data=get_metar(STATION_CODE)

if metar_data:
    if len(df_history)==0 or df_history.iloc[-1]["metar"]!=metar_data:
        df_history=pd.concat([
            df_history,
            pd.DataFrame([{
                "station":STATION_CODE,
                "time":datetime.utcnow(),
                "metar":metar_data
            }])
        ],ignore_index=True)
        df_history.to_csv(CSV_FILE,index=False)

# =========================
# DISPLAY
# =========================
if len(df_history)>0:

    latest=df_history.iloc[-1]
    parsed=parse_metar(latest["metar"])
    narrative=generate_narrative(parsed)

    st.subheader(f"📡 METAR Terbaru - {latest['station']}")

    st.markdown(f"""
    <div style="background:#111827;padding:15px;border-radius:10px;
    font-family:monospace;color:#00FFAA;border:1px solid #1F2937;">
    {latest["metar"]}
    </div>
    """,unsafe_allow_html=True)

    col1,col2,col3=st.columns(3)
    col1.metric("🌡 Suhu (°C)",parsed["temperature_c"])
    col2.metric("💨 Wind (KT)",parsed["wind_speed_kt"])
    col3.metric("👁 Visibility (m)",parsed["visibility_m"])

    # =========================
    # FORMAT QAM
    # =========================
    qam_report=f"""MET REPORT (QAM)
BANDARA JUANDA {latest['station']}
WIND    : {parsed['wind_dir']}°/{parsed['wind_speed_kt']} KT
VIS     : {parsed['visibility_m']} M
TT/TD   : {parsed['temperature_c']}/{parsed['dewpoint_c']}
QNH     : {parsed['pressure_hpa']} MB
TREND   : {parsed['trend'] if parsed['trend'] else 'NIL'}
"""

    st.markdown("<hr>",unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center;'>🧾 Format QAM</h3>",unsafe_allow_html=True)

    st.markdown(f"""
    <div style="max-width:750px;margin:40px auto;
    background:linear-gradient(135deg,#0F172A,#111827);
    padding:35px;border-radius:25px;
    border:1px solid #1F2937;
    font-family:monospace;color:#00FFAA;
    white-space:pre-wrap;">
    {qam_report}
    </div>
    """,unsafe_allow_html=True)

    safe_qam=qam_report.replace("`","\\`")

    components.html(f"""
    <div style="text-align:center;">
    <button onclick="copyText()"
    style="background:linear-gradient(90deg,#00FFAA,#00CC88);
    color:black;border:none;padding:12px 25px;
    border-radius:12px;font-weight:bold;">
    📋 Copy QAM
    </button>
    </div>
    <script>
    function copyText() {{
        navigator.clipboard.writeText(`{safe_qam}`);
        alert("QAM berhasil dicopy!");
    }}
    </script>
    """,height=120)

    # =========================
    # GENERATIVE TEXT
    # =========================
    st.markdown("<hr>",unsafe_allow_html=True)
    st.subheader("🧠 Interpretasi METAR")
    st.write(narrative)

    # =========================
    # HISTORY
    # =========================
    with st.expander("📜 METAR History (Last 20 Records)"):
        st.table(df_history.tail(20))

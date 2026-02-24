import streamlit as st
import requests
import pandas as pd
import os
import base64
from datetime import datetime, timezone
from streamlit_autorefresh import st_autorefresh

# =========================
# CONFIG PAGE
# =========================
st.set_page_config(page_title="METAR Realtime Global", layout="wide")

# =========================
# LOGIN SYSTEM
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_form():
    st.sidebar.markdown("### 🔐 Admin Login")
    user = st.sidebar.text_input("Username")
    pw = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if (
            user == st.secrets["ADMIN_USERNAME"]
            and pw == st.secrets["ADMIN_PASSWORD"]
        ):
            st.session_state.logged_in = True
            st.sidebar.success("Login berhasil")
            st.rerun()
        else:
            st.sidebar.error("Login gagal")

    if st.session_state.logged_in:
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

login_form()

IS_ADMIN = st.session_state.logged_in

# =========================
# AUTO REFRESH
# =========================
st_autorefresh(interval=60000, key="refresh")

# =========================
# GET METAR
# =========================
def get_metar(station_code):
    try:
        url = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{station_code}.TXT"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.text.strip().split("\n")[-1]
    except:
        pass
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
        "wind_speed": None,
        "visibility": None,
        "weather": None,
        "cloud": None,
        "temp": None,
        "dew": None,
        "pressure": None,
        "trend": None
    }

    parts = metar.replace("=", "").split()

    for p in parts:

        if len(p) == 4 and p.isalpha():
            data["station"] = p

        if p.endswith("Z") and len(p) == 7:
            data["day"] = p[:2]
            data["hour"] = p[2:4]
            data["minute"] = p[4:6]

        if p.endswith("KT"):
            data["wind_dir"] = p[:3]
            data["wind_speed"] = p[3:5]

        if p.isdigit() and len(p) == 4:
            data["visibility"] = int(p)

        if p.startswith(("FEW","SCT","BKN","OVC")):
            data["cloud"] = p

        if "/" in p and len(p) == 5:
            t, d = p.split("/")
            data["temp"] = t
            data["dew"] = d

        if p.startswith("Q"):
            data["pressure"] = p[1:]

        if p in ["RA","+RA","-RA","TSRA","+TSRA","HZ"]:
            data["weather"] = p

        if p == "NOSIG":
            data["trend"] = p

    return data

# =========================
# GITHUB UPLOAD (ADMIN ONLY)
# =========================
def upload_to_github(file_path):

    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]
    path = st.secrets["GITHUB_FILE_PATH"]

    with open(file_path, "rb") as f:
        content = f.read()

    encoded = base64.b64encode(content).decode()

    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}"}

    r = requests.get(url, headers=headers)

    sha = None
    if r.status_code == 200:
        sha = r.json()["sha"]

    data = {
        "message": "Update METAR history",
        "content": encoded,
        "branch": "main"
    }

    if sha:
        data["sha"] = sha

    r = requests.put(url, headers=headers, json=data)
    return r.status_code

# =========================
# CSV INIT
# =========================
CSV_FILE = "metar_history.csv"

if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=["station","time","metar"]).to_csv(CSV_FILE,index=False)

df_history = pd.read_csv(CSV_FILE)

# =========================
# MAIN LOGIC
# =========================
station = "WARR"
metar = get_metar(station)

if metar:

    if len(df_history) == 0 or df_history.iloc[-1]["metar"] != metar:

        new_row = {
            "station": station,
            "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "metar": metar
        }

        df_history = pd.concat([df_history, pd.DataFrame([new_row])])
        df_history.to_csv(CSV_FILE, index=False)

        st.success("Data baru ditambahkan")

        if IS_ADMIN:
            status = upload_to_github(CSV_FILE)
            if status in [200,201]:
                st.success("GitHub updated")
            else:
                st.error("Upload GitHub gagal")

# =========================
# DISPLAY
# =========================
if len(df_history) > 0:

    latest = df_history.iloc[-1]
    parsed = parse_metar(latest["metar"])

    st.subheader("📡 METAR TERBARU")
    st.code(latest["metar"])

    col1,col2,col3 = st.columns(3)

    col1.metric("🌡 Temp (°C)", parsed["temp"])
    col1.metric("💧 Dew (°C)", parsed["dew"])

    col2.metric("💨 Wind Dir", parsed["wind_dir"])
    col2.metric("💨 Wind KT", parsed["wind_speed"])

    col3.metric("👁 Vis (m)", parsed["visibility"])
    col3.metric("📊 QNH", parsed["pressure"])

# =========================
# HISTORY
# =========================
with st.expander("📜 METAR History (Last 20)"):
    st.table(df_history.tail(20))

    with open(CSV_FILE, "rb") as f:
        st.download_button(
            "Download CSV",
            f,
            "metar_history.csv",
            "text/csv"
        )

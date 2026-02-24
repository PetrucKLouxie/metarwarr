import streamlit as st
import requests
import pandas as pd
import os
import base64
import streamlit.components.v1 as components
from datetime import datetime, timezone
from streamlit_autorefresh import st_autorefresh


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="METAR Realtime Global", layout="wide")


# =========================================================
# LOGIN SYSTEM (ADMIN ONLY)
# =========================================================
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
            st.success("Login berhasil!")
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


# =========================================================
# AUTO REFRESH
# =========================================================
st_autorefresh(interval=60000, key="refresh")


# =========================================================
# CONSTANT
# =========================================================
STATION_CODE = "WARR"
CSV_FILE = "metar_history.csv"


# =========================================================
# GET METAR
# =========================================================
def get_metar(station):
    try:
        url = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{station}.TXT"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.text.strip().split("\n")[-1]
        return None
    except:
        return None


# =========================================================
# TIME FORMAT
# =========================================================
def get_rounded_utc_time():
    now = datetime.now(timezone.utc)
    minute = 30 if now.minute >= 30 else 0
    return now.replace(minute=minute, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M UTC")


# =========================================================
# GITHUB UPLOAD
# =========================================================
def upload_to_github(file_path):

    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]
    github_path = st.secrets["GITHUB_FILE_PATH"]

    with open(file_path, "rb") as f:
        local_content = f.read()

    encoded_content = base64.b64encode(local_content).decode()

    url = f"https://api.github.com/repos/{repo}/contents/{github_path}"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        github_content = base64.b64decode(response.json()["content"])
        if github_content == local_content:
            return 999, "No changes detected"
        sha = response.json()["sha"]
    else:
        sha = None

    data = {
        "message": "Update METAR history CSV",
        "content": encoded_content,
        "branch": "main"
    }

    if sha:
        data["sha"] = sha

    r = requests.put(url, headers=headers, json=data)
    return r.status_code, r.json()


# =========================================================
# PARSE METAR
# =========================================================
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

    parts = metar.replace("=", "").split()

    for part in parts:

        if len(part) == 4 and part.isalpha():
            data["station"] = part

        if part.endswith("Z") and len(part) == 7:
            data["day"] = part[0:2]
            data["hour"] = part[2:4]
            data["minute"] = part[4:6]

        if part.endswith("KT"):
            data["wind_dir"] = part[0:3]
            data["wind_speed_kt"] = part[3:5]

        if part.isdigit() and len(part) == 4:
            data["visibility_m"] = int(part)

        if part.startswith(("FEW", "SCT", "BKN", "OVC")):
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


# =========================================================
# CSV SETUP
# =========================================================
if not os.path.exists(CSV_FILE):
    df_history = pd.DataFrame(columns=["station", "time", "metar"])
    df_history.to_csv(CSV_FILE, index=False)
else:
    df_history = pd.read_csv(CSV_FILE)


# =========================================================
# MAIN ENGINE
# =========================================================
metar_data = get_metar(STATION_CODE)

if metar_data:
    if len(df_history) == 0 or df_history.iloc[-1]["metar"] != metar_data:

        parsed = parse_metar(metar_data)

        new_row = {
            "station": STATION_CODE,
            "time": get_rounded_utc_time(),
            "metar": metar_data
        }

        df_history = pd.concat([df_history, pd.DataFrame([new_row])], ignore_index=True)
        df_history.to_csv(CSV_FILE, index=False)

        status, result = upload_to_github(CSV_FILE)

        if status == 999:
            st.info("Tidak ada perubahan.")
        elif status in [200, 201]:
            st.success("CSV berhasil diupdate ke GitHub!")
        else:
            st.error(result)


# =========================================================
# DISPLAY
# =========================================================
st.title("🛫 METAR REAL-TIME MONITORING SYSTEM")
st.subheader("JUANDA INTERNATIONAL AIRPORT (WARR)")

if len(df_history) > 0:
    latest = df_history.iloc[-1]
    parsed = parse_metar(latest["metar"])

    st.code(latest["metar"])

    col1, col2, col3 = st.columns(3)

    col1.metric("🌡 Suhu (°C)", parsed["temperature_c"])
    col2.metric("💨 Wind (KT)", parsed["wind_speed_kt"])
    col3.metric("👁 Visibility (m)", parsed["visibility_m"])

    with st.expander("📜 METAR History (Last 20 Records)"):
        st.table(df_history.tail(20))

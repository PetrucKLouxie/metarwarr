import streamlit as st
import requests
import pandas as pd
import os
import re
import base64
import streamlit.components.v1 as components
from datetime import datetime, timezone
from streamlit_autorefresh import st_autorefresh

# =========================
# CONFIG PAGE
# =========================
st.set_page_config(page_title="METAR Realtime Global", layout="wide")
st.markdown("""
<h1 style='text-align: center; color: #00FFAA;'>
🛫 METAR REAL-TIME MONITORING SYSTEM
</h1>
<h3 style='text-align:center; color:#DCDCDC;'>
📍 JUANDA INTERNATIONAL AIRPORT (WARR)
</h3>
<p style='text-align:center; color:#AAAAAA;'>
Surabaya – Indonesia
</p>
""", unsafe_allow_html=True)

st.markdown("""
<style>

/* Expander container */
[data-testid="stExpander"] {
    background-color: #0F172A !important;
    border: 1px solid #1F2937 !important;
    border-radius: 20px !important;
}

/* Expander header */
[data-testid="stExpander"] summary {
    background-color: #0F172A !important;
    color: #00FFAA !important;
    border-radius: 20px !important;
}

/* Hilangkan strip putih */
[data-testid="stExpander"] > div:first-child {
    background-color: transparent !important;
}
/* =========================
   SIDEBAR DARK MODE
========================= */

section[data-testid="stSidebar"] {
    background-color: #0F172A !important;
}

section[data-testid="stSidebar"] * {
    color: #E5E7EB !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label {
    font-size: 20px !important;
    font-weight: 600 !important;
    display: block;
    padding: 12px 10px;
    border-radius: 10px;
    transition: 0.3s;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background-color: #1F2937;
}

/* Input di sidebar */
section[data-testid="stSidebar"] input {
    background-color: #1F2937 !important;
    color: white !important;
    border-radius: 8px !important;
    border: 1px solid #334155 !important;
}

/* Tombol di sidebar */
section[data-testid="stSidebar"] button {
    background: linear-gradient(90deg,#00FFAA,#00CC88) !important;
    color: black !important;
    border-radius: 10px !important;
    font-weight: bold !important;
}

/* Header sidebar */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #00FFAA !important;
}
/* Table full dark */
table {
    background-color: #0F172A !important;
    color: #E5E7EB !important;
}

thead th {
    background-color: #111827 !important;
    color: #00FFAA !important;
}

tbody td {
    background-color: #0F172A !important;
    color: #E5E7EB !important;
}

    /* Background utama */
    .stApp {
        background-color: #0E1117;
    }

    /* Container */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Header & Text */
    h1, h2, h3, h4 {
        color: #00FFAA;
    }

    p, label, div {
        color: #E5E7EB;
    }

    /* Code block */
    div[data-testid="stCodeBlock"] {
        background-color: #111827;
        border-radius: 10px;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1F2937, #111827);
        padding: 20px;
        border-radius: 12px;
    }

    /* Text area */
    textarea {
        background-color: #111827 !important;
        color: #00FFAA !important;
        font-family: monospace;
    }

    /* Input box */
    input {
        background-color: #1F2937 !important;
        color: white !important;
    }

    /* Status bar */
    .status-box {
        background: linear-gradient(90deg, #065F46, #064E3B);
        padding: 10px;
        border-radius: 8px;
        font-weight: bold;
}
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1E293B, #0F172A);
    border: 1px solid #1F2937;
    padding: 20px;
    border-radius: 15px;
    transition: 0.3s;
    }

    [data-testid="stMetric"]:hover {
        transform: scale(1.02);
    }
    div.stButton > button {
        background: linear-gradient(90deg,#00FFAA,#00CC88);
        color: black;
        border-radius: 12px;
        font-weight: bold;
    }
    div.stDownloadButton > button {
        background: linear-gradient(90deg,#00FFAA,#00CC88);
        color: black;
        font-weight: bold;
        border-radius: 15px;
        padding: 12px;
    }

    div.stDownloadButton > button:hover {
        background: linear-gradient(90deg,#00CC88,#00FFAA);
    }
</style>
""", unsafe_allow_html=True)
# =========================
# ADMIN LOGIN SYSTEM
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
            st.success("Login berhasil!")
            st.rerun()
        else:
            st.error("Username atau password salah")

# 🔥 BLOCK TOTAL kalau belum login
# =========================
# ADMIN LOGIN SYSTEM (PUBLIC VIEW MODE)
# =========================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "show_login" not in st.session_state:
    st.session_state.show_login = False

# =========================
# SIDEBAR MENU SYSTEM
# =========================
with st.sidebar:

    # ===== LOGO CENTER =====
    st.markdown("""
        <div style='text-align:center;'>
            <img src="https://upload.wikimedia.org/wikipedia/commons/6/6e/Logo_BMKG.png" width="110">
            <h4 style='margin-top:10px;'>BMKG JUANDA</h4>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ===== MENU =====
    menu = st.radio(
        "",
        ["Dashboard", "Data"],
        label_visibility="collapsed"
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ===== ADMIN PANEL =====
    st.markdown("### 🔐 Admin Panel")

    if not st.session_state.logged_in:
        if st.button("Admin Login"):
            st.session_state.show_login = True

    if st.session_state.logged_in:
        st.success("Admin Active")
        if st.button("Logout", key="logout_sidebar"):
            st.session_state.logged_in = False
            st.rerun()

# Login form muncul kalau ditekan
if st.session_state.show_login and not st.session_state.logged_in:

    st.sidebar.markdown("#### Login Required")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Submit Login"):
        if (
            username == st.secrets["ADMIN_USERNAME"]
            and password == st.secrets["ADMIN_PASSWORD"]
        ):
            st.session_state.logged_in = True
            st.session_state.show_login = False
            st.rerun()
        else:
            st.sidebar.error("Username / Password salah")

if st.session_state.logged_in:
    st.markdown("🟢 **MODE: ADMIN**")
else:
    st.markdown("🌍 **MODE: PUBLIC VIEW**")

# =========================
# PAGE ROUTING
# =========================

if menu == "📊 Dashboard":
    st.session_state.page = "dashboard"

elif menu == "⚙️ Generate Data":
    st.session_state.page = "generate"

# =========================
# SESSION STATE INIT
# =========================

if "last_wa_sent" not in st.session_state:
    st.session_state.last_wa_sent = None

# =========================
# AUTO REFRESH 1 MENIT
# =========================
st_autorefresh(interval=60000, key="refresh")

# =========================
# INPUT ICAO
# =========================
station_code = "WARR"

# =========================
# GET METAR FROM NOAA
# =========================
def get_metar(station_code):
    try:
        url = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{station_code.upper()}.TXT"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            lines = response.text.strip().split("\n")
            return lines[-1]

        return None
    except:
        return None

# =========================
# ROUND UTC 00 / 30
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
# GENERATE NARRATIVE TEXT
# =========================
def generate_metar_narrative(parsed, tempo=None):

    if not parsed["station"]:
        return "Data METAR tidak valid."

    text = []

    text.append(
        f"Observasi cuaca di Bandara {parsed['station']} "
        f"pada tanggal {parsed['day']} pukul {parsed['hour']}:{parsed['minute']} UTC menunjukkan kondisi berikut:"
    )

    if parsed["wind_dir"] and parsed["wind_speed_kt"]:
        text.append(
            f"Angin dari arah {parsed['wind_dir']} derajat "
            f"dengan kecepatan {parsed['wind_speed_kt']} knot."
        )

    if parsed["visibility_m"]:
        km = parsed["visibility_m"] / 1000
        text.append(f"Jarak pandang sekitar {km:.1f} kilometer.")

    weather_map = {
        "HZ": "kabut asap",
        "RA": "hujan",
        "+RA": "hujan lebat",
        "-RA": "hujan ringan",
        "TSRA": "badai petir disertai hujan",
        "+TSRA": "badai petir kuat disertai hujan"
    }

    if parsed["weather"]:
        desc = weather_map.get(parsed["weather"], parsed["weather"])
        text.append(f"Terdapat fenomena cuaca berupa {desc}.")

    if parsed["cloud"]:
        amount = parsed["cloud"][:3]
        height = int(parsed["cloud"][3:6]) * 100
        text.append(f"Awan {amount} pada ketinggian {height} kaki.")

    if parsed["temperature_c"] and parsed["dewpoint_c"]:
        text.append(
            f"Suhu {parsed['temperature_c']}°C dengan titik embun {parsed['dewpoint_c']}°C."
        )

    if parsed["pressure_hpa"]:
        text.append(f"Tekanan udara {parsed['pressure_hpa']} hPa.")

    if tempo:
        text.append(
            f"Hingga {tempo['until']} UTC diperkirakan visibilitas "
            f"{tempo['visibility']} meter dengan kondisi {tempo['weather']}."
        )
    elif parsed["trend"] == "NOSIG":
        text.append("Tidak ada perubahan signifikan dalam waktu dekat.")

    return " ".join(text)
# =========================
# =========================
# CSV SETUP (READ ONLY)
# =========================
CSV_FILE = "metar_history.csv"

if os.path.exists(CSV_FILE):
    df_history = pd.read_csv(CSV_FILE)
else:
    df_history = pd.DataFrame(columns=["station","time","metar"])
# =========================
# DISPLAY LATEST
# =========================
if len(df_history) > 0:

    latest = df_history.iloc[-1]
    parsed = parse_metar(latest["metar"])
    tempo = parse_tempo_section(latest["metar"])
    narrative = generate_metar_narrative(parsed, tempo)

    # =========================
# DASHBOARD PAGE
# =========================
if menu == "📊 Dashboard":

    # =========================
    # 1️⃣ RAW METAR
    # =========================
    st.subheader(f"📡 METAR Terbaru - {latest['station']}")
    st.markdown(f"""
    <div style="
    background: #111827;
    padding:15px;
    border-radius:10px;
    font-family: monospace;
    color:#00FFAA;
    border:1px solid #1F2937;
    ">
    {latest["metar"]}
    </div>
    """, unsafe_allow_html=True)
    status_color = "#16A34A"  # hijau default

    if parsed["weather"] in ["TSRA","+TSRA"]:
        status_color = "#DC2626"
    elif parsed["visibility_m"] and parsed["visibility_m"] < 5000:
        status_color = "#F59E0B"

    st.markdown(f"""
    <div style="
    background:{status_color};
    padding:8px 15px;
    border-radius:8px;
    color:white;
    font-weight:600;
    display:inline-block;
    ">
    ● STATUS: OPERATIONAL
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # 2️⃣ VISUALISASI METRIC
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
    # 3️⃣ FORMAT QAM
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

    trend_text = parsed["trend"] if parsed["trend"] else "NIL"
    if tempo:
        trend_text = f"TEMPO TL{tempo['until']} {tempo['visibility']} {tempo['weather']}"

    qam_report = f"""MET REPORT (QAM)
BANDARA JUANDA {latest['station']}
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

    st.markdown("<hr style='border: 1px solid #333;'>", unsafe_allow_html=True)
# =========================
# FORMAT QAM CENTERED CLEAN
# =========================

    st.markdown("<hr style='border:1px solid #1F2937;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center;'>🧾 Format QAM</h3>", unsafe_allow_html=True)

    clean_qam = qam_report.replace("`", "").strip()

    st.markdown(f"""
    <div style="
    max-width:750px;
    margin:40px auto 20px auto;
    background:linear-gradient(135deg,#0F172A,#111827);
    padding:35px;
    border-radius:25px;
    box-shadow:0 15px 40px rgba(0,0,0,0.6);
    border:1px solid #1F2937;
    font-family:monospace;
    color:#00FFAA;
    white-space:pre-wrap;
    line-height:1.6;
    ">
    {clean_qam}
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2,3,2])

    with col2:

        safe_qam = qam_report.replace("`", "\\`")

        copy_html = f"""
        <div style="text-align:center; margin-top:20px;">
            <button onclick="copyText()" 
                style="
                background: linear-gradient(90deg,#00FFAA,#00CC88);
                color: black;
                border: none;
                padding: 12px 25px;
                border-radius: 12px;
                font-weight: bold;
                cursor: pointer;
                ">
                📋 Copy QAM
            </button>
        </div>

        <script>
        function copyText() {{
            const text = `{safe_qam}`;
            navigator.clipboard.writeText(text).then(function() {{
                alert("QAM berhasil dicopy!");
            }});
        }}
        </script>
        """

        components.html(copy_html, height=120)
    # =========================
    # 4️⃣ GENERATIVE TEXT
    # =========================
    st.markdown("<hr style='border: 1px solid #333;'>", unsafe_allow_html=True)
    st.subheader("🧠 Interpretasi METAR")
    st.write(narrative)

    # =========================
    # 5️⃣ HISTORI DATA
    # =========================

    st.markdown("<hr style='border:1px solid #1F2937;'>", unsafe_allow_html=True)

    with st.expander("📜 METAR History ", expanded=False):

        st.markdown("### 📊 Latest 20 Records")
        st.caption(f"Total records stored: {len(df_history)}")

        styled_df = df_history.tail(20).style.set_table_styles([
            {"selector": "thead th", "props": [
                ("background-color", "#111827"),
                ("color", "#00FFAA"),
                ("border", "1px solid #1F2937")
            ]},
            {"selector": "tbody td", "props": [
                ("background-color", "#0F172A"),
                ("color", "#E5E7EB"),
                ("border", "1px solid #1F2937")
            ]}
        ])

        st.table(styled_df)

    st.markdown("<br>", unsafe_allow_html=True)

    with open(CSV_FILE, "rb") as file:
        st.download_button(
            label="⬇ Download METAR Record (CSV)",
            data=file,
            file_name="metar_history.csv",
            mime="text/csv",
            use_container_width=True
        )
# =========================
# GENERATE DATA PAGE
# =========================
elif menu == "⚙️ Generate Data":

    st.title("⚙️ Generate Data")
    st.write("Fitur generate data sementara.")

    if st.button("Generate Dummy METAR"):
        st.success("Data berhasil digenerate!")


























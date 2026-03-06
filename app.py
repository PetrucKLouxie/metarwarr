# metarwarr - FUTURISTIC BRIGHT THEME
import streamlit as st
import pandas as pd
import requests
import re
import os
import base64
import math
from datetime import datetime
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="METAR WARR Monitor",
    page_icon="✈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# CUSTOM CSS - FUTURISTIC BRIGHT THEME
# =========================
st.markdown("""
<style>
    /* Google Fonts Import */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');

    /* Main Theme Variables */
    :root {
        --primary: #00B4D8;
        --secondary: #0077B6;
        --accent: #00F5D4;
        --bg-gradient-start: #F0F8FF;
        --bg-gradient-end: #E8F4FD;
        --text-dark: #1A1A2E;
        --text-light: #4A5568;
        --card-bg: rgba(255, 255, 255, 0.95);
        --neon-glow: 0 0 20px rgba(0, 180, 216, 0.3);
        --neon-glow-strong: 0 0 30px rgba(0, 180, 216, 0.5);
    }

    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, var(--bg-gradient-start) 0%, var(--bg-gradient-end) 100%);
        font-family: 'Rajdhani', sans-serif;
    }

    /* Title Styling */
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        color: var(--text-dark) !important;
        font-weight: 700 !important;
    }

    h1 {
        text-shadow: var(--neon-glow);
        background: linear-gradient(90deg, var(--secondary), var(--primary), var(--accent));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* Custom Card Styling */
    .futuristic-card {
        background: var(--card-bg);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 180, 216, 0.15);
        border: 2px solid transparent;
        background-image: linear-gradient(white, white), linear-gradient(135deg, var(--primary), var(--accent));
        background-origin: border-box;
        background-clip: padding-box, border-box;
        transition: all 0.3s ease;
    }

    .futuristic-card:hover {
        box-shadow: var(--neon-glow-strong);
        transform: translateY(-2px);
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F0F8FF 100%);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        border: 2px solid var(--primary);
        box-shadow: var(--neon-glow);
        transition: all 0.3s ease;
    }

    .metric-card:hover {
        box-shadow: var(--neon-glow-strong);
        transform: scale(1.02);
    }

    .metric-label {
        font-family: 'Orbitron', sans-serif;
        font-size: 12px;
        color: var(--secondary);
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    .metric-value {
        font-family: 'Orbitron', sans-serif;
        font-size: 28px;
        font-weight: 700;
        color: var(--primary);
        text-shadow: var(--neon-glow);
    }

    /* Alert Boxes */
    .alert-box {
        padding: 15px 20px;
        border-radius: 12px;
        font-weight: 600;
        margin: 10px 0;
        animation: pulse 2s infinite;
        font-family: 'Rajdhani', sans-serif;
    }

    .alert-warning {
        background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
        border: 2px solid #F59E0B;
        color: #92400E;
    }

    .alert-error {
        background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%);
        border: 2px solid #EF4444;
        color: #991B1B;
    }

    .alert-success {
        background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%);
        border: 2px solid #10B981;
        color: #065F46;
    }

    /* Code Block Styling */
    .stCodeBlock {
        background: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%) !important;
        border-radius: 12px !important;
        border: 2px solid var(--primary) !important;
    }

    .stCodeBlock code {
        color: #00F5D4 !important;
        font-family: 'Fira Code', monospace !important;
    }

    /* Live Clock */
    .live-clock {
        font-family: 'Orbitron', sans-serif;
        font-size: 24px;
        color: var(--primary);
        text-align: right;
        padding: 10px;
        text-shadow: var(--neon-glow);
        animation: glow 1.5s ease-in-out infinite alternate;
    }

    @keyframes glow {
        from { text-shadow: 0 0 10px var(--primary); }
        to { text-shadow: 0 0 20px var(--accent), 0 0 30px var(--primary); }
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }

    @keyframes slideIn {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }

    /* Header Section */
    .header-section {
        background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(240,248,255,0.9) 100%);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 20px;
        border: 2px solid var(--primary);
        box-shadow: var(--neon-glow);
    }

    .logo-container {
        display: flex;
        align-items: center;
        gap: 15px;
    }

    .logo-icon {
        font-size: 48px;
        animation: pulse 2s infinite;
    }

    .title-container h1 {
        margin: 0;
        font-size: 32px;
    }

    .title-container p {
        margin: 5px 0 0 0;
        color: var(--text-light);
        font-size: 16px;
    }

    /* Status Indicator */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%);
        border-radius: 20px;
        border: 2px solid #10B981;
        font-family: 'Orbitron', sans-serif;
        font-size: 12px;
        color: #065F46;
    }

    .status-dot {
        width: 10px;
        height: 10px;
        background: #10B981;
        border-radius: 50%;
        animation: blink 1s infinite;
    }

    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }

    /* DataFrame Styling */
    .stDataFrame {
        border-radius: 12px;
        border: 2px solid var(--primary);
    }

    /* Section Headers */
    .section-header {
        font-family: 'Orbitron', sans-serif;
        font-size: 20px;
        color: var(--secondary) !important;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid var(--primary);
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .section-icon {
        font-size: 24px;
    }

    /* Info Box */
    .info-box {
        background: linear-gradient(135deg, #E0F2FE 0%, #BAE6FD 100%);
        border-radius: 12px;
        padding: 15px;
        border-left: 4px solid var(--primary);
        font-size: 15px;
        line-height: 1.6;
    }

    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-family: 'Orbitron', sans-serif;
        font-size: 14px;
        transition: all 0.3s ease;
        box-shadow: var(--neon-glow);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--neon-glow-strong);
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #F0F8FF 0%, #E8F4FD 100%);
        border-right: 2px solid var(--primary);
    }

    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #F0F8FF;
    }
    ::-webkit-scrollbar-thumb {
        background: var(--primary);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--secondary);
    }
</style>
""", unsafe_allow_html=True)

# =========================
# JAVASCRIPT FOR CLOCK & ANIMATIONS
# =========================
st.markdown("""
<script>
    // Live Clock Function
    function updateClock() {
        const now = new Date();
        const hours = String(now.getUTCHours()).padStart(2, '0');
        const minutes = String(now.getUTCMinutes()).padStart(2, '0');
        const seconds = String(now.getUTCSeconds()).padStart(2, '0');
        const timeString = hours + ':' + minutes + ':' + seconds + ' UTC';
        
        const clockElement = document.getElementById('liveClock');
        if (clockElement) {
            clockElement.textContent = timeString;
        }
    }
    
    // Update clock every second
    setInterval(updateClock, 1000);
    updateClock();
</script>
""", unsafe_allow_html=True)

# =========================
# CONSTANTS
# =========================
STATION = "WARR"
RUNWAY_HEADING = 280
CSV_FILE = "metar_history.csv"

# =========================
# AUTO REFRESH (60 seconds)
# =========================
count = st_autorefresh(interval=60000, limit=None, key="metar_refresh")

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
    data["station"] = metar.split()[0]
    
    t = re.search(r"(\d{2})(\d{2})(\d{2})Z", metar)
    if t:
        data["day"] = t.group(1)
        data["hour"] = t.group(2)
        data["minute"] = t.group(3)
    
    wind = re.search(r"(\d{3}|VRB)(\d{2})(G\d{2})?KT", metar)
    if wind:
        data["wind_dir"] = wind.group(1)
        data["wind_speed"] = int(wind.group(2))
        if wind.group(3):
            data["gust"] = int(wind.group(3).replace("G",""))
        else:
            data["gust"] = None
    
    vis = re.search(r" (\d{4}) ", metar)
    if vis:
        data["vis"] = int(vis.group(1))
    if "9999" in metar:
        data["vis"] = 10000
    
    wx = re.findall(r"(\+TSRA|-TSRA|TSRA|\+RA|-RA|RA|BR|FG|HZ|TS)", metar)
    data["weather"] = " ".join(wx) if wx else "NIL"
    
    cloud = re.findall(r"(FEW|SCT|BKN|OVC)(\d{3})(CB|TCU)?", metar)
    if cloud:
        c = cloud[0]
        height = int(c[1]) * 100
        data["cloud"] = f"{c[0]} {height}FT {c[2] if c[2] else ''}"
    
    temp = re.search(r" (\d{2})/(\d{2}) ", metar)
    if temp:
        data["temp"] = int(temp.group(1))
        data["dew"] = int(temp.group(2))
    
    qnh = re.search(r"Q(\d{4})", metar)
    if qnh:
        data["qnh"] = int(qnh.group(1))
    
    trend = re.search(r"(NOSIG|TEMPO.*)", metar)
    data["trend"] = trend.group(1) if trend else "NIL"
    
    return data

# =========================
# CROSSWIND CALC
# =========================
def calculate_crosswind(wind_dir, wind_speed):
    try:
        angle = abs(int(wind_dir) - RUNWAY_HEADING)
        angle_rad = math.radians(angle)
        cross = wind_speed * math.sin(angle_rad)
        return round(cross, 1)
    except:
        return None

# =========================
# WEATHER ALERT
# =========================
def get_alert(parsed):
    alerts = []
    if "TS" in parsed.get("weather",""):
        alerts.append("⛈ THUNDERSTORM ALERT - Aktivitas badai petir terdeteksi!")
    if parsed.get("vis",10000) < 2000:
        alerts.append("⚠ LOW VISIBILITY - Visibilitas rendah!")
    if parsed.get("gust"):
        alerts.append("🌬 WIND GUST - Angin kencang terdeteksi!")
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
╔══════════════════════════════════════╗
║     MET REPORT (QAM) - {STATION}         ║
║     BANDARA JUANDA INTERNASIONAL     ║
╠══════════════════════════════════════╣
║ DATE : {parsed.get("day")}/{datetime.utcnow().strftime("%m/%Y")}                      ║
║ TIME : {parsed.get("hour")}.{parsed.get("minute")} UTC                       ║
╠══════════════════════════════════════╣
║ WIND    : {wind:<25} ║
║ VIS     : {vis_km} KM                        ║
║ WEATHER : {parsed.get("weather"):<25} ║
║ CLOUD   : {parsed.get("cloud"):<25} ║
║ TT/TD   : {parsed.get("temp")}°C/{parsed.get("dew")}°C                      ║
║ QNH     : {parsed.get("qnh")} MB                      ║
║ TREND   : {parsed.get("trend"):<25} ║
╚══════════════════════════════════════╝
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

    if vis >= 8000:
        text.append("✅ Visibilitas sangat baik (>8km).")
    elif vis >= 3000:
        text.append("⚠️ Visibilitas cukup baik (3-8km).")
    else:
        text.append("❌ Visibilitas rendah (<3km) - dapat mempengaruhi operasi penerbangan.")

    if "TS" in weather:
        text.append("⛈️ THUNDERSTORM: Aktivitas badai petir di sekitar bandara.")
    elif "RA" in weather:
        text.append("🌧️ Hujan: Runway berpotensi basah.")
    elif "BR" in weather or "FG" in weather:
        text.append("🌫️ Kabut/Mist: Jarak pandang berkurang.")
    else:
        text.append("☀️ Tidak ada fenomena cuaca signifikan.")

    if "BKN" in cloud or "OVC" in cloud:
        text.append("☁️ Tutupan awan signifikan - perhatikan ceiling.")
    else:
        text.append("🌤️ Tutupan awan relatif ringan.")

    if wind_speed > 20:
        text.append("💨 Kecepatan angin tinggi (>20kt) - perhatikan saat takeoff/landing.")
    else:
        text.append("🍃 Kecepatan angin normal untuk operasi.")

    return " ".join(text)

# =========================
# WHATSAPP ALERT
# =========================
def send_whatsapp(message):
    try:
        token = st.secrets["FONNTE_TOKEN"]
        target = st.secrets["TARGET_WA"]
        url = "https://api.fonnte.com/send"
        payload = {"target": target, "message": message}
        headers = {"Authorization": token}
        requests.post(url, data=payload, headers=headers)
    except:
        pass  # Silent fail if no WhatsApp config

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
        df.to_csv(CSV_FILE, index=False)
    return metar

@st.cache_data(ttl=60)
def get_latest():
    return update_metar()

# =========================
# RUN APP
# =========================
metar = get_latest()
parsed = parse_metar(metar)

# =========================
# HEADER SECTION
# =========================
st.markdown(f"""
<div class="header-section">
    <div class="logo-container">
        <div class="logo-icon">✈️</div>
        <div class="title-container">
            <h1>🚀 METAR REAL-TIME MONITORING</h1>
            <p>🎯 JUANDA INTERNATIONAL AIRPORT (WARR) | SIDOARJO, EAST JAVA</p>
        </div>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px;">
        <div class="status-indicator">
            <span class="status-dot"></span>
            LIVE MONITORING ACTIVE
        </div>
        <div class="live-clock" id="liveClock">--:--:-- UTC</div>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================
# METAR RAW DATA
# =========================
st.markdown('<div class="section-header"><span class="section-icon">📡</span> RAW METAR DATA</div>', unsafe_allow_html=True)
st.code(metar, language="text")

# =========================
# ALERTS
# =========================
alerts = get_alert(parsed)
if alerts:
    for a in alerts:
        st.markdown(f'<div class="alert-box alert-warning">{a}</div>', unsafe_allow_html=True)

# =========================
# METRICS DASHBOARD
# =========================
st.markdown('<div class="section-header"><span class="section-icon">📊</span> WEATHER METRICS</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">🌡️ Temperature</div>
        <div class="metric-value">{parsed.get("temp")}°C</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">🔵 Pressure (QNH)</div>
        <div class="metric-value">{parsed.get("qnh")} hPa</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    wind_text = f"{parsed.get('wind_dir')}° / {parsed.get('wind_speed')}KT"
    if parsed.get("gust"):
        wind_text += f" G{parsed.get('gust')}"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">💨 Wind</div>
        <div class="metric-value" style="font-size: 20px;">{wind_text}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    cross = calculate_crosswind(int(parsed.get("wind_dir",0)), parsed.get("wind_speed",0))
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">🛫 Crosswind RWY28</div>
        <div class="metric-value">{cross} KT</div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# HOLDING RISK
# =========================
st.markdown('<div class="section-header"><span class="section-icon">⚠️</span> HOLDING RISK ASSESSMENT</div>', unsafe_allow_html=True)

risk = holding_risk(parsed)
if risk == "HIGH":
    st.markdown('<div class="alert-box alert-error">🛑 HOLDING RISK: HIGH - Kondisi tidak menguntungkan untuk holding!</div>', unsafe_allow_html=True)
elif risk == "MEDIUM":
    st.markdown('<div class="alert-box alert-warning">⚠️ HOLDING RISK: MEDIUM - Harap berhati-hati!</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="alert-box alert-success">✅ HOLDING RISK: LOW - Kondisi normal untuk operasi.</div>', unsafe_allow_html=True)

# =========================
# QAM FORMAT
# =========================
st.markdown('<div class="section-header"><span class="section-icon">📋</span> METAR QAM FORMAT</div>', unsafe_allow_html=True)
st.code(format_qam(parsed), language="text")

# =========================
# INTERPRETASI CUACA
# =========================
st.markdown('<div class="section-header"><span class="section-icon">🔍</span> INTERPRETASI KONDISI CUACA</div>', unsafe_allow_html=True)
interpretasi = interpret_metar(parsed)
st.markdown(f'<div class="info-box">{interpretasi}</div>', unsafe_allow_html=True)

# =========================
# CHARTS - FUTURISTIC STYLE
# =========================
st.markdown('<div class="section-header"><span class="section-icon">📈</span> WEATHER TRENDS</div>', unsafe_allow_html=True)

df["time"] = pd.to_datetime(df["time"], errors="coerce")
df = df.dropna(subset=["time"])

# Custom Plotly template
futuristic_template = {
    "layout": {
        "paper_bgcolor": "rgba(255,255,255,0.9)",
        "plot_bgcolor": "rgba(240,248,255,0.8)",
        "font": {"family": "Rajdhani, sans-serif", "color": "#1A1A2E"},
        "title": {"font": {"family": "Orbitron, sans-serif", "size": 18, "color": "#0077B6"}},
        "xaxis": {
            "gridcolor": "rgba(0,180,216,0.2)",
            "linecolor": "#00B4D8",
            "tickfont": {"color": "#4A5568"}
        },
        "yaxis": {
            "gridcolor": "rgba(0,180,216,0.2)",
            "linecolor": "#00B4D8",
            "tickfont": {"color": "#4A5568"}
        }
    }
}

if len(df) > 0:
    # Temperature Chart
    fig = px.line(df, x="time", y="temp", title="🌡️ Temperature Trend",
                  markers=True, line_color="#00B4D8")
    fig.update_traces(marker=dict(size=8, color="#00F5D4", line=dict(color="#0077B6", width=2)))
    fig.update_layout(**futuristic_template["layout"])
    st.plotly_chart(fig, use_container_width=True)

    # Pressure Chart
    fig2 = px.line(df, x="time", y="qnh", title="🔵 Pressure (QNH) Trend",
                   markers=True, line_color="#0077B6")
    fig2.update_traces(marker=dict(size=8, color="#00B4D8", line=dict(color="#00F5D4", width=2)))
    fig2.update_layout(**futuristic_template["layout"])
    st.plotly_chart(fig2, use_container_width=True)

# =========================
# HISTORY TABLE
# =========================
st.markdown('<div class="section-header"><span class="section-icon">📜</span> METAR HISTORY</div>', unsafe_allow_html=True)

if len(df) > 0:
    st.dataframe(df, use_container_width=True)
else:
    st.info("Belum ada data history.")

# =========================
# DOWNLOAD BUTTON
# =========================
st.download_button(
    "📥 Download CSV",
    df.to_csv(index=False),
    file_name="metar_history.csv"
)

# =========================
# FOOTER
# =========================
st.markdown("""
---
<div style="text-align: center; padding: 20px; color: #4A5568; font-family: 'Rajdhani', sans-serif;">
    <p>🚀 <strong>METAR Real-Time Monitoring System</strong> | Generated by AI</p>
    <p>Data Source: NOAA | Airport: Juanda International (WARR)</p>
    <p style="font-size: 12px;">Auto-refresh every 60 seconds | Theme: Futuristic Bright</p>
</div>
""", unsafe_allow_html=True)



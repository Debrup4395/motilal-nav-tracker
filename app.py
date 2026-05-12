import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# =========================
# AUTO REFRESH EVERY 30 SEC
# =========================

st_autorefresh(interval=30000, key="refresh")

# =========================
# PAGE SETTINGS
# =========================

st.set_page_config(
    page_title="Motilal Oswal Midcap Fund NAV Tracker",
    layout="wide"
)

# =========================
# CUSTOM CSS
# =========================

st.markdown("""
<style>

.main {
    background-color: #050816;
    color: white;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

div[data-testid="metric-container"] {
    background: linear-gradient(135deg, #0f172a, #111827);
    border: 1px solid #1e293b;
    padding: 20px;
    border-radius: 20px;
    text-align: center;
    box-shadow: 0px 0px 20px rgba(0,0,0,0.35);
}

div[data-testid="metric-container"] label {
    color: #cbd5e1 !important;
    font-size: 15px !important;
}

.big-title {
    font-size: 42px;
    font-weight: bold;
    color: white;
}

.timestamp {
    color: #bbbbbb;
    font-size: 15px;
}

.screenshot-box {
    background: linear-gradient(135deg, #081028, #0b1220);
    padding: 25px;
    border-radius: 25px;
    border: 1px solid #1e3a5f;
    margin-bottom: 20px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# LOGO + TITLE
# =========================

col_logo, col_title = st.columns([1, 8])

with col_logo:
    st.image("logo.png", width=90)

with col_title:

    st.markdown(
        '<div class="big-title">🔥 Motilal Oswal Midcap Fund NAV Tracker</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="timestamp">Last Updated: {datetime.now().strftime("%d %b %Y | %I:%M:%S %p")}</div>',
        unsafe_allow_html=True
    )

# =========================
# AUTO NAV FETCH
# =========================

mf_api = "https://api.mfapi.in/mf/146139"

data = requests.get(mf_api).json()

previous_nav = float(data["data"][0]["nav"])

weekly_start_nav = float(data["data"][5]["nav"])

# =========================
# PORTFOLIO HOLDINGS
# =========================

stocks = [

    ("PAYTM", 7.29),
    ("KALYANKJIL", 7.09),
    ("ETERNAL", 5.83),
    ("COFORGE", 5.58),
    ("KEI", 5.48),
    ("PERSISTENT", 5.41),
    ("ABCAPITAL", 5.17),
    ("GROWW", 5.09),
    ("BHARTIARTL", 5.01),
    ("MCX", 4.33),
    ("BSE", 3.83),
    ("DIXON", 3.54),
    ("TIINDIA", 3.51),
    ("BHARTIHEXA", 3.18),
    ("SHRIRAMFIN", 3.03),
    ("PRESTIGE", 2.91),
    ("BEL", 2.63),
    ("LTF", 2.61),
    ("MAXHEALTH", 2.23),
    ("POLICYBZR", 2.20),
    ("TVSMOTOR", 2.08),
    ("ICICIPRULI", 1.96),
    ("IDFCFIRSTB", 1.47),
    ("PREMIERENE", 1.25),
    ("AXISBANK", 1.24),
    ("WAAREEENER", 1.04),
    ("AUBANK", 1.01)

]

# =========================
# FETCH LIVE DATA
# =========================

rows = []

total_weighted_return = 0

for symbol, weight in stocks:

    ticker = symbol + ".NS"

    try:

        stock = yf.Ticker(ticker)

        hist = stock.history(period="5d", interval="1d")

        prev_close = hist["Close"].iloc[-2]
        live_price = hist["Close"].iloc[-1]

        change_pct = (
            (live_price - prev_close)
            / prev_close
        ) * 100

        weighted_return = (
            change_pct * weight
        ) / 100

        total_weighted_return += weighted_return

        rows.append([

            symbol,
            round(weight, 2),
            round(prev_close, 2),
            round(live_price, 2),
            round(change_pct, 2)

        ])

    except:

        rows.append([

            symbol,
            weight,
            0,
            0,
            0

        ])

# =========================
# DATAFRAME
# =========================

df = pd.DataFrame(

    rows,

    columns=[

        "Stock",
        "Weight %",
        "Previous Close",
        "Live Price",
        "% Change"

    ]

)

# =========================
# NAV CALCULATIONS
# =========================

estimated_nav = previous_nav * (
    1 + total_weighted_return / 100
)

weekly_change = (
    (estimated_nav - weekly_start_nav)
    / weekly_start_nav
) * 100

weekly_nav_change = (
    estimated_nav - weekly_start_nav
)

# =========================
# TOP GAINER & LOSER
# =========================

top_gainer = df.loc[df["% Change"].idxmax()]
top_loser = df.loc[df["% Change"].idxmin()]

# =========================
# CONDITIONAL COLORS
# =========================

def color_change(val):

    if val > 0:
        return "color: lime"

    elif val < 0:
        return "color: red"

    return "color: white"

styled_df = df.style.format({

    "Weight %": "{:.2f}",
    "Previous Close": "{:.2f}",
    "Live Price": "{:.2f}",
    "% Change": "{:.2f}"

}).map(

    color_change,
    subset=["% Change"]

)

# =========================
# SCREENSHOT SECTION
# =========================

st.markdown('<div class="screenshot-box">', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Previous NAV",
    f"{previous_nav:.2f}"
)

col2.metric(
    "Expected NAV",
    f"{estimated_nav:.2f}",
    f"{total_weighted_return:.2f}%"
)

col3.metric(
    "📅 Weekly Change",
    f"{weekly_change:.2f}%",
    f"{weekly_nav_change:.2f} NAV"
)

col4.metric(
    "📈 Daily Change",
    f"{total_weighted_return:.2f}%"
)

st.markdown("---")

# =========================
# TOP GAINER & LOSER
# =========================

col5, col6 = st.columns(2)

col5.metric(
    "🚀 Top Gainer",
    f"{top_gainer['Stock']} ({top_gainer['Weight %']:.2f}%)",
    f"{top_gainer['% Change']:.2f}%"
)

col6.metric(
    "🔻 Top Loser",
    f"{top_loser['Stock']} ({top_loser['Weight %']:.2f}%)",
    f"{top_loser['% Change']:.2f}%"
)

st.markdown('</div>', unsafe_allow_html=True)

# =========================
# PORTFOLIO TABLE
# =========================

st.markdown("---")

st.subheader("📊 Portfolio Holdings")

st.dataframe(
    styled_df,
    use_container_width=True,
    height=850
)

st.markdown("---")

st.caption("Auto-refresh every 30 seconds")

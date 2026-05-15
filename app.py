import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Motilal Oswal Midcap Fund Tracker",
    layout="wide"
)

# =========================================================
# AUTO REFRESH
# =========================================================

st_autorefresh(interval=5000, key="refresh")

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}

.main {
    background: #050816;
    color: white;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
}

.big-title {
    font-size: 42px;
    font-weight: 700;
    color: white;
    letter-spacing: -1px;
}

.subtitle {
    color: #60a5fa;
    font-size: 18px;
    margin-top: -8px;
    font-weight: 600;
}

.timestamp {
    color: #94a3b8;
    font-size: 14px;
    margin-top: 5px;
}

div[data-testid="metric-container"] {
    background: linear-gradient(135deg, #111827, #1e293b);
    border: 1px solid #334155;
    padding: 22px;
    border-radius: 20px;
    box-shadow: 0 0 18px rgba(0,0,0,0.35);
}

div[data-testid="metric-container"] label {
    color: #cbd5e1 !important;
    font-size: 14px !important;
}

.screenshot-box {
    background: linear-gradient(135deg, #0f172a, #111827);
    border: 1px solid #334155;
    border-radius: 25px;
    padding: 25px;
    margin-bottom: 20px;
}

.gainer-box {
    background: rgba(34,197,94,0.12);
    border: 1px solid rgba(34,197,94,0.35);
    padding: 12px;
    border-radius: 14px;
    margin-bottom: 10px;
}

.loser-box {
    background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.35);
    padding: 12px;
    border-radius: 14px;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# INDIAN TIME
# =========================================================

india_time = datetime.now(
    ZoneInfo("Asia/Kolkata")
).strftime("%d %b %Y | %I:%M:%S %p")

# =========================================================
# HEADER
# =========================================================

col1, col2 = st.columns([1,8])

with col1:
    st.image("logo.png", width=90)

with col2:

    st.markdown(
        '<div class="big-title">🔥 Motilal Oswal Midcap Fund NAV Tracker</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Professional Live NAV Analytics Dashboard</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="timestamp">Last Updated : {india_time}</div>',
        unsafe_allow_html=True
    )

# =========================================================
# MANUAL NAV SETTINGS
# =========================================================

previous_nav = 104.84
weekly_start_nav = 108.67

# =========================================================
# INVESTMENT DETAILS
# =========================================================

avg_nav = 117.70
total_units = 36529.698

total_investment = total_units * avg_nav

investment_date = datetime(2024,9,2)

today_date = datetime.now()

total_days = (today_date - investment_date).days

years = total_days // 365
remaining_days = total_days % 365
months = remaining_days // 30
days = remaining_days % 30

investment_duration = f"{years}Y {months}M {days}D"

# =========================================================
# PORTFOLIO HOLDINGS
# =========================================================

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

# =========================================================
# FETCH LIVE STOCK DATA
# =========================================================

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
            weight,
            round(prev_close,2),
            round(live_price,2),
            round(change_pct,2)

        ])

    except:

        rows.append([
            symbol,
            weight,
            0,
            0,
            0
        ])

# =========================================================
# DATAFRAME
# =========================================================

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

# =========================================================
# NAV CALCULATION
# =========================================================

estimated_nav = previous_nav * (
    1 + total_weighted_return / 100
)

daily_nav_change = estimated_nav - previous_nav

weekly_change = (
    (estimated_nav - weekly_start_nav)
    / weekly_start_nav
) * 100

weekly_nav_change = estimated_nav - weekly_start_nav

# =========================================================
# P/L CALCULATIONS
# =========================================================

unrealised_pl_pct = (
    (estimated_nav - avg_nav)
    / avg_nav
) * 100

daily_return_amount = (
    total_investment
    * total_weighted_return
    / 100
)

weekly_return_amount = (
    total_investment
    * weekly_change
    / 100
)

unrealised_pl_amount = (
    total_investment
    * unrealised_pl_pct
    / 100
)

# =========================================================
# TOP GAINERS & LOSERS
# =========================================================

top_gainers = df.sort_values(
    by="% Change",
    ascending=False
).head(5)

top_losers = df.sort_values(
    by="% Change",
    ascending=True
).head(5)

# =========================================================
# TABLE COLORS
# =========================================================

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

# =========================================================
# METRICS SECTION
# =========================================================

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
    "Weekly Change",
    f"{weekly_change:.2f}%",
    f"{weekly_nav_change:.2f} NAV"
)

col4.metric(
    "Daily Change",
    f"{daily_nav_change:.2f}"
)

st.markdown("---")

col5, col6, col7 = st.columns(3)

col5.metric(
    "Daily Return",
    f"₹{daily_return_amount:,.0f}"
)

col6.metric(
    "Weekly Return",
    f"₹{weekly_return_amount:,.0f}"
)

col7.metric(
    "Unrealised P/L",
    f"₹{unrealised_pl_amount:,.0f}",
    f"{unrealised_pl_pct:.2f}%"
)

st.markdown("---")

col8, col9 = st.columns(2)

col8.metric(
    "Investment Duration",
    investment_duration
)

col9.metric(
    "Total Units",
    f"{total_units:,.3f}"
)

st.markdown("---")

# =========================================================
# GAINERS & LOSERS
# =========================================================

col10, col11 = st.columns(2)

with col10:

    st.subheader("🚀 Top 5 Gainers")

    for _, row in top_gainers.iterrows():

        st.markdown(f"""
        <div class="gainer-box">
        <b>{row['Stock']}</b><br>
        Weight : {row['Weight %']:.2f}%<br>
        Change : {row['% Change']:.2f}%
        </div>
        """, unsafe_allow_html=True)

with col11:

    st.subheader("🔻 Top 5 Losers")

    for _, row in top_losers.iterrows():

        st.markdown(f"""
        <div class="loser-box">
        <b>{row['Stock']}</b><br>
        Weight : {row['Weight %']:.2f}%<br>
        Change : {row['% Change']:.2f}%
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# PORTFOLIO TABLE
# =========================================================

st.markdown("---")

st.subheader("📊 Portfolio Holdings")

st.dataframe(
    styled_df,
    use_container_width=True,
    height=850
)

# =========================================================
# NAV HEATMAP CALENDAR
# =========================================================

st.markdown("---")
st.subheader("📅 Historical NAV Heatmap")

nav_data = {

    "2026-01-01":113.9116,
    "2026-01-02":114.6253,
    "2026-01-05":114.4763,
    "2026-01-06":113.9835,
    "2026-01-07":114.9269,
    "2026-01-08":113.7923,
    "2026-01-09":113.2379,
    "2026-01-12":112.7175,
    "2026-01-13":112.3857,
    "2026-01-14":112.087,
    "2026-05-14":104.8438

}

heatmap_df = pd.DataFrame(
    list(nav_data.items()),
    columns=["Date","NAV"]
)

heatmap_df["Date"] = pd.to_datetime(
    heatmap_df["Date"]
)

heatmap_df["Return %"] = (
    heatmap_df["NAV"].pct_change() * 100
)

heatmap_df["Weekday"] = (
    heatmap_df["Date"].dt.weekday
)

colors = []

for val in heatmap_df["Return %"]:

    if pd.isna(val):
        colors.append("gray")

    elif val > 1:
        colors.append("#00ff66")

    elif val > 0:
        colors.append("#66ff99")

    elif val < -1:
        colors.append("#ff1a1a")

    else:
        colors.append("#ff6666")

fig = go.Figure()

fig.add_trace(

    go.Scatter(

        x=heatmap_df["Date"],
        y=heatmap_df["Weekday"],

        mode="markers",

        marker=dict(
            size=24,
            color=colors,
            symbol="square"
        ),

        customdata=heatmap_df[
            ["NAV","Return %"]
        ],

        hovertemplate=
        "<b>%{x|%d %b %Y}</b><br>" +
        "NAV : %{customdata[0]:.2f}<br>" +
        "Return : %{customdata[1]:.2f}%<extra></extra>"

    )

)

fig.update_layout(

    height=300,

    paper_bgcolor="#050816",
    plot_bgcolor="#050816",

    font=dict(
        color="white"
    ),

    xaxis=dict(
        showgrid=False,
        tickformat="%b"
    ),

    yaxis=dict(

        showgrid=False,

        tickmode="array",

        tickvals=[0,1,2,3,4],

        ticktext=[
            "Mon",
            "Tue",
            "Wed",
            "Thu",
            "Fri"
        ]

    )

)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "© Motilal Oswal Midcap Fund Analytics Dashboard | Designed by Debrup Bera"
)

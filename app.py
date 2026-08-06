import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from zoneinfo import ZoneInfo
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.parse

# =========================
# AUTO REFRESH EVERY 15 SEC
# =========================

st_autorefresh(interval=15000, key="refresh")

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
    background: linear-gradient(135deg, #111827, #1f2937);
    border: 1px solid #374151;
    padding: 20px;
    border-radius: 18px;
    text-align: center;
    box-shadow: 0px 0px 15px rgba(0,0,0,0.35);
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
    background: linear-gradient(135deg, #0f172a, #111827);
    padding: 25px;
    border-radius: 25px;
    border: 1px solid #334155;
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

.impact-up-box {
    background: rgba(34,197,94,0.12);
    border: 1px solid rgba(34,197,94,0.35);
    padding: 12px;
    border-radius: 14px;
    margin-bottom: 10px;
}

.impact-down-box {
    background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.35);
    padding: 12px;
    border-radius: 14px;
    margin-bottom: 10px;
}

.message-box {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    padding: 20px;
    border-radius: 18px;
    border: 1px solid #475569;
    margin-top: 20px;
}

.stButton>button {
    border-radius: 12px;
    height: 50px;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# =========================
# INDIAN TIME
# =========================

india_time = datetime.now(
    ZoneInfo("Asia/Kolkata")
).strftime("%d %b %Y | %I:%M:%S %p")

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
        '<div style="font-size:18px; color:#60a5fa; font-weight:bold; margin-top:-8px;">© Debrup Bera</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="timestamp">Last Updated: {india_time}</div>',
        unsafe_allow_html=True
    )

# =========================
# MANUAL NAV UPDATE
# =========================

previous_nav = 117.74
weekly_start_nav = 117.602

# =========================
# INVESTMENT DETAILS
# =========================

avg_nav = 117.70

total_units = 35689.71

total_investment = (
    total_units * avg_nav
)

investment_date = datetime(
    2024,
    9,
    2
)

today_date = datetime.now()

total_days = (
    today_date - investment_date
).days

years = total_days // 365

remaining_days = total_days % 365

months = remaining_days // 30

days = remaining_days % 30

investment_duration = (
    f"{years}Y {months}M {days}D"
)

# =========================
# PORTFOLIO HOLDINGS
# =========================

stocks = [

    ("PAYTM", 7.34),
    ("KALYANKJIL", 6.34),
    ("COFORGE", 6.04),
    ("ETERNAL", 5.96),
    ("KEI", 5.61),
    ("ABCAPITAL", 5.49),
    ("PERSISTENT", 4.59),
    ("GROWW", 4.56),
    ("SHRIRAMFIN", 3.78),
    ("BSE", 3.61),
    ("MCX", 3.48),
    ("TIINDIA", 3.44),
    ("DIXON", 3.26),
    ("PRESTIGE", 3.10),
    ("BHARTIHEXA", 2.97),
    ("MAXHEALTH", 2.80),
    ("LTF", 2.77),
    ("SUZLON", 2.47),
    ("POLICYBZR", 2.35),
    ("ICICIAMC", 2.25),
    ("IDFCFIRSTB", 2.25),
    ("BEL", 2.21),
    ("MOTHERSON", 2.20),
    ("PREMIERENE", 2.19),
    ("WAAREEENER", 1.91),
    ("INDIGO", 1.68),
    ("AUBANK", 0.99),
    ("STLTECH", 0.91),
    ("PWL", 0.57),

]

# =========================
# FETCH LIVE DATA
# =========================
#
# NOTE ON THE "None" BUG (earlier fix):
# The original code called yf.Ticker(...).history() separately for each
# of the 29 symbols, one after another. Yahoo Finance occasionally
# rate-limits or hiccups on an individual request in that loop, so a
# random symbol (e.g. COFORGE) would intermittently return empty data
# and render as None/blank in the table.
#
# NOTE ON THE "WRONG PRICE / WRONG %" BUG (previous fix):
# An earlier version pulled "Previous Close" from a batched daily-bar
# download (yf.download) and "Live Price" from a separate fast_info call,
# which could desync (previous close shifted back an extra day).
#
# NOTE ON THE "PRICE STILL WRONG AFTER THE 1m-BAR FIX" BUG (THIS fix):
# Switching Live Price from fast_info to a 1-minute intraday candle
# helped for some symbols, but for others (e.g. KALYANKJIL showing
# 571.40 vs the broker's 598.00, a ~4.7% gap, WHILE Previous Close
# matched exactly at 569.50) the gap remained. That combination --
# correct previous close, wrong live price -- means the problem isn't
# how the code reads Yahoo's data anymore, it's that Yahoo's own feed
# for a chunk of NSE mid/small-caps is genuinely stale at the source.
# No amount of restructuring the yfinance call can fix data Yahoo
# itself hasn't refreshed yet.
#
# REAL FIX: pull the LIVE PRICE directly from NSE India's own quote API
# (nseindia.com) -- the exchange's own feed, which is the same
# ultimate source your broker app's numbers come from. This is far
# more current than Yahoo for NSE names. yfinance (1-minute bar, then
# fast_info, then daily-bar batch) is kept as a fallback chain only for
# when NSE's site is unreachable or rate-limits a request.
#
# IMPORTANT CAVEATS (read before assuming this is 100% fixed):
# 1) NSE's website uses bot-detection (cookies + browser-like headers
#    are required, done below via a persistent requests.Session). If
#    NSE tightens that detection, or blocks the IP range Streamlit
#    Cloud runs on, these calls can start failing -- in which case the
#    code will silently drop back to the yfinance chain, and you'll
#    see Yahoo-level accuracy again, not an error.
# 2) NSE's own site quote still isn't literally the same millisecond
#    tick your broker terminal shows (broker apps often have a direct
#    licensed exchange feed), but it is materially closer than Yahoo.
# 3) I could not execute/test this against the live NSE API from this
#    environment (network access here is restricted to package
#    registries only) -- please deploy and check it actually returns
#    data for your account/region before relying on it.

if "last_good_data" not in st.session_state:
    st.session_state["last_good_data"] = {}

if "last_good_time" not in st.session_state:
    st.session_state["last_good_time"] = {}

if "nse_session" not in st.session_state:
    st.session_state["nse_session"] = None

tickers_list = [symbol + ".NS" for symbol, _ in stocks]

NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/get-quotes/equity",
}


def get_nse_session():
    """Reuse one requests.Session across reruns so we don't re-negotiate
    NSE's anti-bot cookies on every 15-second autorefresh. NSE's API
    rejects requests that don't carry cookies obtained from first
    loading the site like a real browser does."""
    session = st.session_state.get("nse_session")
    if session is None:
        session = requests.Session()
        session.headers.update(NSE_HEADERS)
        try:
            session.get("https://www.nseindia.com", timeout=5)
        except Exception:
            pass
        st.session_state["nse_session"] = session
    return session


@st.cache_data(ttl=5, show_spinner=False)
def get_nse_quote(symbol):
    """PRIMARY live-quote source: NSE India's own quote-equity API.
    This is the exchange's own feed rather than a third-party mirror,
    so it doesn't carry Yahoo's staleness for lower-liquidity names."""
    session = get_nse_session()
    url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
    try:
        resp = session.get(url, timeout=5)
        if resp.status_code != 200:
            # Cookies likely expired -- refresh once and retry.
            session.get("https://www.nseindia.com", timeout=5)
            resp = session.get(url, timeout=5)
        data = resp.json()
        price_info = data.get("priceInfo", {})
        live_price = price_info.get("lastPrice")
        prev_close = price_info.get("previousClose")
        if live_price and prev_close:
            return float(prev_close), float(live_price)
    except Exception:
        pass
    return None, None


@st.cache_data(ttl=10, show_spinner=False)
def fetch_batch_data(tickers):
    """Fallback-only daily bar data, used solely when everything else fails."""
    return yf.download(
        tickers=tickers,
        period="10d",
        interval="1d",
        group_by="ticker",
        threads=True,
        progress=False,
        auto_adjust=False,
    )


@st.cache_data(ttl=10, show_spinner=False)
def get_quote(ticker):
    """
    FALLBACK live-quote source (used only if NSE's API failed for this
    symbol this refresh cycle). Same logic as before:

    Live price: most recent 1-minute intraday candle close.
    Previous close: last COMPLETE daily bar from a fresh daily-history
    pull (not a cached quote field), so it can't desync from live price.
    fast_info is used only as a last-resort fallback for either value.
    """
    live_price = None
    prev_close = None

    try:
        t = yf.Ticker(ticker)

        # --- LIVE PRICE: latest 1-minute intraday bar ---
        intraday = t.history(period="1d", interval="1m")
        if not intraday.empty:
            closes = intraday["Close"].dropna()
            if len(closes) >= 1:
                live_price = float(closes.iloc[-1])

        # --- PREVIOUS CLOSE: last complete daily bar ---
        daily = t.history(period="5d", interval="1d")
        if not daily.empty:
            daily_closes = daily["Close"].dropna()
            if len(daily_closes) >= 2:
                prev_close = float(daily_closes.iloc[-2])
            elif len(daily_closes) == 1:
                # Only today's bar exists so far (e.g. pre-market) --
                # let the fast_info fallback below try to fill this in.
                prev_close = None

        # --- FALLBACK: fast_info, only for whichever value is still missing ---
        if live_price is None or prev_close is None:
            fi = t.fast_info
            if live_price is None:
                live_price = fi.get("last_price") or fi.get("lastPrice")
            if prev_close is None:
                prev_close = (
                    fi.get("previous_close")
                    or fi.get("previousClose")
                    or fi.get("regular_market_previous_close")
                )

        if live_price and prev_close:
            return float(prev_close), float(live_price)

    except Exception:
        pass

    return None, None


def get_prev_close_fallback(ticker, batch_data):
    """Last-resort fallback if everything above failed. Uses the last
    COMPLETE daily bar from the batched download."""
    try:
        if isinstance(batch_data.columns, pd.MultiIndex):
            hist = batch_data[ticker]["Close"].dropna()
        else:
            hist = batch_data["Close"].dropna()

        if len(hist) >= 2:
            return hist.iloc[-2]
        elif len(hist) == 1:
            return hist.iloc[-1]
    except Exception:
        pass
    return None


def get_live_price_fallback(ticker, batch_data):
    """Last-resort fallback live price if everything above failed."""
    try:
        if isinstance(batch_data.columns, pd.MultiIndex):
            hist = batch_data[ticker]["Close"].dropna()
        else:
            hist = batch_data["Close"].dropna()
        if len(hist) >= 1:
            return hist.iloc[-1]
    except Exception:
        pass
    return None


rows = []

total_weighted_return = 0

# Only pull the fallback daily-bar batch if we actually end up needing it
batch_data = None

for symbol, weight in stocks:

    ticker = symbol + ".NS"

    # PRIMARY: NSE India's own quote API -- see get_nse_quote() docstring
    prev_close, live_price = get_nse_quote(symbol)

    # FALLBACK 1: yfinance 1m intraday bar / fast_info -- only if NSE
    # gave us nothing at all for this symbol this cycle
    if prev_close is None or live_price is None:
        prev_close, live_price = get_quote(ticker)

    # FALLBACK 2: batched daily-bar download -- only if BOTH of the
    # above failed entirely for this symbol
    if prev_close is None or live_price is None:
        if batch_data is None:
            try:
                batch_data = fetch_batch_data(tickers_list)
            except Exception:
                batch_data = pd.DataFrame()

        if prev_close is None:
            prev_close = get_prev_close_fallback(ticker, batch_data)
        if live_price is None:
            live_price = get_live_price_fallback(ticker, batch_data)

    if prev_close is not None and live_price is not None:
        # Good data this refresh -> compute and remember it
        change_pct = (
            (live_price - prev_close)
            / prev_close
        ) * 100

        weighted_return = (
            change_pct * weight
        ) / 100

        nav_impact = (
            previous_nav * weighted_return
        ) / 100

        row = [
            symbol,
            round(weight, 2),
            round(prev_close, 2),
            round(live_price, 2),
            round(change_pct, 2),
            round(nav_impact, 4),
        ]

        st.session_state["last_good_data"][symbol] = row
        total_weighted_return += weighted_return

    else:
        # No fresh data at all this refresh -> reuse last known good
        # values instead of showing None, so the row stays populated
        cached_row = st.session_state["last_good_data"].get(symbol)

        if cached_row is not None:
            row = cached_row
            # still add its cached contribution so NAV math stays consistent
            cached_change_pct = row[4]
            weighted_return = (cached_change_pct * weight) / 100
            total_weighted_return += weighted_return
        else:
            # First-ever load and even the retry failed -> show 0s,
            # not None, so formatting never breaks
            row = [symbol, weight, 0, 0, 0, 0]

    rows.append(row)

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
        "% Change",
        "NAV Impact"

    ]

)

# =========================
# NAV CALCULATIONS
# =========================

estimated_nav = previous_nav * (
    1 + total_weighted_return / 100
)

daily_nav_change = (
    estimated_nav - previous_nav
)

weekly_change = (
    (estimated_nav - weekly_start_nav)
    / weekly_start_nav
) * 100

weekly_nav_change = (
    estimated_nav - weekly_start_nav
)

# =========================
# UNREALISED PROFIT / LOSS
# =========================

unrealised_pl_pct = (
    (estimated_nav - avg_nav)
    / avg_nav
) * 100

# =========================
# AMOUNT CALCULATIONS
# =========================

daily_return_amount = daily_nav_change * total_units

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

# =========================
# TOP 5 GAINERS & LOSERS
# =========================

top_gainers = df.sort_values(
    by="% Change",
    ascending=False
).head(5)

top_losers = df.sort_values(
    by="% Change",
    ascending=True
).head(5)

# =========================
# TOP 5 NAV MOVERS (BY IMPACT)
# =========================

top_nav_boosters = df.sort_values(
    by="NAV Impact",
    ascending=False
).head(5)

top_nav_draggers = df.sort_values(
    by="NAV Impact",
    ascending=True
).head(5)

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
    "% Change": "{:.2f}",
    "NAV Impact": "{:+.4f}"

}).map(

    color_change,
    subset=["% Change", "NAV Impact"]

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

col5, col6, col7 = st.columns(3)

col5.metric(
    "💰 Daily Return",
    f"₹{daily_return_amount:,.0f}"
)

col6.metric(
    "💵 Weekly Return",
    f"₹{weekly_return_amount:,.0f}"
)

col7.metric(
    "💼 Unrealised P/L",
    f"₹{unrealised_pl_amount:,.0f}",
    f"{unrealised_pl_pct:.2f}%"
)

st.markdown("---")

col8, col9 = st.columns(2)

col8.metric(
    "⏳ Investment Time",
    investment_duration
)

col9.metric(
    "🧾 Total Units",
    f"{total_units:,.3f}"
)

st.markdown("---")

# =========================
# TOP 5 GAINERS
# =========================

col10, col11 = st.columns(2)

with col10:

    st.subheader("🚀 Top 5 Gainers")

    for _, row in top_gainers.iterrows():

        st.markdown(f"""
        <div class="gainer-box">
        <b>{row['Stock']}</b> ({row['Weight %']:.2f}%)
        <br>
        {row['% Change']:.2f}%
        </div>
        """, unsafe_allow_html=True)

# =========================
# TOP 5 LOSERS
# =========================

with col11:

    st.subheader("🔻 Top 5 Losers")

    for _, row in top_losers.iterrows():

        st.markdown(f"""
        <div class="loser-box">
        <b>{row['Stock']}</b> ({row['Weight %']:.2f}%)
        <br>
        {row['% Change']:.2f}%
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# =========================
# TOP 5 NAV BOOSTERS / DRAGGERS
# (which stocks are moving the LIVE NAV the most,
#  in actual NAV rupees, not just % change)
# =========================

col12, col13 = st.columns(2)

with col12:

    st.subheader("🟢 Top 5 NAV Boosters")

    for _, row in top_nav_boosters.iterrows():

        st.markdown(f"""
        <div class="impact-up-box">
        <b>{row['Stock']}</b> ({row['Weight %']:.2f}% weight)
        <br>
        {row['% Change']:.2f}% move &nbsp;→&nbsp; <b>+{row['NAV Impact']:.4f}</b> NAV pts
        </div>
        """, unsafe_allow_html=True)

with col13:

    st.subheader("🔴 Top 5 NAV Draggers")

    for _, row in top_nav_draggers.iterrows():

        st.markdown(f"""
        <div class="impact-down-box">
        <b>{row['Stock']}</b> ({row['Weight %']:.2f}% weight)
        <br>
        {row['% Change']:.2f}% move &nbsp;→&nbsp; <b>{row['NAV Impact']:.4f}</b> NAV pts
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# =========================
# EMAIL & WHATSAPP SECTION
# =========================

st.markdown('<div class="message-box">', unsafe_allow_html=True)

st.subheader("📧 Share Today's Expected Returns")

# Prepare the message content
message_content = f"""
🔥 Motilal Oswal Midcap Fund - Daily Update

📅 Date: {india_time}

📊 NAV Details:
• Previous NAV: ₹{previous_nav:.2f}
• Expected NAV: ₹{estimated_nav:.2f}
• Daily Change: {total_weighted_return:.2f}%

💰 Returns:
• Daily Return: ₹{daily_return_amount:,.0f}
• Weekly Return: ₹{weekly_return_amount:,.0f}
• Unrealised P/L: ₹{unrealised_pl_amount:,.0f} ({unrealised_pl_pct:.2f}%)

📈 Portfolio Performance:
• Weekly Change: {weekly_change:.2f}%
• Investment Duration: {investment_duration}

🚀 Top 5 Gainers:
"""

for idx, (_, row) in enumerate(top_gainers.head(5).iterrows(), 1):
    message_content += f"{idx}. {row['Stock']} - {row['% Change']:.2f}%\n"

message_content += "\n🔻 Top 5 Losers:\n"

for idx, (_, row) in enumerate(top_losers.head(5).iterrows(), 1):
    message_content += f"{idx}. {row['Stock']} - {row['% Change']:.2f}%\n"

message_content += "\n🟢 Top 5 NAV Boosters (actual NAV pts):\n"

for idx, (_, row) in enumerate(top_nav_boosters.head(5).iterrows(), 1):
    message_content += f"{idx}. {row['Stock']} - +{row['NAV Impact']:.4f} NAV pts\n"

message_content += "\n🔴 Top 5 NAV Draggers (actual NAV pts):\n"

for idx, (_, row) in enumerate(top_nav_draggers.head(5).iterrows(), 1):
    message_content += f"{idx}. {row['Stock']} - {row['NAV Impact']:.4f} NAV pts\n"

message_content += "\n© Debrup Bera | Motilal Oswal Midcap Fund Tracker"

# Display the message preview
with st.expander("📝 Preview Message", expanded=False):
    st.text_area("Message Content", message_content, height=300, disabled=True)

# Create columns for input fields
col_email, col_phone = st.columns(2)

with col_email:
    st.markdown("#### 📧 Send via Email")
    recipient_email = st.text_input("Recipient Email", placeholder="example@gmail.com")
    
    # Email configuration (You need to set these in Streamlit secrets or environment variables)
    sender_email = st.text_input("Your Email (Gmail)", placeholder="your-email@gmail.com")
    sender_password = st.text_input("App Password", type="password", 
                                   help="Use Gmail App Password, not your regular password")

with col_phone:
    st.markdown("#### 📱 Send via WhatsApp")
    phone_number = st.text_input("Phone Number (with country code)", 
                                 placeholder="+911234567890",
                                 help="Format: +91XXXXXXXXXX (India)")

# Create buttons
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

with col_btn1:
    send_email_btn = st.button("📧 Send Email", use_container_width=True)

with col_btn2:
    send_whatsapp_btn = st.button("📱 Send WhatsApp", use_container_width=True)

# =========================
# EMAIL SENDING FUNCTION
# =========================

def send_email(sender, password, recipient, subject, body):
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(sender, recipient, text)
        server.quit()
        
        return True, "Email sent successfully! ✅"
    
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

# =========================
# WHATSAPP LINK GENERATION
# =========================

def generate_whatsapp_link(phone, message):
    # Remove '+' and any spaces from phone number
    clean_phone = phone.replace('+', '').replace(' ', '').replace('-', '')
    
    # URL encode the message
    encoded_message = urllib.parse.quote(message)
    
    # Generate WhatsApp link
    whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_message}"
    
    return whatsapp_url

# =========================
# HANDLE BUTTON CLICKS
# =========================

if send_email_btn:
    if not recipient_email or not sender_email or not sender_password:
        st.error("⚠️ Please fill in all email fields!")
    else:
        with st.spinner("Sending email..."):
            subject = f"Motilal Oswal Midcap Fund Update - {datetime.now().strftime('%d %b %Y')}"
            success, message = send_email(sender_email, sender_password, recipient_email, 
                                         subject, message_content)
            
            if success:
                st.success(message)
            else:
                st.error(message)
                st.info("💡 Tip: For Gmail, you need to use an 'App Password', not your regular password. "
                       "Generate one at: https://myaccount.google.com/apppasswords")

if send_whatsapp_btn:
    if not phone_number:
        st.error("⚠️ Please enter a phone number!")
    else:
        whatsapp_url = generate_whatsapp_link(phone_number, message_content)
        st.success("✅ WhatsApp link generated!")
        st.markdown(f"[📱 Click here to open WhatsApp]({whatsapp_url})")
        st.info("💡 Clicking the link will open WhatsApp with the pre-filled message. "
               "You can review and send it from there.")

st.markdown('</div>', unsafe_allow_html=True)

# =========================
# PORTFOLIO TABLE
# =========================

st.markdown("---")

st.subheader("📊 Portfolio Holdings (with live NAV impact)")

st.dataframe(
    styled_df,
    use_container_width=True,
    height=850
)

st.markdown("---")

st.caption("© Debrup Bera | Auto-refresh every 15 seconds")

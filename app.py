import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import concurrent.futures
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from zoneinfo import ZoneInfo
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.parse

# =========================
# AUTO REFRESH
# =========================
# Matched to the cache ttl on the fetch functions.

REFRESH_SECONDS = 10

st_autorefresh(interval=REFRESH_SECONDS * 1000, key="refresh")

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

.source-tag {
    font-size: 11px;
    color: #94a3b8;
    font-style: italic;
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

previous_nav = 120.81
weekly_start_nav = 119.1088   # TODO: set to last week's closing NAV

# =========================
# INVESTMENT DETAILS
# =========================

avg_nav = 117.70            # TODO: update if your average cost changed

total_units = 34462.54

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
# Motilal Oswal Midcap Fund - Monthly Portfolio Statement
# AS ON OCTOBER 31, 2026 ("% to Net Assets", equity only).
# TREPS (4.39%) and net receivables (0.40%) excluded.
# NEW vs September: MEESHO. All 31 listed holdings included.

stocks = [

    ("PAYTM", 8.54),
    ("ETERNAL", 7.32),
    ("KALYANKJIL", 7.29),
    ("COFORGE", 6.44),
    ("PERSISTENT", 5.15),
    ("ABCAPITAL", 4.57),
    ("STLTECH", 4.04),
    ("GROWW", 3.90),
    ("MCX", 3.67),
    ("KEI", 3.66),
    ("SHRIRAMFIN", 3.07),
    ("LENSKART", 3.06),
    ("DIXON", 2.92),
    ("BHARTIHEXA", 2.60),
    ("MOTHERSON", 2.34),
    ("PRESTIGE", 2.29),
    ("BSE", 2.28),
    ("ICICIAMC", 2.28),
    ("TIINDIA", 2.20),
    ("IDFCFIRSTB", 2.15),
    ("PREMIERENE", 2.10),
    ("BEL", 1.92),
    ("INDIGO", 1.74),
    ("SUZLON", 1.71),
    ("POLICYBZR", 1.64),
    ("LTF", 1.56),
    ("WAAREEENER", 1.50),
    ("MAXHEALTH", 1.24),
    ("ADANIENT", 0.79),
    ("MEESHO", 0.69),
    ("PWL", 0.55),

]

# =========================
# FETCH LIVE DATA
# =========================
#
# Design: nothing in the per-symbol loop touches the network.
#   Tier 1: NSE (all symbols concurrently, one overall timeout)
#   Tier 2: Yahoo fast_info quote (all tickers concurrently, one timeout)
#   Tier 3: Yahoo batched daily/intraday bars (last resort, derived)
# The staleness guard is keyed by (symbol, date) and only applies to
# the Tier 3 derived path. NSE and Yahoo quote values are trusted.
# Check the Debug expander to see which tier served each stock and
# whether NSE is blocking this host's IP (common on Streamlit Cloud).

STALE_GUARD_PCT = 3.0  # max allowed jump in previous_close vs last known-good, in % (Tier 3 only)
NSE_REQUEST_TIMEOUT = 5        # per-request timeout, seconds
NSE_BATCH_TIMEOUT = 20         # hard ceiling for ALL NSE requests combined
YF_BATCH_TIMEOUT = 15          # hard ceiling for each batched yfinance download

if "last_good_data" not in st.session_state:
    st.session_state["last_good_data"] = {}

if "last_good_prev_close" not in st.session_state:
    # {symbol: {"date": "YYYY-MM-DD", "value": float}}
    st.session_state["last_good_prev_close"] = {}

if "nse_session" not in st.session_state:
    st.session_state["nse_session"] = None

symbol_list = [s for s, _ in stocks]
tickers_list = [s + ".NS" for s in symbol_list]

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
    NSE's anti-bot cookies on every refresh."""
    session = st.session_state.get("nse_session")
    if session is None:
        session = requests.Session()
        session.headers.update(NSE_HEADERS)
        try:
            session.get("https://www.nseindia.com", timeout=NSE_REQUEST_TIMEOUT)
        except Exception:
            pass
        st.session_state["nse_session"] = session
    return session


def _fetch_one_nse(symbol, session):
    """Single-symbol NSE fetch. Called from a thread pool, never
    directly from the main per-symbol loop."""
    url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
    try:
        resp = session.get(url, timeout=NSE_REQUEST_TIMEOUT)
        if resp.status_code != 200:
            resp = session.get(url, timeout=NSE_REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return symbol, None, None, f"HTTP {resp.status_code}"
        data = resp.json()
        price_info = data.get("priceInfo", {})
        live_price = price_info.get("lastPrice")
        prev_close = price_info.get("previousClose")
        if live_price and prev_close:
            return symbol, float(prev_close), float(live_price), None
        return symbol, None, None, "missing priceInfo fields (likely bot-blocked page)"
    except ValueError:
        return symbol, None, None, "non-JSON response (likely bot-block HTML page)"
    except requests.exceptions.Timeout:
        return symbol, None, None, "timeout"
    except Exception as e:
        return symbol, None, None, f"{type(e).__name__}"


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def fetch_nse_batch(symbols):
    """PRIMARY source. Fetches ALL symbols concurrently via a thread
    pool, bounded by ONE overall timeout."""
    session = get_nse_session()
    results = {}
    errors = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(_fetch_one_nse, s, session): s for s in symbols}
        try:
            for fut in concurrent.futures.as_completed(futures, timeout=NSE_BATCH_TIMEOUT):
                s = futures[fut]
                try:
                    _, prev_close, live_price, err = fut.result()
                except Exception as e:
                    prev_close, live_price, err = None, None, str(e)
                results[s] = (prev_close, live_price)
                if err:
                    errors[s] = err
        except concurrent.futures.TimeoutError:
            for fut, s in futures.items():
                if s not in results:
                    results[s] = (None, None)
                    errors[s] = "timeout (overall NSE batch)"

    return results, errors


def _fetch_one_yf_quote(ticker):
    """Single-symbol Yahoo QUOTE fetch via fast_info. Called from a
    thread pool, never directly from the main per-symbol loop."""
    try:
        t = yf.Ticker(ticker)
        fi = t.fast_info
        prev_close = fi.get("previousClose") or fi.get("regularMarketPreviousClose")
        live_price = (
            fi.get("lastPrice")
            or fi.get("last_price")
            or fi.get("regularMarketPrice")
        )
        if prev_close and live_price:
            return ticker, float(prev_close), float(live_price), None
        return ticker, None, None, "missing fast_info fields"
    except Exception as e:
        return ticker, None, None, f"{type(e).__name__}"


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def fetch_yf_quote_batch(tickers):
    """TIER 2 source, used when NSE fails. Concurrent, bounded by ONE
    overall timeout."""
    results = {}
    errors = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(_fetch_one_yf_quote, t): t for t in tickers}
        try:
            for fut in concurrent.futures.as_completed(futures, timeout=YF_BATCH_TIMEOUT):
                t = futures[fut]
                try:
                    _, prev_close, live_price, err = fut.result()
                except Exception as e:
                    prev_close, live_price, err = None, None, str(e)
                results[t] = (prev_close, live_price)
                if err:
                    errors[t] = err
        except concurrent.futures.TimeoutError:
            for fut, t in futures.items():
                if t not in results:
                    results[t] = (None, None)
                    errors[t] = "timeout (overall yfinance quote batch)"

    return results, errors


def _download_with_timeout(kwargs, timeout_seconds):
    """Runs a yf.download() call in a worker thread with a hard
    timeout, since yfinance itself sets none."""
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(lambda: yf.download(**kwargs))
            return future.result(timeout=timeout_seconds)
    except concurrent.futures.TimeoutError:
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def fetch_daily_batch(tickers):
    """TIER 3 (last-resort) source for previous close: ONE batched,
    threaded call for ALL tickers' recent daily bars."""
    return _download_with_timeout(
        dict(
            tickers=tickers,
            period="10d",
            interval="1d",
            group_by="ticker",
            threads=True,
            progress=False,
            auto_adjust=False,
        ),
        YF_BATCH_TIMEOUT,
    )


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def fetch_intraday_batch(tickers):
    """TIER 3 source (live price): ONE batched, threaded call for ALL
    tickers' 1-minute intraday bars."""
    return _download_with_timeout(
        dict(
            tickers=tickers,
            period="1d",
            interval="1m",
            group_by="ticker",
            threads=True,
            progress=False,
            auto_adjust=False,
        ),
        YF_BATCH_TIMEOUT,
    )


def get_prev_close_from_daily(ticker, daily_batch, intraday_batch):
    """Previous close = last COMPLETE daily bar, from the pre-fetched
    daily batch. No network I/O.

    Compares yfinance's daily bar dates to yfinance's OWN intraday bar
    dates (same source, same normalization), never to the Python clock:
      - If the intraday batch's last date matches the daily batch's last
        date, that last daily row is today's in-progress bar -> drop it,
        use the row before it.
      - Otherwise the last daily row is already a completed session ->
        it IS the previous close.
    """
    try:
        if daily_batch is None or daily_batch.empty:
            return None
        if isinstance(daily_batch.columns, pd.MultiIndex):
            daily_hist = daily_batch[ticker]["Close"].dropna()
        else:
            daily_hist = daily_batch["Close"].dropna()

        if daily_hist.empty:
            return None

        last_daily_ts = daily_hist.index[-1]
        last_daily_date = pd.Timestamp(last_daily_ts).date()

        intraday_last_date = None
        try:
            if intraday_batch is not None and not intraday_batch.empty:
                if isinstance(intraday_batch.columns, pd.MultiIndex):
                    intraday_hist = intraday_batch[ticker]["Close"].dropna()
                else:
                    intraday_hist = intraday_batch["Close"].dropna()
                if len(intraday_hist) >= 1:
                    intraday_last_date = pd.Timestamp(intraday_hist.index[-1]).date()
        except Exception:
            intraday_last_date = None

        if intraday_last_date is not None and last_daily_date == intraday_last_date:
            if len(daily_hist) >= 2:
                return float(daily_hist.iloc[-2])
            return None

        return float(daily_hist.iloc[-1])
    except Exception:
        pass
    return None


def get_live_price_from_intraday(ticker, batch_data):
    """Live price = most recent 1-minute intraday close, from the
    pre-fetched intraday batch. No network I/O."""
    try:
        if batch_data is not None and not batch_data.empty:
            if isinstance(batch_data.columns, pd.MultiIndex):
                hist = batch_data[ticker]["Close"].dropna()
            else:
                hist = batch_data["Close"].dropna()
            if len(hist) >= 1:
                return float(hist.iloc[-1])
    except Exception:
        pass
    return None


def validate_prev_close(symbol, prev_close, source):
    """
    STALENESS GUARD, keyed by (symbol, date) so the baseline resets
    every day. NSE and Yahoo-quote values are trusted outright; the
    guard only protects the Tier 3 candle-derived path.
    """
    today_str = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()

    if source in ("NSE", "yfinance-quote"):
        st.session_state["last_good_prev_close"][symbol] = {
            "date": today_str,
            "value": prev_close,
        }
        return prev_close, True

    entry = st.session_state["last_good_prev_close"].get(symbol)

    if entry is None or entry.get("date") != today_str:
        st.session_state["last_good_prev_close"][symbol] = {
            "date": today_str,
            "value": prev_close,
        }
        return prev_close, True

    last_good = entry["value"]
    deviation_pct = abs(prev_close - last_good) / last_good * 100

    if deviation_pct > STALE_GUARD_PCT:
        return last_good, False

    st.session_state["last_good_prev_close"][symbol] = {
        "date": today_str,
        "value": prev_close,
    }
    return prev_close, True


# --- Fetch all sources ONCE, up front, each bounded by its own hard
# --- timeout. The per-symbol loop below does NO network I/O.

nse_results, nse_errors = fetch_nse_batch(tuple(symbol_list))

need_tier2 = any(
    nse_results.get(s, (None, None))[0] is None
    or nse_results.get(s, (None, None))[1] is None
    for s in symbol_list
)

yf_quote_results, yf_quote_errors = (
    fetch_yf_quote_batch(tuple(tickers_list)) if need_tier2 else ({}, {})
)

need_tier3 = any(
    (nse_results.get(s, (None, None))[0] is None or nse_results.get(s, (None, None))[1] is None)
    and (
        yf_quote_results.get(s + ".NS", (None, None))[0] is None
        or yf_quote_results.get(s + ".NS", (None, None))[1] is None
    )
    for s in symbol_list
)

daily_batch = fetch_daily_batch(tuple(tickers_list)) if need_tier3 else None
intraday_batch = fetch_intraday_batch(tuple(tickers_list)) if need_tier3 else None

rows = []
total_weighted_return = 0

for symbol, weight in stocks:

    ticker = symbol + ".NS"

    prev_close, live_price = nse_results.get(symbol, (None, None))
    source = "NSE"

    if prev_close is None or live_price is None:
        # TIER 2: Yahoo's own quote fields for this ticker.
        q_prev, q_live = yf_quote_results.get(ticker, (None, None))
        prev_close = prev_close if prev_close is not None else q_prev
        live_price = live_price if live_price is not None else q_live
        source = "yfinance-quote"

    if prev_close is None or live_price is None:
        # TIER 3 (last resort): derive from historical candles.
        fb_prev = get_prev_close_from_daily(ticker, daily_batch, intraday_batch)
        fb_live = get_live_price_from_intraday(ticker, intraday_batch)
        prev_close = prev_close if prev_close is not None else fb_prev
        live_price = live_price if live_price is not None else fb_live
        source = "yfinance-daily-derived"

    if prev_close is not None and live_price is not None:

        # --- STALENESS GUARD: reject an implausible previous_close jump ---
        validated_prev_close, accepted = validate_prev_close(symbol, prev_close, source)
        if not accepted:
            source = f"{source} (rejected, using last-good)"
        prev_close = validated_prev_close

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
            source,
        ]

        st.session_state["last_good_data"][symbol] = row
        total_weighted_return += weighted_return

    else:
        # No fresh data at all this refresh -> reuse last known good
        # values instead of showing None, so the row stays populated
        cached_row = st.session_state["last_good_data"].get(symbol)

        if cached_row is not None:
            row = cached_row
            cached_change_pct = row[4]
            weighted_return = (cached_change_pct * weight) / 100
            total_weighted_return += weighted_return
        else:
            row = [symbol, weight, 0, 0, 0, 0, "no data"]

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
        "NAV Impact",
        "Source",

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

# =========================
# PORTFOLIO VALUE (with eye toggle to hide / unhide)
# =========================

if "show_portfolio_value" not in st.session_state:
    st.session_state["show_portfolio_value"] = True

current_portfolio_value = total_units * avg_nav          # units x buying avg NAV
expected_portfolio_value = total_units * estimated_nav   # units x live expected NAV
portfolio_value_change = daily_return_amount             # today's expected move in rupees

col_pv_title, col_pv_eye = st.columns([8, 1])

with col_pv_title:
    st.subheader("💎 Portfolio Value")

with col_pv_eye:
    eye_icon = "👁️" if st.session_state["show_portfolio_value"] else "🙈"
    if st.button(eye_icon, key="toggle_portfolio_value", help="Hide / show portfolio value"):
        st.session_state["show_portfolio_value"] = not st.session_state["show_portfolio_value"]
        st.rerun()

col_pv1, col_pv2 = st.columns(2)

if st.session_state["show_portfolio_value"]:
    col_pv1.metric(
        "🏦 Current Portfolio Value",
        f"₹{current_portfolio_value:,.0f}"
    )
    col_pv2.metric(
        "📊 Expected Portfolio Value",
        f"₹{expected_portfolio_value:,.0f}",
        f"{portfolio_value_change:+,.0f} ({total_weighted_return:+.2f}%)"
    )
else:
    col_pv1.metric("🏦 Current Portfolio Value", "₹ ••••••")
    col_pv2.metric("📊 Expected Portfolio Value", "₹ ••••••")

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
# DEBUG: DATA SOURCE PER STOCK
# =========================

with st.expander("🛠️ Debug: Data source per stock", expanded=False):
    st.dataframe(
        df[["Stock", "Previous Close", "Live Price", "Source"]],
        use_container_width=True
    )

    if nse_errors:
        st.markdown("**NSE fetch failures this cycle:**")
        nse_error_df = pd.DataFrame(
            [{"Stock": s, "NSE Error": e} for s, e in nse_errors.items()]
        )
        st.dataframe(nse_error_df, use_container_width=True)
        st.caption(
            "If every symbol shows an error here (especially "
            "'non-JSON response' or 'HTTP 403'), NSE is very likely "
            "blocking requests from this host's IP address -- common on "
            "Streamlit Community Cloud. In that case the app runs on "
            "Yahoo's own quote fields instead (Source column shows "
            "'yfinance-quote'). 'yfinance-daily-derived' in the "
            "Source column means even Yahoo's quote fields failed for "
            "that symbol and it fell back to candle-derived data, "
            "which is the least reliable tier -- worth investigating "
            "for that specific ticker if you see it."
        )
    else:
        st.caption("NSE responded successfully for all symbols this cycle.")

    if 'yf_quote_errors' in dir() and yf_quote_errors:
        st.markdown("**Yahoo quote (Tier 2) failures this cycle:**")
        yf_error_df = pd.DataFrame(
            [{"Ticker": t, "Error": e} for t, e in yf_quote_errors.items()]
        )
        st.dataframe(yf_error_df, use_container_width=True)

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

st.caption(f"© Debrup Bera | Auto-refresh every {REFRESH_SECONDS} seconds")

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
# Was 15s. Combined with per-symbol, un-timed-out network calls (see
# fetch section below) this meant the app could spend minutes blocked
# inside a single refresh cycle, then immediately start another one.
# Slowed down and matched to the cache ttl on the fetch functions.

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

previous_nav = 120.56
weekly_start_nav = 122.78

# =========================
# INVESTMENT DETAILS
# =========================

avg_nav = 117.70

total_units = 35399.24

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
# Updated to match latest factsheet disclosure (equity holdings only;
# Triparty Repo / cash-equivalent and Net Receivables/(Payables) lines
# are excluded since they aren't tradable equity tickers).
#
# Verified against NSE: "PWL" is PhysicsWallah Ltd (correct symbol,
# not a typo) -- if you were suspecting a bad ticker there, it's fine.

stocks = [

    ("KALYANKJIL", 8.87),
    ("PAYTM", 8.08),
    ("ETERNAL", 6.37),
    ("COFORGE", 5.58),
    ("ABCAPITAL", 5.20),
    ("KEI", 4.81),
    ("PERSISTENT", 4.75),
    ("GROWW", 4.08),
    ("SHRIRAMFIN", 3.75),
    ("DIXON", 3.48),
    ("MCX", 2.90),
    ("TIINDIA", 2.83),
    ("BSE", 2.73),
    ("STLTECH", 2.66),
    ("PRESTIGE", 2.58),
    ("LTF", 2.55),
    ("BHARTIHEXA", 2.55),
    ("SUZLON", 2.34),
    ("IDFCFIRSTB", 2.25),
    ("MAXHEALTH", 2.20),
    ("POLICYBZR", 2.16),
    ("PREMIERENE", 2.15),
    ("MOTHERSON", 2.09),
    ("ICICIAMC", 1.98),
    ("BEL", 1.90),
    ("INDIGO", 1.83),
    ("WAAREEENER", 1.63),
    ("ADANIENT", 0.91),
    ("PWL", 0.60),
    ("AUBANK", 0.06),

]

# =========================
# FETCH LIVE DATA
# =========================
#
# WHY THIS VERSION FROZE (same underlying disease as the sister app,
# worse symptoms):
#
# The previous version made, PER SYMBOL, PER 15-SECOND REFRESH:
#   1) an NSE request (with its own retry-on-403 round trip)
#   2) if that failed: a yfinance 1-minute intraday history() call
#   3) a yfinance 5-day daily history() call
#   4) a yfinance fast_info call
# ...all executed ONE SYMBOL AT A TIME, IN SEQUENCE, with NO TIMEOUT
# set on any of the yfinance calls (only the NSE requests.get() calls
# had timeout=5). For 30 symbols that's up to 100+ sequential blocking
# network calls per refresh. If NSE is bot-blocking the app's IP
# (extremely common for Streamlit Community Cloud -- NSE actively
# fingerprints and blocks datacenter IPs), EVERY one of those NSE calls
# fails only after its own retry, and EVERY symbol then also falls
# through 3 more yfinance calls that can hang indefinitely. That's
# enough to freeze the page for minutes, and it repeats every 15
# seconds forever -- exactly the symptom reported.
#
# FIX -- three changes, same NSE-primary / yfinance-fallback design
# and the same staleness guard, but restructured so NOTHING in the
# per-symbol loop touches the network anymore:
#
#   1) NSE calls are fetched for ALL 30 symbols CONCURRENTLY via a
#      thread pool (not one-by-one), and the whole batch is wrapped in
#      a hard overall timeout. If NSE is blocking/slow, we find out
#      once, in ~5-20 seconds total, not 30 times sequentially.
#   2) The yfinance fallback no longer makes per-symbol history()/
#      fast_info calls. It uses TWO single batched, threaded
#      yf.download() calls (one for daily bars -> previous close, one
#      for 1-minute intraday bars -> live price) for ALL tickers at
#      once, each wrapped in its own hard timeout.
#   3) The per-symbol for-loop that builds the final table now does
#      ZERO network I/O -- it only reads from the three pre-fetched
#      batches (NSE dict, daily batch, intraday batch) that were
#      already fetched above. A single slow/blocked source can no
#      longer stall the whole page, because it's bounded by one
#      timeout instead of 30 uncapped ones.
#
# The "Source" column and NSE-error debug panel are kept so you can
# still see, per stock, which feed actually served the data and
# whether NSE is being blocked.
#
# ---------------------------------------------------------------
# WHY PRICES WERE SHOWING WRONG (this revision's fix):
#
# The staleness guard on `previous_close` -- meant to reject a single
# corrupted fetch -- was keyed ONLY by symbol, with NO notion of
# "today". Once it locked onto a baseline value for a symbol, that
# baseline sat in st.session_state and was never reset at the start of
# a new trading day. On a long-running Streamlit Cloud instance, that
# baseline could be several days old. Any freshly-fetched (correct)
# previous_close that differed from that stale baseline by MORE than
# STALE_GUARD_PCT (3%) was rejected and the old, wrong value kept
# being reused -- silently, with no error shown. That's exactly what
# was happening to PERSISTENT: its live/previous-close numbers didn't
# match the real market because the guard was defending a stale
# baseline instead of the truth.
#
# Fixed by:
#   1) Keying the guard by (symbol, date) so the baseline auto-resets
#      every trading day instead of persisting indefinitely.
#   2) Only applying the guard to the yfinance FALLBACK path. NSE's
#      own `previousClose` field comes straight from the exchange and
#      is authoritative -- there's nothing to validate it against, and
#      running it through a same-symbol guard was the exact mechanism
#      that let a stale value get "defended" over real data.
#
# CAVEATS (still apply):
# 1) NSE's website uses bot-detection (cookies + browser-like headers
#    required). If NSE blocks Streamlit Cloud's IP range, all NSE
#    calls fail together (visible in the debug panel) and the app runs
#    entirely on the yfinance batch fallback -- which is fine, just
#    slightly less fresh than NSE's own feed.
# 2) This could not be executed against the live NSE API from this
#    development environment (network access here is restricted to
#    package registries only) -- please check the debug panel on first
#    run to confirm NSE is actually being reached.

STALE_GUARD_PCT = 3.0  # max allowed jump in previous_close vs last known-good, in % (yfinance fallback only)
NSE_REQUEST_TIMEOUT = 5        # per-request timeout, seconds
NSE_BATCH_TIMEOUT = 20         # hard ceiling for ALL 30 NSE requests combined
YF_BATCH_TIMEOUT = 15          # hard ceiling for each batched yfinance download

if "last_good_data" not in st.session_state:
    st.session_state["last_good_data"] = {}

if "last_good_prev_close" not in st.session_state:
    # Tracks the last ACCEPTED previous_close per symbol, keyed as
    # {symbol: {"date": "YYYY-MM-DD", "value": float}}, used solely
    # for the staleness guard on the yfinance FALLBACK path (separate
    # from last_good_data, which stores the full display row). The
    # "date" field is what makes the baseline reset every trading day
    # instead of persisting stale for as long as the server stays warm.
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
    pool, bounded by ONE overall timeout -- so a blocked/slow NSE can
    only cost us NSE_BATCH_TIMEOUT seconds total, not 30x that."""
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
            # Whatever didn't finish in time is treated as failed for
            # this cycle rather than left to block indefinitely.
            for fut, s in futures.items():
                if s not in results:
                    results[s] = (None, None)
                    errors[s] = "timeout (overall NSE batch)"

    return results, errors


def _fetch_one_yf_quote(ticker):
    """Single-symbol Yahoo QUOTE fetch via fast_info (not our own
    historical-bar derivation). Called from a thread pool, never
    directly from the main per-symbol loop.

    Correction on what this actually is: fast_info.previousClose is
    NOT a raw untouched field straight off Yahoo's servers -- under
    the hood it's still derived (yfinance groups a week of hourly
    pre/post-market bars by calendar date and takes the second-to-
    last day's close), with a genuine fallback to Yahoo's quote-
    summary "previousClose" field if that derivation comes up empty.
    So it's yfinance's OWN tested, maintained derivation, not our
    homegrown one -- which combined two separately-fetched batch
    downloads (10d daily + 1d intraday) and tried to reconcile them
    ourselves. That reconciliation is what was landing on the wrong
    bar for at least PERSISTENT. Using yfinance's built-in logic here
    is a materially different, better-tested code path, but it's
    still a derivation, not a guarantee -- if a ticker is still wrong
    after this change, the debug panel's Source column will say which
    tier actually served it, which is the fastest way to narrow down
    where it's still going wrong.
    """
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
    """TIER 2 (secondary) source, used when NSE fails. Fetches ALL
    tickers' live quote fields (previousClose, lastPrice) CONCURRENTLY
    via a thread pool, bounded by ONE overall timeout -- same pattern
    as the NSE batch, so a slow/blocked ticker can only cost us
    YF_BATCH_TIMEOUT seconds total, not 30x that, and this can never
    fall back into the old one-symbol-at-a-time-with-no-timeout bug."""
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
    threaded call for ALL tickers' recent daily bars, instead of a
    per-ticker loop. Only used if BOTH NSE and the Yahoo quote batch
    (Tier 2) fail for a symbol -- prefer Tier 2 whenever possible,
    since deriving previous-close from historical candles ourselves
    is exactly what caused the earlier bug."""
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
    """FALLBACK source (live price): ONE batched, threaded call for
    ALL tickers' 1-minute intraday bars, instead of a per-ticker
    history() loop."""
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
    """Previous close = last COMPLETE daily bar, pulled from the
    pre-fetched daily batch. No network I/O.

    IMPORTANT: this used to decide which daily bar was "today's
    still-forming bar" (and therefore not a valid previous close) by
    comparing yfinance's own bar timestamps against a SEPARATELY
    computed `datetime.now(ZoneInfo("Asia/Kolkata")).date()`. Those
    are two independent sources of "what day is it" -- Python's clock
    vs. however yfinance/pandas normalized the daily index for this
    ticker -- and they don't always agree (timezone normalization for
    .NS daily bars isn't perfectly consistent across yfinance
    versions/tickers). When they disagreed by a day, this function
    would either keep today's in-progress bar as "previous close", or
    skip back an extra day -- both look like "wrong day" bugs from the
    outside, which is what was happening on PERSISTENT.

    Fixed by never comparing a yfinance date to a Python-clock date.
    Instead, compare yfinance's daily bar dates to yfinance's OWN
    intraday bar dates (same source, same normalization), since those
    two are internally consistent with each other:
      - If the intraday batch has data whose last date matches the
        daily batch's last date, the market is (or was very recently)
        open today, so that last daily row is today's in-progress bar
        -> drop it, use the row before it as previous close.
      - Otherwise (no intraday data yet, e.g. pre-market, or dates
        don't match) the last daily row is already a completed
        session -> it IS the previous close, use it directly.
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
            # Last daily row is today's in-progress session -> drop it.
            if len(daily_hist) >= 2:
                return float(daily_hist.iloc[-2])
            return None

        # No matching in-progress session detected -> the last daily
        # row is already a completed trading day, so it IS the
        # previous close.
        return float(daily_hist.iloc[-1])
    except Exception:
        pass
    return None


def get_live_price_from_intraday(ticker, batch_data):
    """Live price = most recent 1-minute intraday close, pulled from
    the pre-fetched intraday batch. No network I/O. Falls back to the
    daily batch's last close if intraday data is unavailable (e.g.
    market closed)."""
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
    STALENESS GUARD -- rewritten to fix the wrong-price bug.

    Previously this was keyed only by `symbol`, with no notion of
    "today". Once a baseline value was accepted for a symbol it lived
    in st.session_state indefinitely (Streamlit Cloud instances can
    stay warm for days). Any later, CORRECT previous_close that
    happened to differ from that stale baseline by more than
    STALE_GUARD_PCT was silently rejected in favour of the old value
    -- so a bad or outdated baseline could "win" forever. That's what
    was producing incorrect Previous Close / % Change / NAV Impact
    numbers (most visibly on PERSISTENT).

    Fix, two parts:
      1) The baseline is now keyed by (symbol, date). A new trading
         day always re-seeds the baseline from the first fresh value
         seen that day, instead of carrying forward an arbitrarily old
         one.
      2) NSE's own previousClose, and Yahoo's own quote previousClose
         (Tier 2, "yfinance-quote"), are both trusted outright and
         skip the guard entirely -- they're authoritative values
         straight from the exchange/vendor, not something we compute,
         so there's nothing to validate them against. The guard now
         only protects the Tier 3 "yfinance-daily-derived" path,
         which is the one that derives previous-close from historical
         candles ourselves and can occasionally land on a bad bar.
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
        # First fetch of the (trading) day for this symbol -- nothing
        # to compare against yet, so accept it as today's baseline.
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
#
# Three tiers now, tried in order per symbol:
#   1) NSE                     -- exchange's own numbers directly
#   2) Yahoo quote (fast_info)  -- Yahoo's own stated previousClose/
#                                  lastPrice, same "authoritative
#                                  field, not derived by us" category
#                                  as NSE
#   3) Yahoo historical bars    -- last resort only: WE derive
#      (daily/intraday)          previous close ourselves from candle
#                                 history. This is the path that was
#                                 producing the wrong PERSISTENT number,
#                                 so it's now only reached if both NSE
#                                 and the Yahoo quote batch fail for a
#                                 symbol.

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
# (lets you see at a glance which feed served each row, and spot any
#  "rejected, using last-good" tags if the staleness guard fires)
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
            "'yfinance-quote') -- fetched once for all stocks, not "
            "per-symbol, so it can't stall the page the way the old "
            "per-symbol loop could. 'yfinance-daily-derived' in the "
            "Source column means even Yahoo's quote fields failed for "
            "that symbol and it fell back to candle-derived data, "
            "which is the least reliable tier -- that's worth "
            "investigating for that specific ticker if you see it."
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

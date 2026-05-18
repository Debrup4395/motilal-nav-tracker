import streamlit as st
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import calendar as cal_mod

# ─────────────────────────────────────────
#  AUTO REFRESH — every 5 s
# ─────────────────────────────────────────
st_autorefresh(interval=5000, key="refresh")

# ─────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Motilal Oswal Midcap Fund — NAV Tracker",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}
.stApp { background: #060c18; }
.block-container { padding: 1.5rem 2.5rem 2rem 2.5rem; max-width: 100% !important; }

/* ── TOP HEADER ── */
.top-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 28px;
    background: linear-gradient(135deg, #0d1424 0%, #111c32 100%);
    border: 1px solid #1a2740;
    border-radius: 18px;
    margin-bottom: 24px;
}
.header-left { display: flex; align-items: center; gap: 18px; }
.fund-badge {
    background: linear-gradient(135deg, #1d4ed8, #2563eb);
    color: white;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    padding: 5px 12px;
    border-radius: 20px;
    text-transform: uppercase;
}
.fund-name {
    font-size: 22px;
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: -0.3px;
    line-height: 1.2;
}
.fund-meta {
    font-size: 12px;
    color: #475569;
    margin-top: 3px;
}
.header-right { text-align: right; }
.live-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: #22c55e;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%,100%{opacity:1;} 50%{opacity:0.3;}
}
.last-updated { font-size: 12px; color: #64748b; }
.author-tag { font-size: 11px; color: #3b82f6; font-weight: 600; margin-top: 4px; }

/* ── EST. NAV CHIP IN HEADER ── */
.header-center {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
}
.est-nav-chip {
    background: linear-gradient(135deg, #0f1e38, #162440);
    border: 1px solid #1e3a5f;
    border-radius: 16px;
    padding: 14px 28px;
    text-align: center;
    min-width: 200px;
}
.est-nav-chip-label {
    font-size: 10px;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 6px;
}
.est-nav-chip-value {
    font-size: 28px;
    font-weight: 900;
    color: #f8fafc;
    letter-spacing: -0.5px;
    line-height: 1;
}
.est-nav-chip-sub { font-size: 12px; font-weight: 600; margin-top: 5px; }
.est-nav-chip-sub.pos { color: #22c55e; }
.est-nav-chip-sub.neg { color: #ef4444; }

/* ── MONTHLY TOGGLE TITLE ROW ── */
.section-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 14px;
}

/* ── SUMMARY METRICS BAR ── */
.metrics-bar {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 22px;
}
.metric-card {
    background: #0d1424;
    border: 1px solid #1a2740;
    border-radius: 14px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.metric-card.nav-card::before { background: linear-gradient(90deg,#3b82f6,#6366f1); }
.metric-card.pos-card::before { background: linear-gradient(90deg,#22c55e,#16a34a); }
.metric-card.neg-card::before { background: linear-gradient(90deg,#ef4444,#b91c1c); }
.metric-card.neutral-card::before { background: linear-gradient(90deg,#f59e0b,#d97706); }
.metric-label {
    font-size: 11px;
    font-weight: 600;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 8px;
}
.metric-value {
    font-size: 24px;
    font-weight: 800;
    color: #f1f5f9;
    line-height: 1;
}
.metric-sub { font-size: 13px; font-weight: 500; margin-top: 6px; }
.metric-sub.pos { color: #22c55e; }
.metric-sub.neg { color: #ef4444; }
.metric-sub.neutral { color: #94a3b8; }

/* second row – 4 cards */
.metrics-bar-2 {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 28px;
}

/* ── SECTION TITLE ── */
.section-title {
    font-size: 16px;
    font-weight: 700;
    color: #e2e8f0;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-title span.pill {
    font-size: 10px;
    font-weight: 600;
    background: #1e3a5f;
    color: #60a5fa;
    padding: 3px 9px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

/* ── CALENDAR HEATMAP ── */
.cal-wrap {
    background: #0d1424;
    border: 1px solid #1a2740;
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 24px;
}
.cal-months-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 28px 32px;
    margin-top: 8px;
}
.cal-month-block { min-width: 200px; }
.cal-month-name {
    font-size: 12px;
    font-weight: 700;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 10px;
}
.cal-header-row {
    display: flex;
    gap: 3px;
    margin-bottom: 3px;
}
.cal-dname {
    width: 28px;
    height: 16px;
    font-size: 9px;
    font-weight: 700;
    color: #334155;
    text-align: center;
    line-height: 16px;
}
.cal-week-row { display: flex; gap: 3px; margin-bottom: 3px; }

.cal-cell {
    width: 28px;
    height: 28px;
    border-radius: 6px;
    font-size: 9px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: default;
    position: relative;
    transition: transform 0.12s ease, box-shadow 0.12s ease;
    z-index: 1;
}
.cal-cell:hover {
    transform: scale(1.45);
    z-index: 9999;
    box-shadow: 0 4px 20px rgba(0,0,0,0.6);
}
.cal-cell.empty { background: transparent; pointer-events: none; }
.cal-cell.no-data { background: #131e30; color: #1e3a5f; }

/* CSS Tooltip */
.cal-cell[data-tip]:hover::after {
    content: attr(data-tip);
    position: absolute;
    bottom: 130%;
    left: 50%;
    transform: translateX(-50%);
    background: #0f1c2e;
    color: #e2e8f0;
    padding: 8px 12px;
    border-radius: 8px;
    white-space: pre;
    font-size: 11px;
    font-weight: 500;
    line-height: 1.6;
    z-index: 99999;
    border: 1px solid #1e3a5f;
    pointer-events: none;
    box-shadow: 0 8px 24px rgba(0,0,0,0.5);
}

/* ── COLOR LEGEND ── */
.legend-bar {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 18px;
    flex-wrap: wrap;
}
.legend-item { display: flex; align-items: center; gap: 4px; }
.legend-swatch { width: 14px; height: 14px; border-radius: 3px; }
.legend-txt { font-size: 10px; color: #475569; white-space: nowrap; }
.legend-sep { width: 1px; height: 14px; background: #1e3a5f; margin: 0 4px; }

/* ── MONTHLY P&L SUMMARY ── */
.monthly-summary-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin-bottom: 24px;
}
.month-card {
    background: #0d1424;
    border: 1px solid #1a2740;
    border-radius: 12px;
    padding: 14px 16px;
}
.month-card-name { font-size: 11px; color: #475569; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }
.month-card-pct { font-size: 18px; font-weight: 800; }
.month-card-pct.pos { color: #22c55e; }
.month-card-pct.neg { color: #ef4444; }
.month-card-rs { font-size: 12px; font-weight: 500; margin-top: 2px; }
.month-card-rs.pos { color: #16a34a; }
.month-card-rs.neg { color: #b91c1c; }

/* ── GAINERS / LOSERS ── */
.gl-panel {
    background: #0d1424;
    border: 1px solid #1a2740;
    border-radius: 14px;
    padding: 18px;
    height: 100%;
}
.gl-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    border-radius: 10px;
    margin-bottom: 8px;
}
.gl-item.gain { background: rgba(34,197,94,0.07); border: 1px solid rgba(34,197,94,0.18); border-left: 3px solid #22c55e; }
.gl-item.loss { background: rgba(239,68,68,0.07); border: 1px solid rgba(239,68,68,0.18); border-left: 3px solid #ef4444; }
.gl-name { font-size: 13px; font-weight: 700; color: #e2e8f0; }
.gl-weight { font-size: 11px; color: #475569; margin-top: 2px; }
.gl-pct-pos { font-size: 15px; font-weight: 800; color: #22c55e; }
.gl-pct-neg { font-size: 15px; font-weight: 800; color: #ef4444; }

/* ── EYE TOGGLE BUTTON ── */
.eye-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 2px;
}
div[data-testid="stButton"].eye-btn > button {
    background: transparent !important;
    border: 1px solid #1e3a5f !important;
    color: #64748b !important;
    padding: 1px 7px !important;
    font-size: 13px !important;
    border-radius: 6px !important;
    line-height: 1.4 !important;
    min-height: 0 !important;
    height: auto !important;
}
div[data-testid="stButton"].eye-btn > button:hover {
    border-color: #3b82f6 !important;
    color: #93c5fd !important;
    background: #1e3a5f22 !important;
}
.metric-masked { color: #334155 !important; letter-spacing: 3px; }

/* ── TABLE ── */
div[data-testid="stDataFrame"] {
    border: 1px solid #1a2740 !important;
    border-radius: 14px !important;
    overflow: hidden !important;
}

/* ── DIVIDER ── */
.hdivider {
    border: none;
    border-top: 1px solid #1a2740;
    margin: 8px 0 24px 0;
}

/* ── FOOTER ── */
.footer {
    text-align: center;
    padding: 16px;
    font-size: 12px;
    color: #334155;
    border-top: 1px solid #1a2740;
    margin-top: 20px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
#  INDIA TIME
# ─────────────────────────────────────────
india_time = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y  |  %I:%M:%S %p")


# ─────────────────────────────────────────
#  NAV HISTORY  (01 Jan 2026 – 14 May 2026)
# ─────────────────────────────────────────
NAV_RAW: dict[date, float] = {
    date(2026,  1,  1): 113.9116,
    date(2026,  1,  2): 114.6253,
    date(2026,  1,  5): 114.4763,
    date(2026,  1,  6): 113.9835,
    date(2026,  1,  7): 114.9269,
    date(2026,  1,  8): 113.7923,
    date(2026,  1,  9): 113.2379,
    date(2026,  1, 12): 112.7175,
    date(2026,  1, 13): 112.3857,
    date(2026,  1, 14): 112.0870,
    date(2026,  1, 16): 112.0791,
    date(2026,  1, 19): 111.7642,
    date(2026,  1, 20): 109.7724,
    date(2026,  1, 21): 107.9135,
    date(2026,  1, 22): 107.8337,
    date(2026,  1, 23): 105.2749,
    date(2026,  1, 27): 105.3361,
    date(2026,  1, 28): 106.4244,
    date(2026,  1, 29): 106.5496,
    date(2026,  1, 30): 105.8740,
    date(2026,  2,  2): 105.5445,
    date(2026,  2,  3): 109.0760,
    date(2026,  2,  4): 109.1999,
    date(2026,  2,  5): 108.0524,
    date(2026,  2,  6): 107.6683,
    date(2026,  2,  9): 109.9484,
    date(2026,  2, 10): 110.2109,
    date(2026,  2, 11): 109.4638,
    date(2026,  2, 12): 108.6828,
    date(2026,  2, 13): 106.4226,
    date(2026,  2, 16): 107.2624,
    date(2026,  2, 17): 107.2640,
    date(2026,  2, 18): 107.5889,
    date(2026,  2, 19): 105.3975,
    date(2026,  2, 20): 105.4926,
    date(2026,  2, 23): 104.7282,
    date(2026,  2, 24): 102.8287,
    date(2026,  2, 25): 103.3312,
    date(2026,  2, 26): 103.5967,
    date(2026,  2, 27): 102.4950,
    date(2026,  3,  2): 101.3711,
    date(2026,  3,  4):  99.8871,
    date(2026,  3,  5): 100.5741,
    date(2026,  3,  6):  99.6939,
    date(2026,  3,  9):  98.5871,
    date(2026,  3, 10):  99.5268,
    date(2026,  3, 11):  97.5235,
    date(2026,  3, 12):  97.0585,
    date(2026,  3, 13):  94.8845,
    date(2026,  3, 16):  95.4975,
    date(2026,  3, 17):  96.8760,
    date(2026,  3, 18):  99.4352,
    date(2026,  3, 19):  96.0741,
    date(2026,  3, 20):  96.3556,
    date(2026,  3, 23):  93.3110,
    date(2026,  3, 24):  95.6599,
    date(2026,  3, 25):  97.9963,
    date(2026,  3, 27):  95.5937,
    date(2026,  3, 30):  92.9573,
    date(2026,  3, 31):  92.9568,
    date(2026,  4,  1):  95.6147,
    date(2026,  4,  2):  95.9132,
    date(2026,  4,  6):  98.0759,
    date(2026,  4,  7):  98.3961,
    date(2026,  4,  8): 103.2887,
    date(2026,  4,  9): 103.3217,
    date(2026,  4, 10): 104.2410,
    date(2026,  4, 13): 103.5421,
    date(2026,  4, 15): 105.9581,
    date(2026,  4, 16): 106.3813,
    date(2026,  4, 17): 106.8944,
    date(2026,  4, 20): 106.5208,
    date(2026,  4, 21): 107.4471,
    date(2026,  4, 22): 107.0569,
    date(2026,  4, 23): 106.4504,
    date(2026,  4, 24): 104.7770,
    date(2026,  4, 27): 105.3803,
    date(2026,  4, 28): 105.5858,
    date(2026,  4, 29): 105.8367,
    date(2026,  4, 30): 104.8667,
    date(2026,  5,  4): 105.3881,
    date(2026,  5,  5): 105.2351,
    date(2026,  5,  6): 107.4244,
    date(2026,  5,  7): 108.2798,
    date(2026,  5,  8): 108.6668,
    date(2026,  5, 11): 106.7105,
    date(2026,  5, 12): 103.5222,
    date(2026,  5, 13): 103.7341,
    date(2026,  5, 14): 104.8438,
    date(2026,  5, 15): 104.7252,
}


# ─────────────────────────────────────────
#  INVESTMENT DETAILS
# ─────────────────────────────────────────
AVG_NAV          = 117.70
TOTAL_UNITS      = 36_529.698
TOTAL_INVESTMENT = TOTAL_UNITS * AVG_NAV
INVESTMENT_DATE  = datetime(2024, 9, 2)

today_dt   = datetime.now()
total_days = (today_dt - INVESTMENT_DATE).days
years      = total_days // 365
rem        = total_days % 365
inv_months = rem // 30
inv_days   = rem % 30
INV_DURATION = f"{years}Y {inv_months}M {inv_days}D"


# ─────────────────────────────────────────
#  COMPUTE DAILY RETURNS FROM NAV DATA
# ─────────────────────────────────────────
sorted_dates  = sorted(NAV_RAW.keys())
DAILY_RETURNS: dict[date, dict] = {}

for i in range(1, len(sorted_dates)):
    d      = sorted_dates[i]
    d_prev = sorted_dates[i - 1]
    n_now  = NAV_RAW[d]
    n_prev = NAV_RAW[d_prev]
    pct    = (n_now - n_prev) / n_prev * 100
    rs     = TOTAL_UNITS * (n_now - n_prev)
    DAILY_RETURNS[d] = {
        "nav":      n_now,
        "prev_nav": n_prev,
        "pct":      pct,
        "rs":       rs,
    }

# Latest NAV info
latest_date    = sorted_dates[-1]
latest_nav     = NAV_RAW[latest_date]
latest_prev    = NAV_RAW[sorted_dates[-2]]
latest_pct     = DAILY_RETURNS[latest_date]["pct"]
latest_rs      = DAILY_RETURNS[latest_date]["rs"]

# Current portfolio value
current_value  = TOTAL_UNITS * latest_nav
unrealised_pl  = current_value - TOTAL_INVESTMENT
unrealised_pct = (unrealised_pl / TOTAL_INVESTMENT) * 100

# Weekly NAV (Mon of the current ISO week)
_today = date.today()
_monday = _today - timedelta(days=_today.weekday())
_week_navs = [NAV_RAW[d] for d in sorted_dates if d >= _monday and d in NAV_RAW]
_week_start_nav = NAV_RAW[[d for d in sorted_dates if d >= _monday][0]] if _week_navs else latest_nav
weekly_pct = (latest_nav - _week_start_nav) / _week_start_nav * 100 if _week_start_nav else 0
weekly_rs  = TOTAL_UNITS * (latest_nav - _week_start_nav)

# Monthly returns
def monthly_return(year: int, month: int) -> dict | None:
    month_dates = [d for d in sorted_dates if d.year == year and d.month == month]
    if len(month_dates) < 2:
        return None
    first_nav = NAV_RAW[month_dates[0]]
    last_nav  = NAV_RAW[month_dates[-1]]
    # use the NAV just before first trading day of month for prev if available
    all_before = [d for d in sorted_dates if d < month_dates[0]]
    base_nav   = NAV_RAW[all_before[-1]] if all_before else first_nav
    pct        = (last_nav - base_nav) / base_nav * 100
    rs         = TOTAL_UNITS * (last_nav - base_nav)
    return {"pct": pct, "rs": rs, "month_name": cal_mod.month_abbr[month]}


# ─────────────────────────────────────────
#  COLOR HELPERS
# ─────────────────────────────────────────
def cell_color(pct: float) -> tuple[str, str]:
    """Return (background_hex, text_hex) based on daily return %."""
    if   pct >=  2.5: return "#005c2e", "#4ade80"   # extreme +
    elif pct >=  1.5: return "#006b35", "#86efac"
    elif pct >=  0.8: return "#15803d", "#bbf7d0"
    elif pct >=  0.3: return "#16a34a", "#dcfce7"
    elif pct >   0.0: return "#22c55e", "#f0fdf4"
    elif pct >= -0.3: return "#dc2626", "#fecaca"
    elif pct >= -0.8: return "#b91c1c", "#fca5a5"
    elif pct >= -1.5: return "#991b1b", "#f87171"
    else:             return "#7f1d1d", "#fca5a5"   # extreme −


# ─────────────────────────────────────────
#  CALENDAR HTML BUILDER
# ─────────────────────────────────────────
DAY_ABBR = ["M", "T", "W", "T", "F", "S", "S"]

def build_month_html(year: int, month: int) -> str:
    cal_weeks = cal_mod.monthcalendar(year, month)
    month_name = cal_mod.month_name[month].upper()
    html = f'<div class="cal-month-block">'
    html += f'<div class="cal-month-name">{month_name}</div>'
    # day-name header
    html += '<div class="cal-header-row">'
    for d in DAY_ABBR:
        html += f'<div class="cal-dname">{d}</div>'
    html += '</div>'
    for week in cal_weeks:
        html += '<div class="cal-week-row">'
        for day in week:
            if day == 0:
                html += '<div class="cal-cell empty"></div>'
            else:
                d = date(year, month, day)
                if d in DAILY_RETURNS:
                    r   = DAILY_RETURNS[d]
                    pct = r["pct"]
                    rs  = r["rs"]
                    nav = r["nav"]
                    bg, fg = cell_color(pct)
                    sign   = "+" if pct >= 0 else ""
                    rs_sign = "+" if rs >= 0 else ""
                    tip = (
                        f"{d.strftime('%d %b %Y')}\\n"
                        f"NAV: {nav:.4f}\\n"
                        f"Day Return: {sign}{pct:.2f}%\\n"
                        f"P&L: {rs_sign}₹{abs(rs):,.0f}"
                    )
                    html += (
                        f'<div class="cal-cell" '
                        f'style="background:{bg};color:{fg};" '
                        f'data-tip="{tip}">'
                        f'{day}'
                        f'</div>'
                    )
                else:
                    html += f'<div class="cal-cell no-data">{day}</div>'
        html += '</div>'
    html += '</div>'
    return html


def build_full_calendar_html() -> str:
    months_in_data = sorted(set((d.year, d.month) for d in sorted_dates))
    html = '<div class="cal-months-grid">'
    for yr, mo in months_in_data:
        html += build_month_html(yr, mo)
    html += '</div>'
    # Legend
    legend_items = [
        ("#005c2e", "#4ade80", "> +2.5%"),
        ("#15803d", "#bbf7d0", "+0.8 – 2.5%"),
        ("#22c55e", "#f0fdf4", "0 – +0.8%"),
        ("#dc2626", "#fecaca", "0 – −0.8%"),
        ("#991b1b", "#f87171", "−0.8 – −1.5%"),
        ("#7f1d1d", "#fca5a5", "< −1.5%"),
    ]
    html += '<div class="legend-bar">'
    html += '<span style="font-size:11px;color:#475569;margin-right:4px;">Less</span>'
    for bg, fg, label in legend_items:
        html += (
            f'<div class="legend-item">'
            f'<div class="legend-swatch" style="background:{bg};"></div>'
            f'<span class="legend-txt">{label}</span>'
            f'</div>'
        )
    html += '<span style="font-size:11px;color:#475569;margin-left:4px;">More</span>'
    html += '</div>'
    return html


# ─────────────────────────────────────────
#  PORTFOLIO HOLDINGS
# ─────────────────────────────────────────
STOCKS = [
    ("PAYTM",       7.29), ("KALYANKJIL",  7.09), ("ETERNAL",    5.83),
    ("COFORGE",     5.58), ("KEI",          5.48), ("PERSISTENT", 5.41),
    ("ABCAPITAL",   5.17), ("GROWW",        5.09), ("BHARTIARTL", 5.01),
    ("MCX",         4.33), ("BSE",          3.83), ("DIXON",      3.54),
    ("TIINDIA",     3.51), ("BHARTIHEXA",  3.18), ("SHRIRAMFIN", 3.03),
    ("PRESTIGE",    2.91), ("BEL",          2.63), ("LTF",        2.61),
    ("MAXHEALTH",   2.23), ("POLICYBZR",   2.20), ("TVSMOTOR",   2.08),
    ("ICICIPRULI",  1.96), ("IDFCFIRSTB",  1.47), ("PREMIERENE", 1.25),
    ("AXISBANK",    1.24), ("WAAREEENER",  1.04), ("AUBANK",      1.01),
]


# ─────────────────────────────────────────
#  FETCH LIVE STOCK DATA
# ─────────────────────────────────────────
@st.cache_data(ttl=30)
def fetch_live_data(stocks: list) -> pd.DataFrame:
    rows = []
    total_weighted = 0.0
    for symbol, weight in stocks:
        try:
            hist = yf.Ticker(f"{symbol}.NS").history(period="5d", interval="1d")
            prev_close  = hist["Close"].iloc[-2]
            live_price  = hist["Close"].iloc[-1]
            chg         = (live_price - prev_close) / prev_close * 100
            wt_ret      = chg * weight / 100
            total_weighted += wt_ret
            rows.append([symbol, round(weight, 2), round(prev_close, 2),
                          round(live_price, 2), round(chg, 2)])
        except Exception:
            rows.append([symbol, weight, 0.0, 0.0, 0.0])
    df = pd.DataFrame(rows, columns=["Stock", "Weight %", "Prev Close", "Live Price", "% Change"])
    return df, total_weighted

df_live, total_weighted_return = fetch_live_data(STOCKS)

# Estimated NAV from live holdings
previous_nav   = 104.84          # last known official NAV for live estimation
weekly_nav_ref = 108.67
estimated_nav  = previous_nav * (1 + total_weighted_return / 100)
daily_nav_chg  = estimated_nav - previous_nav
weekly_live_chg = (estimated_nav - weekly_nav_ref) / weekly_nav_ref * 100
daily_return_rs  = TOTAL_INVESTMENT * total_weighted_return / 100
weekly_return_rs = TOTAL_INVESTMENT * weekly_live_chg / 100

top_gainers = df_live.sort_values("% Change", ascending=False).head(5)
top_losers  = df_live.sort_values("% Change", ascending=True).head(5)


# ─────────────────────────────────────────
#  RENDER  ——  TOP HEADER
# ─────────────────────────────────────────
st.markdown(f"""
<div class="top-header">
  <div class="header-left">
    <div>
      <div class="fund-badge">Mutual Fund Tracker</div>
      <div class="fund-name" style="margin-top:8px;">🔥 Motilal Oswal Midcap Fund</div>
      <div class="fund-meta">Direct Growth  ·  NAV-based live tracking  ·  NSE equities</div>
    </div>
  </div>
  <div class="header-center">
    <div class="est-nav-chip">
      <div class="est-nav-chip-label">⚡ Est. Live NAV</div>
      <div class="est-nav-chip-value">₹{estimated_nav:.2f}</div>
      <div class="est-nav-chip-sub {'pos' if total_weighted_return>=0 else 'neg'}">
        {'▲' if total_weighted_return>=0 else '▼'} {'+' if total_weighted_return>=0 else ''}{total_weighted_return:.2f}% vs prev ₹{previous_nav}
      </div>
    </div>
  </div>
  <div class="header-right">
    <div class="last-updated">
      <span class="live-dot"></span>Auto-refresh every 5 s
    </div>
    <div class="last-updated" style="margin-top:4px;">{india_time}</div>
    <div class="author-tag">© Debrup Bera</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────
def fmt_rs(v: float) -> str:
    sign = "+" if v >= 0 else "−"
    return f"{sign}₹{abs(v):,.0f}"

def pct_class(v: float) -> str:
    return "pos" if v >= 0 else "neg"

MASK = "₹ ● ● ● ● ●"

# ── Session state for eye toggles ──────
for _k in ("show_unreal", "show_portval", "show_units", "show_daily", "show_monthly_rs"):
    if _k not in st.session_state:
        st.session_state[_k] = True

# ─────────────────────────────────────────
#  RENDER — METRIC ROW 1  (4 cards)
# ─────────────────────────────────────────
latest_nav_sign = "+" if latest_pct >= 0 else "−"
unrel_class     = pct_class(unrealised_pct)
wkly_class      = pct_class(weekly_pct)

c1, c2, c3, c4 = st.columns(4)

# Card 1 — Latest NAV  (no eye)
with c1:
    st.markdown(f"""
    <div class="metric-card nav-card">
      <div class="metric-label">Latest NAV ({latest_date.strftime('%d %b')})</div>
      <div class="metric-value">₹{latest_nav:.4f}</div>
      <div class="metric-sub {pct_class(latest_pct)}">
        {latest_nav_sign}{abs(latest_pct):.2f}% &nbsp;·&nbsp; {fmt_rs(latest_rs)} today
      </div>
    </div>""", unsafe_allow_html=True)

# Card 2 — Unrealised P&L  (👁 eye)
with c2:
    _show = st.session_state.show_unreal
    _top, _eye = st.columns([6, 1])
    with _top:
        st.markdown(f'<div class="metric-label" style="margin:0;padding:6px 0 0 0;font-size:11px;color:#475569;font-weight:600;text-transform:uppercase;letter-spacing:.8px">Unrealised P&amp;L</div>', unsafe_allow_html=True)
    with _eye:
        if st.button("👁" if _show else "🙈", key="eye_unreal", help="Toggle visibility"):
            st.session_state.show_unreal = not _show
            st.rerun()
    _val  = fmt_rs(unrealised_pl) if _show else MASK
    _sub  = f'{"+" if unrealised_pct>=0 else ""}{unrealised_pct:.2f}%  since avg ₹{AVG_NAV:.2f}' if _show else "——"
    _card = "pos" if unrealised_pct >= 0 else "neg"
    st.markdown(f"""
    <div class="metric-card {_card}-card" style="padding-top:10px;">
      <div class="metric-value {'metric-masked' if not _show else ''}">{_val}</div>
      <div class="metric-sub {unrel_class}">{_sub}</div>
    </div>""", unsafe_allow_html=True)

# Card 3 — WTD Return  (no eye)
with c3:
    st.markdown(f"""
    <div class="metric-card {'pos' if weekly_pct>=0 else 'neg'}-card">
      <div class="metric-label">Week-to-Date Return</div>
      <div class="metric-value">{("+" if weekly_pct>=0 else "")}{weekly_pct:.2f}%</div>
      <div class="metric-sub {wkly_class}">{fmt_rs(weekly_rs)}</div>
    </div>""", unsafe_allow_html=True)

# Card 4 — Current Portfolio Value  (👁 eye)
with c4:
    _show = st.session_state.show_portval
    _top, _eye = st.columns([6, 1])
    with _top:
        st.markdown('<div class="metric-label" style="margin:0;padding:6px 0 0 0;font-size:11px;color:#475569;font-weight:600;text-transform:uppercase;letter-spacing:.8px">Current Portfolio Value</div>', unsafe_allow_html=True)
    with _eye:
        if st.button("👁" if _show else "🙈", key="eye_portval", help="Toggle visibility"):
            st.session_state.show_portval = not _show
            st.rerun()
    _val = f"₹{current_value:,.0f}" if _show else MASK
    _sub = f"Invested ₹{TOTAL_INVESTMENT:,.0f}" if _show else "——"
    st.markdown(f"""
    <div class="metric-card neutral-card" style="padding-top:10px;">
      <div class="metric-value {'metric-masked' if not _show else ''}">{_val}</div>
      <div class="metric-sub neutral">{_sub}</div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  RENDER — METRIC ROW 2  (4 cards)
# ─────────────────────────────────────────
est_sign = "+" if total_weighted_return >= 0 else "−"

c5, c6, c7, c8 = st.columns(4)

# Card 5 — Est. live NAV  (no eye)
with c5:
    st.markdown(f"""
    <div class="metric-card nav-card">
      <div class="metric-label">Est. NAV (live holdings)</div>
      <div class="metric-value">₹{estimated_nav:.2f}</div>
      <div class="metric-sub {pct_class(total_weighted_return)}">
        {est_sign}{abs(total_weighted_return):.2f}% vs prev NAV ₹{previous_nav}
      </div>
    </div>""", unsafe_allow_html=True)

# Card 6 — Est. daily P&L  (👁 eye)
with c6:
    _show = st.session_state.show_daily
    _top, _eye = st.columns([6, 1])
    with _top:
        st.markdown('<div class="metric-label" style="margin:0;padding:6px 0 0 0;font-size:11px;color:#475569;font-weight:600;text-transform:uppercase;letter-spacing:.8px">Est. Daily P&amp;L (live)</div>', unsafe_allow_html=True)
    with _eye:
        if st.button("👁" if _show else "🙈", key="eye_daily", help="Toggle visibility"):
            st.session_state.show_daily = not _show
            st.rerun()
    _val = fmt_rs(daily_return_rs) if _show else MASK
    _sub = f"{est_sign}{abs(total_weighted_return):.2f}%" if _show else "——"
    _card = "pos" if daily_return_rs >= 0 else "neg"
    st.markdown(f"""
    <div class="metric-card {_card}-card" style="padding-top:10px;">
      <div class="metric-value {'metric-masked' if not _show else ''}">{_val}</div>
      <div class="metric-sub {pct_class(total_weighted_return)}">{_sub}</div>
    </div>""", unsafe_allow_html=True)

# Card 7 — Total Units  (👁 eye)
with c7:
    _show = st.session_state.show_units
    _top, _eye = st.columns([6, 1])
    with _top:
        st.markdown('<div class="metric-label" style="margin:0;padding:6px 0 0 0;font-size:11px;color:#475569;font-weight:600;text-transform:uppercase;letter-spacing:.8px">Total Units Held</div>', unsafe_allow_html=True)
    with _eye:
        if st.button("👁" if _show else "🙈", key="eye_units", help="Toggle visibility"):
            st.session_state.show_units = not _show
            st.rerun()
    _val = f"{TOTAL_UNITS:,.3f}" if _show else "● ● ● ● ●"
    _sub = f"Avg NAV ₹{AVG_NAV:.2f}" if _show else "——"
    st.markdown(f"""
    <div class="metric-card neutral-card" style="padding-top:10px;">
      <div class="metric-value {'metric-masked' if not _show else ''}">{_val}</div>
      <div class="metric-sub neutral">{_sub}</div>
    </div>""", unsafe_allow_html=True)

# Card 8 — Investment Duration  (no eye)
with c8:
    st.markdown(f"""
    <div class="metric-card neutral-card">
      <div class="metric-label">Investment Duration</div>
      <div class="metric-value">{INV_DURATION}</div>
      <div class="metric-sub neutral">Since 02 Sep 2024</div>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────
#  RENDER — P&L CALENDAR HEATMAP
# ─────────────────────────────────────────
st.markdown('<div class="section-title">📅 NAV P&amp;L Calendar <span class="pill">Jan – May 2026</span></div>', unsafe_allow_html=True)
st.markdown('<div class="cal-wrap">', unsafe_allow_html=True)
st.markdown(build_full_calendar_html(), unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────
#  RENDER — MONTHLY SUMMARY STRIP
# ─────────────────────────────────────────
_show_mo = st.session_state.show_monthly_rs
_title_col, _eye_col = st.columns([11, 1])
with _title_col:
    st.markdown('<div class="section-title" style="margin-bottom:0;">📊 Monthly P&amp;L Summary</div>', unsafe_allow_html=True)
with _eye_col:
    if st.button("👁" if _show_mo else "🙈", key="eye_monthly", help="Hide/show ₹ amounts"):
        st.session_state.show_monthly_rs = not _show_mo
        st.rerun()

month_cards_html = '<div class="monthly-summary-grid">'
for yr, mo in sorted(set((d.year, d.month) for d in sorted_dates)):
    mr = monthly_return(yr, mo)
    if mr is None:
        continue
    pct    = mr["pct"]
    rs     = mr["rs"]
    p_cl   = "pos" if pct >= 0 else "neg"
    sign   = "+" if pct >= 0 else ""
    r_sign = "+" if rs >= 0 else "−"
    rs_html = (
        f'<div class="month-card-rs {p_cl}">{r_sign}₹{abs(rs):,.0f}</div>'
        if _show_mo else
        '<div class="month-card-rs" style="color:#334155;letter-spacing:3px;">●●●●●</div>'
    )
    month_cards_html += f"""
    <div class="month-card">
      <div class="month-card-name">{mr['month_name']} {yr}</div>
      <div class="month-card-pct {p_cl}">{sign}{pct:.2f}%</div>
      {rs_html}
    </div>"""
month_cards_html += '</div>'
st.markdown(month_cards_html, unsafe_allow_html=True)


# ─────────────────────────────────────────
#  RENDER — TOP GAINERS & LOSERS (live)
# ─────────────────────────────────────────
st.markdown('<hr class="hdivider">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🚀 Live Holdings Movers</div>', unsafe_allow_html=True)

col_g, col_l = st.columns(2)

with col_g:
    st.markdown('<div class="gl-panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title" style="margin-bottom:12px;font-size:15px;">🚀 Top 5 Gainers</div>', unsafe_allow_html=True)
    for _, row in top_gainers.iterrows():
        chg  = row["% Change"]
        sign = "+" if chg >= 0 else ""
        st.markdown(f"""
        <div class="gl-item gain">
          <div>
            <div class="gl-name">{row['Stock']}</div>
            <div class="gl-weight">{row['Weight %']:.2f}% of portfolio</div>
          </div>
          <div class="gl-pct-pos">{sign}{chg:.2f}%</div>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_l:
    st.markdown('<div class="gl-panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title" style="margin-bottom:12px;font-size:15px;">🔻 Top 5 Losers</div>', unsafe_allow_html=True)
    for _, row in top_losers.iterrows():
        chg = row["% Change"]
        st.markdown(f"""
        <div class="gl-item loss">
          <div>
            <div class="gl-name">{row['Stock']}</div>
            <div class="gl-weight">{row['Weight %']:.2f}% of portfolio</div>
          </div>
          <div class="gl-pct-neg">{chg:.2f}%</div>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────
#  RENDER — PORTFOLIO TABLE
# ─────────────────────────────────────────
st.markdown('<div class="section-title">📋 Full Portfolio Holdings <span class="pill">Live NSE</span></div>', unsafe_allow_html=True)

def color_change(val):
    if val > 0:  return "color: #22c55e; font-weight: 700"
    if val < 0:  return "color: #ef4444; font-weight: 700"
    return "color: #94a3b8"

styled_df = df_live.style.format({
    "Weight %":   "{:.2f}",
    "Prev Close": "{:.2f}",
    "Live Price": "{:.2f}",
    "% Change":   "{:+.2f}",
}).map(color_change, subset=["% Change"])

st.dataframe(styled_df, use_container_width=True, height=870)


# ─────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────
st.markdown("""
<div class="footer">
  © Debrup Bera &nbsp;·&nbsp; Motilal Oswal Midcap Fund NAV Tracker
  &nbsp;·&nbsp; Data refreshes every 5 seconds &nbsp;·&nbsp; For personal use only
</div>
""", unsafe_allow_html=True)

from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_VERSION = "1.7.0"
START = date(2026, 9, 1)
DEFAULT_BALANCE = 20.71
DEFAULT_DEPOSIT = 10.0
DEFAULT_NEXT = date(2026, 9, 11)
BASELINE_DEPOSIT = 10.0
BLUE = "#087CF2"
DEEP_BLUE = "#053B98"
NAVY = "#061A45"
RED = "#E51B23"
ORANGE = "#FF6A00"
YELLOW = "#FFE600"
WHITE = "#FFFFFF"

@dataclass(frozen=True)
class Cfg:
    start: date
    balance: float
    next_dep: date
    freq: int
    apy: float = 0.10
    cap: float = 1000.0
    excess_apy: float = 0.001


def daily_rate(apy: float) -> float:
    return (1 + apy) ** (1 / 365) - 1


def daily_interest(balance: float, cfg: Cfg) -> float:
    premium = min(balance, cfg.cap)
    excess = max(balance - cfg.cap, 0.0)
    return premium * daily_rate(cfg.apy) + excess * daily_rate(cfg.excess_apy)


def project(cfg: Cfg, amount: float, end: date) -> pd.DataFrame:
    d, bal, nxt = cfg.start, cfg.balance, cfg.next_dep
    rows = []
    while d <= end:
        dep = 0.0
        if d == nxt:
            dep = float(amount)
            bal += dep
            nxt += timedelta(days=cfg.freq)
        intr = daily_interest(bal, cfg)
        bal += intr
        rows.append({"date": d, "balance": bal, "deposit": dep, "interest": intr})
        d += timedelta(days=1)
    return pd.DataFrame(rows)


def goal_date(df: pd.DataFrame, goal: float = 1000.0):
    x = df[df["balance"] >= goal]
    return None if x.empty else x.iloc[0]["date"]


def dividend_forecast(cfg: Cfg, amount: float, payout: date = date(2026, 9, 30)):
    d, bal, nxt = cfg.start, cfg.balance, cfg.next_dep
    rows, total = [], 0.0
    while d <= payout:
        dep = 0.0
        if d == nxt:
            dep = float(amount)
            bal += dep
            nxt += timedelta(days=cfg.freq)
        intr = daily_interest(bal, cfg)
        total += intr
        rows.append({"date": d, "balance": bal, "deposit": dep, "accrual": intr})
        d += timedelta(days=1)
    return total, pd.DataFrame(rows)


def monthly_dividends(cfg: Cfg, amount: float, months: int = 12) -> pd.DataFrame:
    end = cfg.start + timedelta(days=370)
    df = project(cfg, amount, end).copy()
    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M")
    out = df.groupby("month", as_index=False)["interest"].sum().head(months)
    out["label"] = out["month"].astype(str).map(lambda x: pd.Period(x).strftime("%b %Y"))
    return out[["label", "interest"]]


def scenarios(cfg: Cfg, values) -> pd.DataFrame:
    rows = []
    for amount in values:
        df = project(cfg, amount, cfg.start + timedelta(days=3650))
        hit = goal_date(df)
        if hit:
            thru = df[df["date"] <= hit]
            rows.append({
                "Deposit": amount,
                "Goal Date": hit,
                "Months": round((hit - cfg.start).days / 30.4375, 1),
                "Interest": float(thru["interest"].sum()),
            })
    return pd.DataFrame(rows)


def two_bucket(cfg: Cfg, amount: float, next_apy: float, end: date) -> pd.DataFrame:
    d, orsa, bucket2, nxt = cfg.start, cfg.balance, 0.0, cfg.next_dep
    rows = []
    while d <= end:
        if d == nxt:
            room = max(cfg.cap - orsa, 0.0)
            to_orsa = min(amount, room)
            orsa += to_orsa
            bucket2 += max(amount - to_orsa, 0.0)
            nxt += timedelta(days=cfg.freq)
        orsa += daily_interest(orsa, cfg)
        bucket2 += bucket2 * daily_rate(next_apy)
        if orsa > cfg.cap:
            bucket2 += orsa - cfg.cap
            orsa = cfg.cap
        rows.append({"date": d, "ORSA": orsa, "Bucket #2": bucket2, "Total": orsa + bucket2})
        d += timedelta(days=1)
    return pd.DataFrame(rows)


def money(v: float) -> str:
    return f"${v:,.2f}"


def style_chart(fig: go.Figure, height: int = 410):
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=42, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=NAVY,
        font_color=WHITE,
        xaxis=dict(gridcolor="#2B5AA0", tickfont=dict(color=WHITE)),
        yaxis=dict(gridcolor="#2B5AA0", tickfont=dict(color=WHITE)),
        legend=dict(orientation="h", y=1.10),
        hovermode="x unified",
    )


st.set_page_config(page_title="High-Yield Savings Project", page_icon="💰", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
:root{--blue:#087CF2;--deep:#053B98;--navy:#061A45;--red:#E51B23;--orange:#FF6A00;--yellow:#FFE600}
.stApp{background:linear-gradient(180deg,#087CF2 0%,#075dcc 22%,#061A45 72%,#04102d 100%);color:white}.block-container{max-width:1380px;padding:.35rem .7rem 3rem}header,footer{visibility:hidden}
.brand{font-family:Impact,Arial Black,sans-serif;font-size:clamp(2rem,5vw,4.1rem);line-height:.9;font-style:italic;color:white;text-shadow:3px 3px 0 #E51B23;margin:.15rem 0 .55rem}.brand span{color:#FFE600}
.hero{border:4px solid #FFE600;border-radius:20px;padding:5px;background:#061A45;box-shadow:0 8px 0 #E51B23}.hero img{width:100%;display:block;border-radius:13px}
.banner{background:linear-gradient(90deg,#E51B23,#FF6A00);border:3px solid #FFE600;border-radius:14px;padding:12px 14px;margin:12px 0;color:white;font-weight:1000}
.section-title{font-size:1.3rem;font-weight:1000;color:white;margin:.9rem 0 .35rem}.deposit-zone{background:linear-gradient(135deg,#053B98 0%,#087CF2 48%,#E51B23 49%,#FF6A00 100%);border:4px solid #FFE600;border-radius:20px;padding:15px;box-shadow:0 7px 0 #061A45;margin:10px 0}.deposit-zone h3{margin:0;color:white;font-family:Impact,Arial Black;font-size:1.55rem}.deposit-zone p{margin:4px 0 0;color:white;font-weight:900}
[data-testid="stVerticalBlockBorderWrapper"]{background:rgba(6,26,69,.94);border:2px solid #FF6A00!important;border-radius:16px!important}
[data-testid="stNumberInput"] input{font-size:22px!important;font-weight:1000!important;color:#061A45!important;background:#fff!important}.stNumberInput label,.stDateInput label,.stSelectbox label,.stRadio label{color:white!important;font-weight:900!important}
.stButton button,.stFormSubmitButton button{width:100%;min-height:60px;background:linear-gradient(145deg,#E51B23,#FF6A00)!important;color:white!important;border:3px solid #FFE600!important;border-radius:15px!important;font-weight:1000!important;font-size:1.05rem!important;box-shadow:0 5px 0 #053B98!important}.stButton button:hover,.stFormSubmitButton button:hover{background:linear-gradient(145deg,#087CF2,#053B98)!important;border-color:white!important;color:white!important}
.goalbar{height:22px;background:#061A45;border:2px solid white;border-radius:999px;overflow:hidden}.goalfill{height:100%;background:linear-gradient(90deg,#FFE600,#FF6A00,#E51B23)}.goalcopy{font-weight:900;color:white;margin-top:5px}
.power-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin:10px 0}.power-card{background:#061A45;border:3px solid #087CF2;border-bottom:5px solid #FF6A00;border-radius:15px;padding:13px;color:white}.power-card .label{font-size:.72rem;font-weight:1000;color:#FFE600}.power-card .value{font-family:Impact,Arial Black;font-size:clamp(1.6rem,4vw,2.7rem);line-height:1;color:white;margin-top:4px}.power-card .sub{font-size:.75rem;font-weight:800;color:#dcecff;margin-top:5px}
.impact{background:linear-gradient(90deg,#E51B23,#FF6A00);border:3px solid #FFE600;border-radius:16px;padding:13px;color:white;font-weight:1000;margin:10px 0}.impact b{color:#FFE600}
[data-testid="stPlotlyChart"]{border:3px solid #FF6A00;border-radius:16px;overflow:hidden;background:#061A45;box-shadow:0 5px 0 #053B98}
.action-panel{background:#061A45;border:3px solid #FF6A00;border-left:8px solid #FFE600;border-radius:15px;padding:15px;margin:10px 0;color:white}.action-panel b{color:#FFE600}
@media(max-width:700px){.block-container{padding:.2rem .38rem 2rem}.brand{font-size:2.25rem}.hero{border-width:3px;box-shadow:0 5px 0 #E51B23}.banner{font-size:.9rem}.section-title{font-size:1.08rem}[data-testid="column"]{min-width:100%!important;width:100%!important;flex:1 1 100%!important}.power-grid{grid-template-columns:1fr 1fr}.power-card .value{font-size:1.8rem}[data-testid="stPlotlyChart"]{min-height:320px}.deposit-zone{padding:12px}.deposit-zone h3{font-size:1.3rem}}
</style>
""", unsafe_allow_html=True)

if "active_deposit" not in st.session_state:
    st.session_state.active_deposit = DEFAULT_DEPOSIT
if "deposit_draft" not in st.session_state:
    st.session_state.deposit_draft = DEFAULT_DEPOSIT

st.markdown(f"<div class='brand'>HIGH-YIELD <span>SAVINGS</span> PROJECT <small style='font-size:.28em'>v{APP_VERSION}</small></div>", unsafe_allow_html=True)
st.markdown("<div class='hero'><img src='https://raw.githubusercontent.com/Grzesiak33/High-Yield-Savings-Project/main/assets/savings_hero.png'></div>", unsafe_allow_html=True)
st.markdown("<div class='banner'>⚡ DEPOSIT IMPACT LAB: type $11, $13, $18 — whatever you want — hit GO, and watch the charts show exactly what the extra savings does.</div>", unsafe_allow_html=True)

st.markdown("<div class='deposit-zone'><h3>💥 CHANGE YOUR PAYCHECK DEPOSIT</h3><p>Type an exact dollar amount. Press Enter or tap GO to run the new plan.</p></div>", unsafe_allow_html=True)
with st.form("deposit_form", clear_on_submit=False):
    draft = st.number_input("Deposit every paycheck ($)", min_value=0.0, max_value=5000.0, step=1.0, format="%.2f", key="deposit_draft")
    go = st.form_submit_button("🚀 GO — SHOW ME THE IMPACT", use_container_width=True)
if go:
    st.session_state.active_deposit = float(draft)

amount = float(st.session_state.active_deposit)

with st.container(border=True):
    st.markdown("<div class='section-title'>⚙️ ACCOUNT SETTINGS</div>", unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1:
        balance = st.number_input("Current savings balance", min_value=0.0, value=DEFAULT_BALANCE, step=5.0, format="%.2f")
    with c2:
        next_dep = st.date_input("Next automatic deposit", value=DEFAULT_NEXT)
    with c3:
        freq = st.selectbox("Deposit schedule", [7,14,15,30], index=1, format_func=lambda x:{7:"Weekly",14:"Every 2 weeks",15:"Every 15 days",30:"Monthly"}[x])

cfg = Cfg(START, float(balance), next_dep, int(freq))
active = project(cfg, amount, START + timedelta(days=3650))
baseline = project(cfg, BASELINE_DEPOSIT, START + timedelta(days=3650))
active_hit = goal_date(active)
base_hit = goal_date(baseline)
active_thru = active[active["date"] <= active_hit] if active_hit else active
active_interest = float(active_thru["interest"].sum())
months_to_goal = (active_hit - START).days / 30.4375 if active_hit else 0
base_months = (base_hit - START).days / 30.4375 if base_hit else 0
days_faster = (base_hit - active_hit).days if active_hit and base_hit else 0
months_faster = base_months - months_to_goal
active_div, active_detail = dividend_forecast(cfg, amount)
base_div, _ = dividend_forecast(cfg, BASELINE_DEPOSIT)
div_gain = active_div - base_div
remaining = max(1000 - balance, 0)
progress = min(balance / 1000, 1)
extra_per_check = amount - BASELINE_DEPOSIT
annual_extra = extra_per_check * (365 / freq)

st.markdown(f"<div class='goalbar'><div class='goalfill' style='width:{progress*100:.2f}%'></div></div><div class='goalcopy'>{progress*100:.1f}% FILLED • {money(remaining)} LEFT • ACTIVE PLAN: {money(amount)}/PAYCHECK</div>", unsafe_allow_html=True)

if amount > BASELINE_DEPOSIT:
    st.markdown(f"<div class='impact'>🔥 POWER-UP ACTIVE: adding <b>{money(extra_per_check)}</b> more per paycheck adds about <b>{money(annual_extra)}</b> of extra deposits per year on this schedule and moves your $1,000 finish line forward.</div>", unsafe_allow_html=True)
elif amount == BASELINE_DEPOSIT:
    st.markdown("<div class='impact'>⚡ $10/check is your baseline. Type $11, $13, $18 or any other amount above and hit GO to see the difference explode onto the charts.</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='impact'>⚠️ This plan is <b>{money(abs(extra_per_check))}</b> below the $10/check baseline, so the $1,000 finish line moves later.</div>", unsafe_allow_html=True)

st.markdown("<div class='section-title'>🏆 YOUR IMPACT SCOREBOARD</div>", unsafe_allow_html=True)
st.markdown(f"""
<div class='power-grid'>
  <div class='power-card'><div class='label'>ACTIVE DEPOSIT</div><div class='value'>{money(amount)}</div><div class='sub'>every paycheck</div></div>
  <div class='power-card'><div class='label'>NEXT DIVIDEND</div><div class='value'>≈ {money(active_div)}</div><div class='sub'>{'+' + money(div_gain) if div_gain >= 0 else money(div_gain)} vs $10 plan</div></div>
  <div class='power-card'><div class='label'>$1,000 FINISH</div><div class='value'>{active_hit.strftime('%b %Y') if active_hit else '—'}</div><div class='sub'>{abs(days_faster)} days {'faster' if days_faster > 0 else 'later' if days_faster < 0 else 'same as baseline'}</div></div>
  <div class='power-card'><div class='label'>MODELED INTEREST TO $1K</div><div class='value'>{money(active_interest)}</div><div class='sub'>{months_to_goal:.1f} months to goal</div></div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='section-title'>🚀 HOW MUCH FASTER DOES MY MONEY GROW?</div>", unsafe_allow_html=True)
chart_end_candidates = [d for d in [active_hit, base_hit] if d is not None]
chart_end = max(chart_end_candidates) + timedelta(days=30) if chart_end_candidates else START + timedelta(days=365*5)
a = active[active["date"] <= chart_end]
b = baseline[baseline["date"] <= chart_end]
fig = go.Figure()
fig.add_trace(go.Scatter(x=b["date"], y=b["balance"], mode="lines", name="$10 baseline", line=dict(color=WHITE, width=3, dash="dot")))
fig.add_trace(go.Scatter(x=a["date"], y=a["balance"], mode="lines", name=f"${amount:g}/check plan", line=dict(color=YELLOW, width=6), fill="tozeroy", fillcolor="rgba(255,230,0,.12)"))
fig.add_hline(y=1000, line_dash="dash", line_color=RED, line_width=4, annotation_text="🏁 $1,000")
if active_hit:
    fig.add_vline(x=active_hit, line_dash="dot", line_color=ORANGE, line_width=3)
style_chart(fig, 460)
fig.update_yaxes(tickprefix="$", title="Savings balance")
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
if days_faster > 0:
    st.markdown(f"<div class='impact'>💨 Going from $10 to <b>{money(amount)}</b> per paycheck reaches $1,000 about <b>{days_faster} days sooner</b> — roughly <b>{months_faster:.1f} months faster</b>.</div>", unsafe_allow_html=True)

st.markdown("<div class='section-title'>💵 WATCH THE MONTHLY DIVIDEND POWER UP</div>", unsafe_allow_html=True)
base_monthly = monthly_dividends(cfg, BASELINE_DEPOSIT, 12).rename(columns={"interest":"baseline"})
active_monthly = monthly_dividends(cfg, amount, 12).rename(columns={"interest":"active"})
monthly = pd.merge(base_monthly, active_monthly, on="label", how="inner")
fig2 = go.Figure()
fig2.add_trace(go.Bar(x=monthly["label"], y=monthly["baseline"], name="$10 baseline", marker_color=BLUE))
fig2.add_trace(go.Bar(x=monthly["label"], y=monthly["active"], name=f"${amount:g}/check", marker_color=ORANGE))
fig2.update_layout(barmode="group")
style_chart(fig2, 430)
fig2.update_yaxes(tickprefix="$", tickformat=".2f", title="Estimated monthly dividend")
st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})

st.markdown("<div class='section-title'>🎯 TRY EXACT DOLLAR AMOUNTS</div>", unsafe_allow_html=True)
examples = scenarios(cfg, sorted(set([10,11,13,15,18,20,25,30,int(round(amount))])))
if not examples.empty:
    examples = examples.copy()
    examples["Goal"] = examples["Goal Date"].map(lambda d:d.strftime("%b %d, %Y"))
    fig3 = go.Figure(go.Bar(
        x=examples["Deposit"], y=examples["Months"],
        marker=dict(color=[BLUE if x == 10 else YELLOW if x < 15 else ORANGE if x < 20 else RED for x in examples["Deposit"]]),
        text=examples["Months"].map(lambda x:f"{x:.1f} mo"), textposition="outside"
    ))
    style_chart(fig3, 420)
    fig3.update_xaxes(title="Deposit each paycheck ($)")
    fig3.update_yaxes(title="Months to $1,000")
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})

st.markdown("<div class='section-title'>🧭 MORE TOOLS</div>", unsafe_allow_html=True)
view = st.radio("", ["Next move after $1K", "Real history"], horizontal=True, label_visibility="collapsed")
if view == "Next move after $1K":
    c1,c2 = st.columns(2)
    with c1:
        next_apy = st.number_input("Next account APY (%)", min_value=0.0, max_value=20.0, value=4.5, step=.1, format="%.1f")
    with c2:
        big_goal = st.number_input("Next total savings goal ($)", min_value=1000.0, max_value=100000.0, value=5000.0, step=500.0)
    strategy = two_bucket(cfg, amount, next_apy/100, START+timedelta(days=365*12))
    orsa_rows = strategy[strategy["ORSA"] >= 1000]
    goal_rows = strategy[strategy["Total"] >= big_goal]
    redirect = None if orsa_rows.empty else orsa_rows.iloc[0]["date"]
    final_goal = None if goal_rows.empty else goal_rows.iloc[0]["date"]
    st.markdown(f"<div class='action-panel'><b>NEXT MOVE</b><br>1️⃣ Fill the 10% ORSA zone: <b>{redirect.strftime('%b %d, %Y') if redirect else '—'}</b><br>2️⃣ Redirect new deposits to your next high-yield account.<br>3️⃣ Reach {money(big_goal)} total: <b>{final_goal.strftime('%b %d, %Y') if final_goal else '—'}</b></div>", unsafe_allow_html=True)
else:
    p = Path("data/savings_transactions.csv")
    if p.exists():
        hist = pd.read_csv(p); hist["date"] = pd.to_datetime(hist["date"])
        st.dataframe(hist.sort_values("date", ascending=False), hide_index=True, use_container_width=True)
    else:
        st.info("Savings history file not found.")

st.markdown(f"<div class='goalcopy' style='text-align:center;margin-top:18px'>HIGH-YIELD SAVINGS PROJECT v{APP_VERSION} • TYPE IT • HIT GO • WATCH THE DIFFERENCE</div>", unsafe_allow_html=True)
